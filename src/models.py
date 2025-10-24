from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel


class Participant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    activity_id: int = Field(foreign_key="activity.id")


class Activity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    schedule: Optional[str] = None
    max_participants: Optional[int] = None
    participants: List[Participant] = Relationship(back_populates="activity")


# back-populate relationship (SQLModel requires assignment on the other side)
Participant.__fields__["activity_id"]
