from fastapi import FastAPI
from database import SessionLocal, engine, Base
from models import Reserva
from datetime import date, time

app = FastAPI()

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
def crear_reserva(data: dict):
    db = next(get_db())

    inicio = time.fromisoformat(data["hora_inicio"])
    fin = time.fromisoformat(data["hora_fin"])
    fecha = date.fromisoformat(data["fecha"])

    # 🔒 Validar horario (08:00 - 18:00)
    if inicio < time(8, 0) or fin > time(18, 0):
        return {"error": "Horario fuera de rango (08:00 - 18:00)"}

    # 🔒 Validar duración (bloques de 2 a 8 horas)
    duracion = fin.hour - inicio.hour
    if duracion < 2 or duracion % 2 != 0 or duracion > 8:
        return {"error": "Duración inválida: solo bloques de 2 a 8 horas"}

    # 🔒 Validar correo institucional
    if not data["email"].endswith("@usm.cl"):
        return {"error": "Correo debe ser @usm.cl"}

    # 🔒 Validar conflicto de horario (CRÍTICO)
    reservas = db.query(Reserva).filter(Reserva.fecha == fecha).all()
    for r in reservas:
        if not (fin <= r.hora_inicio or inicio >= r.hora_fin):
            return {"error": "Conflicto de horario con otra reserva"}

    # ✅ Guardar reserva
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
def listar_reservas():
    db = next(get_db())
    return db.query(Reserva).all()