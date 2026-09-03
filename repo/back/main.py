import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
import models
from routes import usuarios, perfil, residentes, propiedades, finanzas, finanzas_copropiedades, mantenimiento, documentos, reportes, configuración, eventos

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Multi-Administrador API")

_origenes_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
ALLOWED_ORIGINS = [o.strip() for o in _origenes_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(usuarios.router)
app.include_router(perfil.router)
app.include_router(residentes.router)
app.include_router(propiedades.router)
app.include_router(finanzas.router)
app.include_router(finanzas_copropiedades.router)
app.include_router(mantenimiento.router)
app.include_router(documentos.router)
app.include_router(reportes.router)
app.include_router(configuración.router)
app.include_router(eventos.router)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home():
    return {"mensaje": "Backend funcionando con PostgreSQL"}
