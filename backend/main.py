from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Base
from backend.models import Reserva
from datetime import date, time, datetime
from pydantic import BaseModel
import uvicorn
import os

# Importa el frontend Dash
from frontend.app import app as dash_app

# Crear instancia FastAPI
app = FastAPI()

# Middleware CORS
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

# Endpoints básicos
@app.get("/")
def root():
    return {"mensaje": "Sistema activo"}

@app.get("/api/status")
def status():
    return {"mensaje": "Sistema funcionando con base de datos"}

# Monta el frontend Dash en /dash
app.mount("/dash", WSGIMiddleware(dash_app))

# Crear reserva
@app.post("/reservas")
def crear_reserva(data: ReservaInput, db: Session = Depends(get_db)):
    try:
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

        # Validar disponibilidad
        reservas = db.query(Reserva).filter(Reserva.fecha == fecha).all()
        for r in reservas:
            if not (fin <= r.hora_inicio or inicio >= r.hora_fin):
                raise HTTPException(status_code=400, detail="Horario no disponible")

        # Crear nueva reserva
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
        raise e
    except Exception as e:
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

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
import os

app = FastAPI()

@app.get("/")
def root():
    return {"mensaje": "Sistema activo"}

@app.get("/index.html")
def get_index():
    # Ruta absoluta desde backend → subir un nivel → frontend_web
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "..", "frontend_web", "index.html")
    return FileResponse(file_path)

@app.get("/api/status")
def status():
    return JSONResponse(content={"status": "ok"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)





