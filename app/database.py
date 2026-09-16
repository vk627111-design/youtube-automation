"""Database models for YT Automation."""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum

Base = declarative_base()

# Database file path
DB_PATH = "data/database.db"
os.makedirs("data", exist_ok=True)


class VideoStatus(str, enum.Enum):
    """Video upload status."""
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    SKIPPED = "skipped"


class Video(Base):
    """Video model."""
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    filename = Column(String, unique=True, nullable=False)
    filepath = Column(String, nullable=False)
    title = Column(String, default="")
    description = Column(Text, default="")
    tags = Column(String, default="")  # Comma-separated
    thumbnail_path = Column(String, nullable=True)
    visibility = Column(String, default="private")
    duration = Column(Float, nullable=True)  # seconds
    resolution = Column(String, nullable=True)  # "1920x1080"
    file_size = Column(Float, nullable=True)  # MB
    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING)
    scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Video {self.filename} - {self.status}>"


class UploadJob(Base):
    """Upload job model."""
    __tablename__ = "upload_jobs"

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, nullable=False)
    profile_name = Column(String, default="default")
    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING)
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)
    result_message = Column(Text, nullable=True)
    youtube_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<UploadJob {self.id} - Video {self.video_id} - {self.status}>"


class BrowserProfile(Base):
    """Browser profile model."""
    __tablename__ = "browser_profiles"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    browser_path = Column(String, nullable=True)
    user_data_dir = Column(String, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BrowserProfile {self.name}>"


class Setting(Base):
    """Application settings model."""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, nullable=False)

    def __repr__(self):
        return f"<Setting {self.key}={self.value}>"


class Log(Base):
    """Application log model."""
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    level = Column(String, default="INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Log [{self.level}] {self.message[:50]}...>"


class Database:
    """Database connection manager."""

    def __init__(self, db_path: str = DB_PATH):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.engine = None
        self.SessionLocal = None
        self._init_db()

    def _init_db(self):
        """Initialize database engine and create tables."""
        db_url = f"sqlite:///{self.db_path}"
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get database session."""
        return self.SessionLocal()

    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()


# Global database instance
db = Database()
