"""
StudySync group chat router (FastAPI + SQLAlchemy).
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Session

from app.database import Base, get_db
from app.auth import get_current_user
from app.models import Group, GroupMember, User

router = APIRouter(prefix="/chat", tags=["chat"])

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text = Column(String(1000), nullable=False)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

class MessageIn(BaseModel):
    text: str = Field(..., max_length=1000)

def _iso(dt: datetime) -> str:
    return dt.isoformat() + "Z"

def _out(m: Message, user_name: str) -> dict:
    return {
        "id": m.id,
        "group_id": m.group_id,
        "user_id": m.user_id,
        "user_name": user_name,
        "text": m.text,
        "created_at": _iso(m.created_at),
    }

def _require_member(db: Session, group_id: int, user_id: int) -> None:
    ok = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        .first()
    )
    if not ok:
        raise HTTPException(status_code=403, detail="You are not a member of this group")

@router.get("/groups")
def my_chat_groups(db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    groups = (
        db.query(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .filter(GroupMember.user_id == me.id)
        .all()
    )
    result = []
    for g in groups:
        last = (
            db.query(Message, User.name)
            .join(User, User.id == Message.user_id)
            .filter(Message.group_id == g.id)
            .order_by(Message.id.desc())
            .first()
        )
        members_count = db.query(GroupMember).filter(GroupMember.group_id == g.id).count()
        result.append({
            "id": g.id,
            "name": g.name,
            "course": getattr(g, "course", ""),
            "members_count": members_count,
            "last_message": (
                {"text": last[0].text, "user_name": last[1], "created_at": _iso(last[0].created_at)}
                if last else None
            ),
        })
    result.sort(key=lambda r: r["last_message"]["created_at"] if r["last_message"] else "", reverse=True)
    return result

@router.get("/groups/{group_id}/messages")
def list_messages(
    group_id: int,
    after_id: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    _require_member(db, group_id, me.id)
    q = (
        db.query(Message, User.name)
        .join(User, User.id == Message.user_id)
        .filter(Message.group_id == group_id)
    )
    if after_id:
        rows = q.filter(Message.id > after_id).order_by(Message.id.asc()).limit(limit).all()
    else:
        rows = list(reversed(q.order_by(Message.id.desc()).limit(limit).all()))
    return [_out(m, name) for m, name in rows]

@router.post("/groups/{group_id}/messages")
def send_message(
    group_id: int,
    body: MessageIn,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    _require_member(db, group_id, me.id)
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    msg = Message(group_id=group_id, user_id=me.id, text=text)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return _out(msg, me.name)

@router.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.user_id != me.id:
        raise HTTPException(status_code=403, detail="You can only delete your own messages")
    db.delete(msg)
    db.commit()
    return {"message": "Deleted"}
