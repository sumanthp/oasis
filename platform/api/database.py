from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os
from pathlib import Path

# Ensure data directory exists
data_dir = Path(__file__).parent.parent.parent / "data"
data_dir.mkdir(exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{data_dir}/ai_engine.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=True)
    role = Column(String, default="candidate") # admin, candidate, demo
    created_at = Column(DateTime, default=datetime.utcnow)

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    challenge_id = Column(String)
    status = Column(String, default="started") # running, completed, abandoned
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    ide_port = Column(Integer, nullable=True) # Dynamically assigned Docker port
    ide_time_seconds = Column(Integer, nullable=True)
    tab_switch_count = Column(Integer, default=0)  # Anti-cheating telemetry
    paste_count = Column(Integer, default=0)        # Anti-cheating telemetry
    
    user = relationship("User")
    evaluations = relationship("Evaluation", back_populates="session")

class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    execution_time_seconds = Column(Integer)
    verdict = Column(String) # HIRE, PASS, REVIEW
    feedback_text = Column(String)
    candidate_code = Column(String, nullable=True)
    ai_trace_logs = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="evaluations")

class Invite(Base):
    __tablename__ = "invites"
    
    id = Column(String, primary_key=True, index=True) # the token
    created_by = Column(String, ForeignKey("users.id"))
    used_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_used = Column(Integer, default=0) # boolean 0 or 1

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Seed default admin user
    # Seed default admin user
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            import uuid
            admin = User(
                id=str(uuid.uuid4()),
                username="admin",
                password_hash=pwd_context.hash("admin"),
                role="admin"
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
