from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    major = Column(String, default="Computer Science")
    avatar = Column(String, default="")
    bio = Column(String, default="CS Senior interested in Algorithms, Systems, and Machine Learning.")
    study_style = Column(String, default="Collaborative problem-solving & sprint sessions")

    topics = relationship("UserTopic", back_populates="user", cascade="all, delete-orphan")
    availability = relationship("Availability", back_populates="user", cascade="all, delete-orphan")
    group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, default="General")


class UserTopic(Base):
    __tablename__ = "user_topics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 (Needs help) to 5 (Excels/Tutor)

    user = relationship("User", back_populates="topics")
    topic = relationship("Topic")

    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_user_topic"),
    )


class Availability(Base):
    __tablename__ = "availability"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    day = Column(String, nullable=False)    # e.g., "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"
    hour = Column(Integer, nullable=False)  # 0 to 23

    user = relationship("User", back_populates="availability")

    __table_args__ = (
        UniqueConstraint("user_id", "day", "hour", name="uq_user_day_hour"),
    )


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)     # e.g. "AlgoRhythms"
    course = Column(String, nullable=False)   # e.g. "CS 4820: Algorithms"
    image = Column(String, default="")
    max_members = Column(Integer, default=5)

    description = Column(String(300), default="")
    mode = Column(String(10), default="hybrid")       # online | in-person | hybrid
    venue = Column(String(120), default="")
    meeting_link = Column(String(300), default="")
    pace = Column(String(30), default="Exam prep")
    study_days = Column(JSON, default=list)                  # ["Tue", "Thu"]
    start_hour = Column(Integer, default=14)
    end_hour = Column(Integer, default=17)
    topic_ids = Column(JSON, default=list)                  # [1, 4, 7]
    created_by = Column(Integer, ForeignKey("users.id"))

    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, default="member")   # "leader" or "member"

    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user"),
    )


class JoinRequest(Base):
    __tablename__ = "join_requests"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending")  # "pending", "accepted", "rejected"
    message = Column(String(300), default="")

    group = relationship("Group")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_request_user"),
    )
