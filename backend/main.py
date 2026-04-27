from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Base
from backend.models import Reserva
from datetime import date, time, datetime
from pydantic import BaseModel
import uvicorn
import os

# Importa el frontend Dash
from fastapi.middleware.wsgi import WSGIMiddleware
from frontend.app import app as dash_app   # aquí está tu app.py

app = FastAPI()  ##Rev PGF

# Monta el frontend en la raíz "/"
app.mount("/", WSGIMiddleware(dash_app))

# Mueve tu endpoint de prueba a otra ruta
@app.get("/api/status")
def status():
    return {"mensaje": "Sistema funcionando con base de datos"}

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)




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

# Modelo de entrada
class ReservaInput(BaseModel):
    fecha: str
    hora_inicio: str
    hora_fin: str
    responsable: str
    grupo: str
    email: str

# Endpoint raíz
@app.get("/")
def inicio():
    return {"mensaje": "Sistema funcionando con base de datos"}

# Crear reserva
@app.post("/reservas")
def crear_reserva(data: ReservaInput, db: Session = Depends(get_db)):
    try:
        print("Datos recibidos en crear_reserva:", data.dict())

        # Conversión de fecha
        if "/" in data.fecha:
            fecha = datetime.strptime(data.fecha, "%d/%m/%Y").date()
        else:
            fecha = date.fromisoformat(data.fecha)

        # Conversión de horas
        inicio = time.fromisoformat(data.hora_inicio)
        fin = time.fromisoformat(data.hora_fin)

        # Validaciones
        if inicio < time(8, 0) or fin > time(18, 0):
            raise HTTPException(status_code=400, detail="Horario fuera de rango (08:00 - 18:00)")

        duracion = (fin.hour * 60 + fin.minute) - (inicio.hour * 60 + inicio.minute)
        duracion = duracion / 60
        if duracion < 2 or duracion % 2 != 0 or duracion > 8:
            raise HTTPException(status_code=400, detail="Duración inválida: solo bloques de 2 a 8 horas")

        if not data.email.endswith("@usm.cl"):
            raise HTTPException(status_code=400, detail="Correo debe ser @usm.cl")

        reservas = db.query(Reserva).filter(Reserva.fecha == fecha).all()
        for r in reservas:
            if not (fin <= r.hora_inicio or inicio >= r.hora_fin):
                raise HTTPException(status_code=400, detail="Horario no disponible")

        nueva = Reserva(
            fecha=fecha,
            hora_inicio=inicio,
            hora_fin=fin,
            responsable=data.responsable,
            grupo=data.grupo,
            email=data.email
        )

        db.add(nueva)
        db.commit()

        return {"mensaje": "Reserva guardada correctamente"}

    except HTTPException as e:
        # Deja pasar los errores de validación tal cual
        print("Error en crear_reserva:", e.detail)
        raise e
    except Exception as e:
        # Solo captura errores inesperados
        print("Error inesperado en crear_reserva:", str(e))
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


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
