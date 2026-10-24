from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from app.database import engine, get_db, Base
from app import models, schemas, auth
from app.chat import router as chat_router
from app.create_group import router as create_group_router, serialize_group_extras
from app.reviews import router as reviews_router
from ml.matching import rank_groups, set_topic_names

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="StudySync API", version="1.0.0")
@app.on_event("startup")
def startup_event():
    db = next(get_db())
    try:
        topics = db.query(models.Topic).all()
        if topics:
            set_topic_names({t.id: t.name for t in topics})
    finally:
        db.close()

# CORS configuration restricted to Vite dev server and common local ports
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(create_group_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")

# ----------------- AUTH ENDPOINTS -----------------

@app.post("/api/auth/signup", response_model=schemas.TokenResponse)
def signup(payload: schemas.UserSignup, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        name=payload.name,
        email=payload.email,
        hashed_password=auth.hash_password(payload.password),
        major=payload.major or "Computer Science",
        avatar="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&q=80"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth.create_access_token({"sub": user.id})
    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        user_name=user.name,
        user_id=user.id
    )

@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = auth.create_access_token({"sub": user.id})
    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        user_name=user.name,
        user_id=user.id
    )

# ----------------- USER & PROFILE ENDPOINTS -----------------

@app.get("/api/users/me", response_model=schemas.UserProfileResponse)
def get_me(user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    topics_data = []
    for ut in user.topics:
        topics_data.append({
            "topic_id": ut.topic_id,
            "topic_name": ut.topic.name,
            "category": ut.topic.category,
            "rating": ut.rating
        })

    avail_data = [{"day": a.day, "hour": a.hour} for a in user.availability]

    return schemas.UserProfileResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        major=user.major,
        avatar=user.avatar or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&q=80",
        bio=user.bio or "CS Senior interested in Algorithms, Systems, and Machine Learning.",
        study_style=user.study_style or "Collaborative problem-solving & sprint sessions",
        topics=topics_data,
        availability=avail_data
    )

@app.get("/api/topics", response_model=List[schemas.TopicSchema])
def list_topics(db: Session = Depends(get_db)):
    return db.query(models.Topic).all()

@app.post("/api/users/profile")
def update_profile(
    payload: schemas.ProfileUpdate,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if payload.name:
        user.name = payload.name
    if payload.major:
        user.major = payload.major
    if payload.bio is not None:
        user.bio = payload.bio
    if payload.study_style is not None:
        user.study_style = payload.study_style
    if payload.avatar:
        user.avatar = payload.avatar

    # Replace user topics safely
    db.query(models.UserTopic).filter(models.UserTopic.user_id == user.id).delete()
    for t in payload.topics:
        db.add(models.UserTopic(user_id=user.id, topic_id=t.topic_id, rating=t.rating))

    # Replace availability safely
    db.query(models.Availability).filter(models.Availability.user_id == user.id).delete()
    for a in payload.availability:
        db.add(models.Availability(user_id=user.id, day=a.day, hour=a.hour))

    db.commit()
    db.refresh(user)
    return {"status": "success", "message": "Profile updated successfully"}

# ----------------- GROUPS & SUGGESTIONS ENDPOINTS -----------------

@app.get("/api/groups", response_model=List[schemas.GroupItem])
def list_groups(db: Session = Depends(get_db)):
    groups = db.query(models.Group).all()
    results = []
    for g in groups:
        extras = serialize_group_extras(g)
        results.append(schemas.GroupItem(
            id=g.id,
            name=g.name,
            course=g.course,
            image=g.image,
            max_members=g.max_members,
            members_count=len(g.members),
            members=[
                schemas.GroupMemberItem(
                    user_id=m.user.id,
                    name=m.user.name,
                    avatar=m.user.avatar,
                    role=m.role
                ) for m in g.members
            ],
            **extras
        ))
    return results

@app.post("/api/groups/{group_id}/join")
def request_to_join_group(
    group_id: int,
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check if user already member
    already_member = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id,
        models.GroupMember.user_id == user.id
    ).first()
    if already_member:
        raise HTTPException(status_code=400, detail="You are already a member of this group")

    # Check group capacity
    current_members_count = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group_id
    ).count()
    if current_members_count >= group.max_members:
        raise HTTPException(status_code=400, detail="This study group is already at full capacity")

    # If the group has no leader or was created by this user, auto-join as leader
    if group.created_by == user.id or current_members_count == 0:
        new_member = models.GroupMember(
            group_id=group_id,
            user_id=user.id,
            role="leader"
        )
        db.add(new_member)
        db.commit()
        return {"status": "success", "message": f"Joined {group.name} as leader!", "joined": True}

    # Otherwise, submit/check join request
    existing_req = db.query(models.JoinRequest).filter(
        models.JoinRequest.group_id == group_id,
        models.JoinRequest.user_id == user.id
    ).first()

    if existing_req:
        if existing_req.status == "pending":
            return {"status": "info", "message": "Your join request is already pending group leader review.", "joined": False}
        elif existing_req.status == "rejected":
            existing_req.status = "pending"
            db.commit()
            return {"status": "success", "message": "Join request re-submitted for approval!", "joined": False}

    req = models.JoinRequest(
        group_id=group_id,
        user_id=user.id,
        status="pending"
    )
    db.add(req)
    db.commit()
    return {"status": "success", "message": f"Join request sent to the leader of {group.name}!", "joined": False}


@app.get("/api/groups/my-requests")
def get_my_group_requests(
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Returns:
    1. pending_incoming: Join requests waiting for my approval on groups I lead or created.
    2. my_outgoing: Groups I have requested to join and their status.
    """
    # Groups where user is creator or leader
    lead_group_ids = [
        gm.group_id for gm in db.query(models.GroupMember).filter(
            models.GroupMember.user_id == user.id,
            models.GroupMember.role == "leader"
        ).all()
    ]
    created_group_ids = [
        g.id for g in db.query(models.Group).filter(models.Group.created_by == user.id).all()
    ]
    my_managed_group_ids = list(set(lead_group_ids + created_group_ids))

    incoming_raw = db.query(models.JoinRequest).filter(
        models.JoinRequest.group_id.in_(my_managed_group_ids),
        models.JoinRequest.status == "pending"
    ).all() if my_managed_group_ids else []

    incoming = []
    for r in incoming_raw:
        # Get applicant topic ratings
        topics_info = [
            {"topic": ut.topic.name, "rating": ut.rating}
            for ut in r.user.topics
        ]
        incoming.append({
            "request_id": r.id,
            "group_id": r.group.id,
            "group_name": r.group.name,
            "user_id": r.user.id,
            "user_name": r.user.name,
            "user_major": r.user.major,
            "user_avatar": r.user.avatar,
            "topics": topics_info,
            "status": r.status
        })

    outgoing_raw = db.query(models.JoinRequest).filter(
        models.JoinRequest.user_id == user.id
    ).all()

    outgoing = {
        r.group_id: r.status for r in outgoing_raw
    }

    return {
        "incoming_requests": incoming,
        "my_outgoing_statuses": outgoing
    }


@app.post("/api/groups/requests/{request_id}/respond")
def respond_to_join_request(
    request_id: int,
    action: str,  # "accept" or "reject"
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(models.JoinRequest).filter(models.JoinRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    group = req.group
    # Verify permission: must be creator or leader
    is_creator = group.created_by == user.id
    my_membership = db.query(models.GroupMember).filter(
        models.GroupMember.group_id == group.id,
        models.GroupMember.user_id == user.id
    ).first()
    is_leader = my_membership and my_membership.role == "leader"

    if not (is_creator or is_leader):
        raise HTTPException(status_code=403, detail="Only team leaders or creators can accept/reject applicants")

    if action == "accept":
        # Check capacity
        current_members_count = db.query(models.GroupMember).filter(
            models.GroupMember.group_id == group.id
        ).count()
        if current_members_count >= group.max_members:
            raise HTTPException(status_code=400, detail="Cannot accept applicant: study group is at full capacity")

        req.status = "accepted"
        # Add to group_members
        existing_m = db.query(models.GroupMember).filter(
            models.GroupMember.group_id == group.id,
            models.GroupMember.user_id == req.user_id
        ).first()
        if not existing_m:
            db.add(models.GroupMember(
                group_id=group.id,
                user_id=req.user_id,
                role="member"
            ))
        db.commit()
        return {"status": "success", "message": f"Accepted {req.user.name} into {group.name}!"}

    elif action == "reject":
        req.status = "rejected"
        db.commit()
        return {"status": "success", "message": f"Rejected application from {req.user.name}."}

    raise HTTPException(status_code=400, detail="Invalid action. Must be 'accept' or 'reject'.")

@app.get("/api/suggestions/wheel", response_model=List[schemas.WheelCandidateItem])
def get_wheel_suggestions(
    user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Collect user ratings and schedule slots
    user_ratings = {ut.topic_id: ut.rating for ut in user.topics}
    user_slots = {(a.day, a.hour) for a in user.availability}

    # Preload topic names dictionary
    topic_dict = {t.id: t.name for t in db.query(models.Topic).all()}
    set_topic_names(topic_dict)

    # 2. Exclude groups the user is already in
    joined_group_ids = [m.group_id for m in user.group_memberships]

    candidate_groups = db.query(models.Group).filter(
        ~models.Group.id.in_(joined_group_ids) if joined_group_ids else True
    ).all()

    # 3. Format candidate groups for the ML matcher
    ml_candidate_groups = []
    group_map = {}

    for group in candidate_groups:
        # Filter out groups at full capacity (or >= 5 as per matcher specs)
        if len(group.members) >= group.max_members or len(group.members) >= 5:
            continue

        group_map[group.id] = group

        members_ratings = {}
        members_slots = []
        for member_rel in group.members:
            m_user = member_rel.user
            members_ratings[m_user.id] = {ut.topic_id: ut.rating for ut in m_user.topics}
            members_slots.append({(a.day, a.hour) for a in m_user.availability})

        ml_candidate_groups.append({
            "id": group.id,
            "name": group.name,
            "members": members_ratings,
            "member_slots": members_slots
        })

    # 4. Rank using ML Logistic Regression model (with automatic heuristic fallback)
    ranked_ml_results = rank_groups(user_ratings, user_slots, ml_candidate_groups)

    scored_groups = []
    for r in ranked_ml_results:
        group = group_map.get(r["group_id"])
        if not group:
            continue

        member_names = [m.user.name for m in group.members]
        extras = serialize_group_extras(group)

        weak_badge = topic_dict.get(r["weak_topic_id"], "Need Support") if r["weak_topic_id"] else "Balanced"
        strong_badge = topic_dict.get(r["strong_topic_id"], "Peer Leader") if r["strong_topic_id"] else "Contributor"

        scored_groups.append({
            "id": group.id,
            "label": group.name,
            "image": group.image or "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=1200&q=80",
            "course": group.course,
            "members_count": len(group.members),
            "max_members": group.max_members,
            "match_score": r["match_score"],
            "weak_topic": weak_badge,
            "strong_topic": strong_badge,
            "why_matched": r["why_matched"],
            "overlapping_hours": r["overlap_hours"],
            "members": member_names,
            **extras
        })

    return scored_groups
