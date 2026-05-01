from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

# IMPORTANTE: usar tu configuración existente
from backend.database import get_db, engine, Base
from backend.models import Reserva

app = FastAPI()

# -------------------------------
# CORS
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# CREAR TABLAS (PostgreSQL)
# -------------------------------
Base.metadata.create_all(bind=engine)

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
    from datetime import datetime, time

    # Validación email
    if not reserva.get("email", "").endswith("@usm.cl"):
        return {"mensaje": "Email inválido"}

    # Parseo
    fecha = datetime.strptime(reserva["fecha"], "%Y-%m-%d").date()
    hora_inicio = datetime.strptime(reserva["hora_inicio"], "%H:%M").time()
    hora_fin = datetime.strptime(reserva["hora_fin"], "%H:%M").time()

    # Validaciones
    if fecha < datetime.today().date():
        return {"mensaje": "Fecha pasada no permitida"}

    if fecha.weekday() >= 5:
        return {"mensaje": "Solo lunes a viernes"}

    if hora_inicio < time(8, 0) or hora_fin > time(18, 0):
        return {"mensaje": "Horario 08:00 - 18:00"}

    if hora_inicio.minute != 0 or hora_fin.minute != 0:
        return {"mensaje": "Horas exactas"}

    if hora_inicio.hour % 2 != 0 or hora_fin.hour % 2 != 0:
        return {"mensaje": "Horas pares"}

    duracion = (
        datetime.combine(fecha, hora_fin)
        - datetime.combine(fecha, hora_inicio)
    ).seconds / 3600

    if duracion < 2:
        return {"mensaje": "Mínimo 2 horas"}

    reservas_grupo = db.query(Reserva).filter(
        Reserva.grupo == reserva["grupo"],
        Reserva.fecha == reserva["fecha"]
    ).all()

    horas_existentes = sum(
        (
            datetime.combine(fecha, r.hora_fin)
            - datetime.combine(fecha, r.hora_inicio)
        ).seconds / 3600
        for r in reservas_grupo
    )

    if horas_existentes + duracion > 4:
        return {"mensaje": "Máximo 4 horas por grupo"}
    

    # 🔍 DETECTAR SOLAPAMIENTO (SIN BLOQUEAR)
    reservas_existentes = db.query(Reserva).filter(
        Reserva.fecha == reserva["fecha"]
        ).all()

    for r in reservas_existentes:

        inicio_existente = r.hora_inicio
        fin_existente = r.hora_fin

        inicio_nuevo = reserva["hora_inicio"]
        fin_nuevo = reserva["hora_fin"]

        print("DEBUG:", inicio_existente, fin_existente, "|", inicio_nuevo, fin_nuevo)


    
    # Guardar en DB REAL (PostgreSQL)
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

# -------------------------------
# RUN LOCAL
# ------------------------------- TEST 20260430
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)