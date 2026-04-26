from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Base
from backend.models import Reserva
from datetime import date, time, datetime
import uvicorn
import os

app = FastAPI()  ##Rev PGF

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
    try:
        print("Datos recibidos en crear_reserva:", data)

        # Conversión de fecha
        if "/" in data["fecha"]:
            fecha = datetime.strptime(data["fecha"], "%d/%m/%Y").date()
        else:
            fecha = date.fromisoformat(data["fecha"])

        # Conversión de horas
        inicio = time.fromisoformat(data["hora_inicio"])
        fin = time.fromisoformat(data["hora_fin"])

        # Validaciones
        if inicio < time(8, 0) or fin > time(18, 0):
            raise HTTPException(status_code=400, detail="Horario fuera de rango (08:00 - 18:00)")

        duracion = (fin.hour * 60 + fin.minute) - (inicio.hour * 60 + inicio.minute)
        duracion = duracion / 60
        if duracion < 2 or duracion % 2 != 0 or duracion > 8:
            raise HTTPException(status_code=400, detail="Duración inválida: solo bloques de 2 a 8 horas")

        if not data["email"].endswith("@usm.cl"):
            raise HTTPException(status_code=400, detail="Correo debe ser @usm.cl")

        reservas = db.query(Reserva).filter(Reserva.fecha == fecha).all()
        for r in reservas:
            if not (fin <= r.hora_inicio or inicio >= r.hora_fin):
                raise HTTPException(status_code=400, detail="Horario no disponible")

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

    except Exception as e:
        print("Error en crear_reserva:", str(e))
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


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
