from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os

# Instancia FastAPI
app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración SQLite
DATABASE_URL = "sqlite:///reservas.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de reservas
class Reserva(Base):
    __tablename__ = "reservas"
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(String, index=True)
    hora_inicio = Column(String)
    hora_fin = Column(String)
    responsable = Column(String)
    grupo = Column(String)
    email = Column(String)

Base.metadata.create_all(bind=engine)

# Conexión DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------
# RUTAS FRONTEND
# -------------------------------
@app.get("/")
def root():
    return {"mensaje": "Sistema activo"}

@app.get("/index.html")
def get_index():
    file_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(file_path)

@app.get("/logo_usm.png")
def get_logo_usm():
    file_path = os.path.join(os.path.dirname(__file__), "logo_usm.png")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Logo USM no encontrado")
    return FileResponse(file_path)

@app.get("/logo_electronica.png")
def get_logo_electronica():
    file_path = os.path.join(os.path.dirname(__file__), "logo_electronica.png")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Logo Electrónica no encontrado")
    return FileResponse(file_path)

# -------------------------------
# RUTAS RESERVAS
# -------------------------------
@app.get("/reservas")
def listar_reservas(db: Session = Depends(get_db)):
    return db.query(Reserva).all()

@app.post("/reservas")
def crear_reserva(reserva: dict, db: Session = Depends(get_db)):
    if not reserva.get("email", "").endswith("@usm.cl"):
        raise HTTPException(status_code=400, detail="Email inválido")
    nueva = Reserva(**reserva)
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return JSONResponse(content={"mensaje": "Reserva creada"}, status_code=200)

@app.put("/reservas/{id}")
def actualizar_reserva(id: int, reserva: dict, db: Session = Depends(get_db)):
    r = db.query(Reserva).filter(Reserva.id == id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    for key, value in reserva.items():
        setattr(r, key, value)
    db.commit()
    db.refresh(r)
    return {"mensaje": "Reserva actualizada"}

@app.delete("/reservas/{id}")
def eliminar_reserva(id: int, db: Session = Depends(get_db)):
    r = db.query(Reserva).filter(Reserva.id == id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    db.delete(r)
    db.commit()
    return {"mensaje": "Reserva eliminada"}

@app.get("/api/status")
def status():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
