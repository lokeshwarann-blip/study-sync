"""
StudySync: "Create your own team" endpoint (FastAPI + SQLAlchemy).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import Group, GroupMember, User

router = APIRouter(tags=["groups"])

MODES = {"online", "in-person", "hybrid"}
PACES = {"Exam prep", "Project sprint", "Assignment help", "Deep dive", "Casual revision"}
DAYS = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=40)
    course: str = Field(..., min_length=2, max_length=80)
    description: str = Field("", max_length=300)
    topic_ids: list[int]
    max_members: int = Field(5, ge=2, le=10)
    pace: str = "Exam prep"
    mode: str = "hybrid"
    venue: str = Field("", max_length=120)
    meeting_link: str = Field("", max_length=300)
    study_days: list[str]
    start_hour: int = Field(14, ge=0, le=23)
    end_hour: int = Field(17, ge=1, le=24)


def serialize_group_extras(g: Group) -> dict:
    """Merge this into your existing group dicts (GET /groups, wheel suggestions)."""
    return {
        "description": g.description or "",
        "mode": g.mode or "hybrid",
        "venue": g.venue or "",
        "meeting_link": g.meeting_link or "",
        "pace": g.pace or "Exam prep",
        "study_days": g.study_days or [],
        "start_hour": g.start_hour if g.start_hour is not None else 14,
        "end_hour": g.end_hour if g.end_hour is not None else 17,
        "topic_ids": g.topic_ids or [],
        "created_by": g.created_by,
    }


@router.post("/groups")
def create_group(
    body: GroupCreate,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    name, course = body.name.strip(), body.course.strip()

    if not body.topic_ids:
        raise HTTPException(400, "Pick at least one topic")
    if not body.study_days or not set(body.study_days) <= DAYS:
        raise HTTPException(400, "Pick valid study days (Mon-Sun)")
    if body.mode not in MODES:
        raise HTTPException(400, "Mode must be online, in-person or hybrid")
    if body.pace not in PACES:
        raise HTTPException(400, "Invalid pace")
    if body.end_hour <= body.start_hour:
        raise HTTPException(400, "End time must be after start time")
    if body.mode != "online" and not body.venue.strip():
        raise HTTPException(400, "Venue is required for in-person or hybrid teams")
    link = body.meeting_link.strip()
    if link and not link.lower().startswith(("http://", "https://")):
        raise HTTPException(400, "Meeting link must start with http:// or https://")

    exists = db.query(Group).filter(Group.name == name, Group.course == course).first()
    if exists:
        raise HTTPException(409, "A team with this name already exists for that course")

    group = Group(
        name=name,
        course=course,
        description=body.description.strip(),
        topic_ids=sorted(set(body.topic_ids)),
        max_members=body.max_members,
        pace=body.pace,
        mode=body.mode,
        venue=body.venue.strip(),
        meeting_link=link,
        study_days=[d for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] if d in body.study_days],
        start_hour=body.start_hour,
        end_hour=body.end_hour,
        created_by=me.id,
    )
    db.add(group)
    db.flush()  # get group.id

    db.add(GroupMember(group_id=group.id, user_id=me.id, role="leader"))  # creator is first member
    db.commit()
    db.refresh(group)

    return {
        "id": group.id,
        "name": group.name,
        "course": group.course,
        "max_members": group.max_members,
        "members_count": 1,
        "message": f'Team "{group.name}" created',
        **serialize_group_extras(group),
    }
