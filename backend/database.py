from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://database_reserva_db_user:MRO8wVhLSjZeo0vi2BrDEvR5iqjyZzDM@dpg-d7oamsdckfvc73fgjp50-a:5432/database_reserva_db"


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()