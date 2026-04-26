from sqlalchemy import Column, Integer, String, Date, Time
from backend.database import Base

class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    responsable = Column(String, nullable=False)
    grupo = Column(String, nullable=False)
    email = Column(String, nullable=False)