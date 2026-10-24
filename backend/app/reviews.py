"""
StudySync review system (FastAPI + SQLAlchemy).

- Member reviews: 1-5 stars + optional comment, only between people who share a group.
- Group reviews: 1-5 stars only, only by members of that group.
- One review per (reviewer, target); posting again updates the existing one.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func,
)
from sqlalchemy.orm import Session, aliased

from app.database import Base, get_db
from app.auth import get_current_user
from app.models import Group, GroupMember, User

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ----------------- MODELS -----------------

class MemberReview(Base):
    __tablename__ = "member_reviews"

    id = Column(Integer, primary_key=True, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reviewee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)          # 1..5
    comment = Column(String(500), nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=_now)
    updated_at = Column(DateTime, nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint("reviewer_id", "reviewee_id", name="uq_member_review"),
    )


class GroupReview(Base):
    __tablename__ = "group_reviews"

    id = Column(Integer, primary_key=True, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)          # 1..5
    created_at = Column(DateTime, nullable=False, default=_now)
    updated_at = Column(DateTime, nullable=False, default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint("reviewer_id", "group_id", name="uq_group_review"),
    )


# ----------------- SCHEMAS -----------------

class MemberReviewIn(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field("", max_length=500)


class GroupReviewIn(BaseModel):
    rating: int = Field(..., ge=1, le=5)


# ----------------- HELPERS -----------------

def _iso(dt: datetime) -> str:
    return dt.isoformat() + "Z"


def _shares_group(db: Session, a: int, b: int) -> bool:
    ga, gb = aliased(GroupMember), aliased(GroupMember)
    return (
        db.query(ga.id)
        .join(gb, gb.group_id == ga.group_id)
        .filter(ga.user_id == a, gb.user_id == b)
        .first()
        is not None
    )


def _is_member(db: Session, group_id: int, user_id: int) -> bool:
    return (
        db.query(GroupMember.id)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        .first()
        is not None
    )


def _avg(value: Optional[float]) -> float:
    return round(float(value), 1) if value is not None else 0.0


# ----------------- MEMBER REVIEWS -----------------

@router.get("/members/{user_id}")
def get_member_reviews(
    user_id: int,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    rows = (
        db.query(MemberReview, User.name)
        .join(User, User.id == MemberReview.reviewer_id)
        .filter(MemberReview.reviewee_id == user_id)
        .order_by(MemberReview.updated_at.desc())
        .all()
    )
    count = len(rows)
    avg = _avg(sum(r.rating for r, _ in rows) / count) if count else 0.0
    mine = next((r for r, _ in rows if r.reviewer_id == me.id), None)

    return {
        "user_id": target.id,
        "name": target.name,
        "avg": avg,
        "count": count,
        "can_review": me.id != target.id and _shares_group(db, me.id, target.id),
        "my_review": {"rating": mine.rating, "comment": mine.comment} if mine else None,
        "reviews": [
            {
                "id": r.id,
                "reviewer_name": name,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": _iso(r.updated_at),
                "is_mine": r.reviewer_id == me.id,
            }
            for r, name in rows
        ],
    }


@router.post("/members/{user_id}")
def post_member_review(
    user_id: int,
    body: MemberReviewIn,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    if user_id == me.id:
        raise HTTPException(status_code=400, detail="You can't review yourself")
    if not db.query(User.id).filter(User.id == user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    if not _shares_group(db, me.id, user_id):
        raise HTTPException(status_code=403, detail="You can only review people you share a study group with")

    comment = body.comment.strip()
    review = (
        db.query(MemberReview)
        .filter(MemberReview.reviewer_id == me.id, MemberReview.reviewee_id == user_id)
        .first()
    )
    if review:
        review.rating = body.rating
        review.comment = comment
    else:
        db.add(MemberReview(reviewer_id=me.id, reviewee_id=user_id, rating=body.rating, comment=comment))
    db.commit()
    return {"status": "success", "message": "Review saved"}


@router.delete("/members/{user_id}")
def delete_member_review(
    user_id: int,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    review = (
        db.query(MemberReview)
        .filter(MemberReview.reviewer_id == me.id, MemberReview.reviewee_id == user_id)
        .first()
    )
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)
    db.commit()
    return {"status": "success", "message": "Review deleted"}


# ----------------- GROUP REVIEWS -----------------
# NOTE: /groups/summary is declared before /groups/{group_id} so "summary"
# isn't parsed as an int group_id.

@router.get("/groups/summary")
def groups_summary(
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    """One call for the Teams page: avg, count, my rating and can_review per group."""
    stats = {
        gid: (avg, cnt)
        for gid, avg, cnt in db.query(
            GroupReview.group_id, func.avg(GroupReview.rating), func.count(GroupReview.id)
        ).group_by(GroupReview.group_id).all()
    }
    mine = {
        r.group_id: r.rating
        for r in db.query(GroupReview).filter(GroupReview.reviewer_id == me.id).all()
    }
    member_of = {
        gid for (gid,) in db.query(GroupMember.group_id).filter(GroupMember.user_id == me.id).all()
    }
    out = []
    for (gid,) in db.query(Group.id).all():
        avg, cnt = stats.get(gid, (None, 0))
        out.append({
            "group_id": gid,
            "avg": _avg(avg),
            "count": cnt,
            "my_rating": mine.get(gid),
            "can_review": gid in member_of,
        })
    return out


@router.post("/groups/{group_id}")
def post_group_review(
    group_id: int,
    body: GroupReviewIn,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    if not db.query(Group.id).filter(Group.id == group_id).first():
        raise HTTPException(status_code=404, detail="Group not found")
    if not _is_member(db, group_id, me.id):
        raise HTTPException(status_code=403, detail="Only members can rate this group")

    review = (
        db.query(GroupReview)
        .filter(GroupReview.reviewer_id == me.id, GroupReview.group_id == group_id)
        .first()
    )
    if review:
        review.rating = body.rating
    else:
        db.add(GroupReview(reviewer_id=me.id, group_id=group_id, rating=body.rating))
    db.commit()

    avg, cnt = db.query(func.avg(GroupReview.rating), func.count(GroupReview.id)).filter(
        GroupReview.group_id == group_id
    ).one()
    return {"status": "success", "avg": _avg(avg), "count": cnt, "my_rating": body.rating}


@router.delete("/groups/{group_id}/members/{user_id}")
def remove_group_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check if requester is group creator or leader or self
    is_creator = group.created_by == me.id
    my_membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id, GroupMember.user_id == me.id
    ).first()
    is_leader = my_membership and my_membership.role == "leader"

    if not (is_creator or is_leader or me.id == user_id):
        raise HTTPException(status_code=403, detail="Only team leaders or creators can remove members")

    membership_to_remove = db.query(GroupMember).filter(
        GroupMember.group_id == group_id, GroupMember.user_id == user_id
    ).first()
    if not membership_to_remove:
        raise HTTPException(status_code=404, detail="Member not found in this group")

    db.delete(membership_to_remove)
    db.commit()
    return {"status": "success", "message": "Member removed from study group"}
