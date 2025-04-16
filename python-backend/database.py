from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base  # Import the Base class where your Message model is defined

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:root@127.0.0.1:3306/chat_app"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if not already created
Base.metadata.create_all(bind=engine)
