from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session
import os

# Importar conexión desde database.py
from backend.database import SessionLocal, Base, init_db, get_db

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

# Inicializar tablas en Postgres
init_db()

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

    # Validaciones de fecha y horario
    from datetime import datetime, time
    fecha = datetime.strptime(reserva["fecha"], "%Y-%m-%d").date()
    hora_inicio = datetime.strptime(reserva["hora_inicio"], "%H:%M").time()
    hora_fin = datetime.strptime(reserva["hora_fin"], "%H:%M").time()

    if fecha < datetime.today().date():
        raise HTTPException(status_code=400, detail="No se permiten reservas en fechas anteriores al día actual")
    if fecha.weekday() >= 5:
        raise HTTPException(status_code=400, detail="Solo se permiten reservas de lunes a viernes")
    if hora_inicio < time(8,0) or hora_fin > time(18,0):
        raise HTTPException(status_code=400, detail="Reservas solo entre 08:00 y 18:00")
    if hora_inicio.minute != 0 or hora_fin.minute != 0:
        raise HTTPException(status_code=400, detail="Las horas deben ser exactas (ej: 08:00, 10:00)")
    if hora_inicio.hour % 2 != 0 or hora_fin.hour % 2 != 0:
        raise HTTPException(status_code=400, detail="Las reservas deben comenzar y terminar en horas pares")

    duracion = (datetime.combine(fecha, hora_fin) - datetime.combine(fecha, hora_inicio)).seconds / 3600
    if duracion < 2:
        raise HTTPException(status_code=400, detail="La duración mínima es de 2 horas")

    reservas_grupo = db.query(Reserva).filter(
        Reserva.grupo == reserva["grupo"],
        Reserva.fecha == reserva["fecha"]
    ).all()
    horas_existentes = sum(
        (datetime.combine(fecha, r.hora_fin) - datetime.combine(fecha, r.hora_inicio)).seconds / 3600
        for r in reservas_grupo
    )
    if horas_existentes + duracion > 4:
        raise HTTPException(status_code=400, detail="Cada grupo puede reservar máximo 4 horas por día")

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

