import os
from typing import List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.config import settings
from app.database import Base, engine, get_db
from app.models import Cancion, OrigenEntrada, Usuario
from app.schemas import (
    CancionDetalleResponse,
    CancionResumenResponse,
    CancionUpdate,
    TokenResponse,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
)

# Crea las tablas en PostgreSQL automáticamente si aún no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

# Permite que el frontend en React (otro puerto) pueda hablar con este backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 1. COMPROBACIÓN DE SALUD DEL SERVIDOR

@app.get("/api/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}



# 2. AUTENTICACIÓN Y PERFIL DE USUARIO

@app.post(
    "/api/auth/register",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Autenticación"],
)
def registrar_usuario(datos: UsuarioCreate, db: Session = Depends(get_db)):
    existe = (db.query(Usuario).filter(
            or_(
                Usuario.username == datos.username,
                Usuario.email == datos.email,
            )
        )
        .first()
    )
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario o el correo electrónico ya están registrados.",
        )

    nuevo_usuario = Usuario(
        username=datos.username,
        email=datos.email,
        password_hash=get_password_hash(datos.password),
        nombre=datos.nombre,
        apellidos=datos.apellidos,
        instrumento_preferido=datos.instrumento_preferido.value,
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@app.post("/api/auth/login", response_model=TokenResponse, tags=["Autenticación"])
def iniciar_sesion(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    usuario = (
        db.query(Usuario).filter(
            or_(
                Usuario.email == form_data.username,
                Usuario.username == form_data.username,
            )
        )
        .first()
    )
    if not usuario or not verify_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo/usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if usuario.estado_cuenta != "ACTIVA":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta de usuario no está activa.",
        )

    token = create_access_token(data={"sub": str(usuario.id)})
    return TokenResponse(access_token=token)


@app.get("/api/auth/me", response_model=UsuarioResponse, tags=["Perfil"])
def obtener_mi_perfil(usuario_actual: Usuario = Depends(get_current_user)):
    return usuario_actual


@app.put("/api/auth/me", response_model=UsuarioResponse, tags=["Perfil"])
def actualizar_mi_perfil(
    datos: UsuarioUpdate,
    usuario_actual: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if datos.nombre is not None:
        usuario_actual.nombre = datos.nombre
    if datos.apellidos is not None:
        usuario_actual.apellidos = datos.apellidos
    if datos.instrumento_preferido is not None:
        usuario_actual.instrumento_preferido = datos.instrumento_preferido.value

    db.commit()
    db.refresh(usuario_actual)
    return usuario_actual


# 3. BIBLIOTECA MUSICAL (CRUD DE CANCIONES)

@app.get(
    "/api/canciones",
    response_model=List[CancionResumenResponse],
    tags=["Biblioteca"],
)
def listar_canciones(
    busqueda: Optional[str] = Query(default=None, description="Filtrar por título"),
    origen_entrada: Optional[OrigenEntrada] = Query(
        default=None, description="Filtrar por AUDIO_AMT o IMAGE_OMR"
    ),
    usuario_actual: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    consulta = db.query(Cancion).filter(Cancion.user_id == usuario_actual.id)

    if busqueda:
        consulta = consulta.filter(Cancion.titulo.ilike(f"%{busqueda}%"))
    if origen_entrada:
        consulta = consulta.filter(Cancion.origen_entrada == origen_entrada.value)

    return consulta.order_by(Cancion.fecha_creacion.desc()).all()


@app.get(
    "/api/canciones/{song_id}",
    response_model=CancionDetalleResponse,
    tags=["Biblioteca"],
)
def obtener_detalle_cancion(
    song_id: UUID,
    usuario_actual: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cancion = (
        db.query(Cancion)
        .filter(Cancion.id == song_id, Cancion.user_id == usuario_actual.id)
        .first()
    )
    if not cancion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Canción no encontrada.",
        )
    return cancion


@app.patch(
    "/api/canciones/{song_id}",
    response_model=CancionResumenResponse,
    tags=["Biblioteca"],
)
def actualizar_cancion(
    song_id: UUID,
    datos: CancionUpdate,
    usuario_actual: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cancion = (
        db.query(Cancion)
        .filter(Cancion.id == song_id, Cancion.user_id == usuario_actual.id)
        .first()
    )
    if not cancion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Canción no encontrada.",
        )

    if datos.titulo is not None:
        cancion.titulo = datos.titulo
    if datos.autor is not None:
        cancion.autor = datos.autor

    db.commit()
    db.refresh(cancion)
    return cancion


@app.delete(
    "/api/canciones/{song_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Biblioteca"],
)
def eliminar_cancion(
    song_id: UUID,
    usuario_actual: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cancion = (
        db.query(Cancion)
        .filter(Cancion.id == song_id, Cancion.user_id == usuario_actual.id)
        .first()
    )
    if not cancion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Canción no encontrada.",
        )

    rutas_a_borrar = [
        cancion.ruta_archivo_original,
        cancion.ruta_midi,
        cancion.ruta_musicxml,
    ]

    db.delete(cancion)
    db.commit()

    for ruta in rutas_a_borrar:
        if ruta and os.path.exists(ruta):
            os.remove(ruta)

    return None