from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# cargar .env
load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    raise Exception("❌ DATABASE_URL no cargada. Revisa tu archivo .env")

SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"
engine = create_engine(DB_URL, echo=SQL_ECHO)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()