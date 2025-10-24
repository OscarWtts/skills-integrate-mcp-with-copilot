"""
High School Management System API (with simple persistence)

This update replaces the in-memory data store with a small SQLite-backed
implementation using SQLModel. It is intentionally minimal for development
and to keep the exercise simple; production should use PostgreSQL and
Alembic migrations (see issue #8).
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
import os
from sqlmodel import Session, select

from .models import Activity, Participant
from .db import engine, init_db


app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")


# Mount static files
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")


@app.on_event("startup")
def on_startup():
    # initialize DB and create tables
    init_db()

    # Ensure there is some seed data if DB is empty
    with Session(engine) as session:
        count = session.exec(select(Activity)).all()
        if not count:
            seed_activities = [
                Activity(name="Chess Club", description="Learn strategies and compete in chess tournaments", schedule="Fridays, 3:30 PM - 5:00 PM", max_participants=12),
                Activity(name="Programming Class", description="Learn programming fundamentals and build software projects", schedule="Tuesdays and Thursdays, 3:30 PM - 4:30 PM", max_participants=20),
                Activity(name="Gym Class", description="Physical education and sports activities", schedule="Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM", max_participants=30),
                Activity(name="Soccer Team", description="Join the school soccer team and compete in matches", schedule="Tuesdays and Thursdays, 4:00 PM - 5:30 PM", max_participants=22),
            ]
            session.add_all(seed_activities)
            session.commit()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


def activity_to_dict(activity: Activity) -> dict:
    participants = [p.email for p in activity.participants] if activity.participants else []
    return {
        activity.name: {
            "description": activity.description or "",
            "schedule": activity.schedule or "",
            "max_participants": activity.max_participants or 0,
            "participants": participants,
        }
    }


@app.get("/activities")
def get_activities():
    with Session(engine) as session:
        activities = session.exec(select(Activity)).all()
        # Need to eagerly load participants
        result = {}
        for a in activities:
            # reload participants
            a = session.get(Activity, a.id)
            session.refresh(a, attribute_names=["participants"])
            result.update(activity_to_dict(a))
        return result


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    with Session(engine) as session:
        activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        session.refresh(activity, attribute_names=["participants"])

        # capacity check
        if activity.max_participants and len(activity.participants) >= activity.max_participants:
            raise HTTPException(status_code=400, detail="Activity is full")

        # duplicate check
        for p in activity.participants:
            if p.email.lower() == email.lower():
                raise HTTPException(status_code=400, detail="Student is already signed up")

        participant = Participant(email=email, activity_id=activity.id)
        session.add(participant)
        session.commit()
        return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    with Session(engine) as session:
        activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        session.refresh(activity, attribute_names=["participants"])

        participant = None
        for p in activity.participants:
            if p.email.lower() == email.lower():
                participant = p
                break

        if not participant:
            raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

        session.delete(participant)
        session.commit()
        return {"message": f"Unregistered {email} from {activity_name}"}

