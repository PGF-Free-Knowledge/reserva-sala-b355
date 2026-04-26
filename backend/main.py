from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Base
from models import Reserva
from datetime import date, time
import uvicorn
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas
Base.metadata.create_all(bind=engine)

# Conexión a DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint raíz
@app.get("/")
def inicio():
    return {"mensaje": "Sistema funcionando con base de datos"}

# Crear reserva
@app.post("/reservas")
def crear_reserva(data: dict, db: Session = Depends(get_db)):
    inicio = time.fromisoformat(data["hora_inicio"])
    fin = time.fromisoformat(data["hora_fin"])
    fecha = date.fromisoformat(data["fecha"])

    # Validar horario
    if inicio < time(8, 0) or fin > time(18, 0):
        raise HTTPException(status_code=400, detail="Horario fuera de rango (08:00 - 18:00)")

    # Validar duración
    duracion = fin.hour - inicio.hour
    if duracion < 2 or duracion % 2 != 0 or duracion > 8:
        raise HTTPException(status_code=400, detail="Duración inválida: solo bloques de 2 a 8 horas")

    # Validar correo
    if not data["email"].endswith("@usm.cl"):
        raise HTTPException(status_code=400, detail="Correo debe ser @usm.cl")

    # Validar conflicto de horario
    reservas = db.query(Reserva).filter(Reserva.fecha == fecha).all()

    for r in reservas:
        if not (fin <= r.hora_inicio or inicio >= r.hora_fin):
            raise HTTPException(status_code=400, detail="Horario no disponible")

    # Guardar
    nueva = Reserva(
        fecha=fecha,
        hora_inicio=inicio,
        hora_fin=fin,
        responsable=data["responsable"],
        grupo=data["grupo"],
        email=data["email"]
    )

    db.add(nueva)
    db.commit()

    return {"mensaje": "Reserva guardada correctamente"}

# Listar reservas
@app.get("/reservas")
def listar_reservas(db: Session = Depends(get_db)):
    reservas = db.query(Reserva).all()
    return reservas

# Eliminar reserva
@app.delete("/reservas/{reserva_id}")
def eliminar_reserva(reserva_id: int, db: Session = Depends(get_db)):
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()

    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    db.delete(reserva)
    db.commit()

    return {"mensaje": "eliminado"}

# RUN (IMPORTANTE PARA RENDER)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)