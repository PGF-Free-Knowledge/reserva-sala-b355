import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Leer la variable DATABASE_URL que configuraste en Render
DATABASE_URL = os.getenv("DATABASE_URL")

# Crear el engine con esa URL
engine = create_engine(DATABASE_URL)

# Configurar sesión y base declarativa
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Inicializar la base de datos (crear tablas si no existen)
def init_db():
    Base.metadata.create_all(bind=engine)

# Obtener sesión de base de datos (para usar en main.py)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

