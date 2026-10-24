from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str
    major: Optional[str] = "Computer Science"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_name: str
    user_id: int

class TopicSchema(BaseModel):
    id: int
    name: str
    category: str

    class Config:
        from_attributes = True

class UserTopicInput(BaseModel):
    topic_id: int
    rating: int  # 1 to 5

class AvailabilityInput(BaseModel):
    day: str    # "Mon", "Tue", ...
    hour: int   # 0 to 23

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    major: Optional[str] = None
    bio: Optional[str] = None
    study_style: Optional[str] = None
    avatar: Optional[str] = None
    topics: List[UserTopicInput]
    availability: List[AvailabilityInput]

class UserProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    major: str
    avatar: str
    bio: Optional[str] = ""
    study_style: Optional[str] = ""
    topics: List[dict]
    availability: List[dict]

class WheelCandidateItem(BaseModel):
    id: int
    label: str
    image: str
    course: str
    members_count: int
    max_members: int
    match_score: float
    weak_topic: str
    strong_topic: str
    why_matched: str
    overlapping_hours: int
    members: List[str]
    description: Optional[str] = ""
    mode: Optional[str] = "hybrid"
    venue: Optional[str] = ""
    meeting_link: Optional[str] = ""
    pace: Optional[str] = "Exam prep"
    study_days: Optional[List[str]] = []
    start_hour: Optional[int] = 14
    end_hour: Optional[int] = 17
    topic_ids: Optional[List[int]] = []
    created_by: Optional[int] = None

class GroupMemberItem(BaseModel):
    user_id: int
    name: str
    avatar: str
    role: str

class GroupItem(BaseModel):
    id: int
    name: str
    course: str
    image: str
    max_members: int
    members_count: int
    members: List[GroupMemberItem]
    description: Optional[str] = ""
    mode: Optional[str] = "hybrid"
    venue: Optional[str] = ""
    meeting_link: Optional[str] = ""
    pace: Optional[str] = "Exam prep"
    study_days: Optional[List[str]] = []
    start_hour: Optional[int] = 14
    end_hour: Optional[int] = 17
    topic_ids: Optional[List[int]] = []
    created_by: Optional[int] = None

    class Config:
        from_attributes = True
