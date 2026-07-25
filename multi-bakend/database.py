from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# cargar .env
load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    raise Exception("❌ DATABASE_URL no cargada. Revisa tu archivo .env")

engine = create_engine(DB_URL, echo=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()