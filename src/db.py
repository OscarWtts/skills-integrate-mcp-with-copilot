from sqlmodel import SQLModel, create_engine
from pathlib import Path

# SQLite file for local development. Production should use PostgreSQL via env var.
DB_PATH = Path(__file__).parent.parent / "dev.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    # create sqlite file directory if missing
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
