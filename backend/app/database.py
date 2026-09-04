import pathlib, datetime, json
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, Float
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = pathlib.Path(__file__).parent.parent / "data" / "thyroid.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="admin")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String, primary_key=True)  # batchId
    filename = Column(String)
    original_name = Column(String)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="uploaded") # uploaded, analyzed, failed
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    missing = Column(Integer, default=0)
    duplicates = Column(Integer, default=0)
    invalid = Column(Integer, default=0)
    model_used = Column(String, default="")
    stats_json = Column(Text, default="{}") # store analytics summary

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    dataset_id = Column(String, index=True)
    patient_id = Column(String, index=True)
    age = Column(String)
    gender = Column(String)
    tsh = Column(String)
    t3 = Column(String)
    tt4 = Column(String)
    raw_json = Column(Text)

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    dataset_id = Column(String, index=True)
    patient_id = Column(String, index=True)
    overall = Column(String) # Positive / Negative
    category = Column(String) # hypothyroid / hyperthyroid / negative etc
    risk = Column(String) # Higher Risk / Lower Risk (only for Negative)
    score = Column(Float) # proba*100
    confidence = Column(Float)
    top_features_json = Column(Text)

def init_db():
    Base.metadata.create_all(bind=engine)
    # create default admin if missing
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email=="admin@lab.local").first():
            u = User(email="admin@lab.local", password_hash=pwd.hash("admin123"), role="admin")
            db.add(u); db.commit()
            print("Created default admin: admin@lab.local / admin123")
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
