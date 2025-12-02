from config import DATABASE_CONFIG
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Update your DB credentials
DATABASE_URL = f"postgresql+psycopg2://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"

# Engine and session
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# Declarative base for all models
Base = declarative_base()
