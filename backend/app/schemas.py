from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models import InstrumentoPreferido, ModoPractica



# 1. ESQUEMAS DE USUARIO Y AUTENTICACIÓN
# ... -> (Campo obligatorio)

class UsuarioCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    nombre: str = Field(..., min_length=1, max_length=100)
    apellidos: str = Field(..., min_length=1, max_length=100)
    instrumento_preferido: InstrumentoPreferido = InstrumentoPreferido.PIANO
    password: str = Field(..., min_length=6, max_length=72)
    confirm_password: str = Field(..., min_length=6, max_length=72)

    @model_validator(mode="after")
    def comprobar_contrasenas(self) -> "UsuarioCreate":
        if self.password != self.confirm_password:
            raise ValueError("Las contraseñas no coinciden.")
        return self


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    apellidos: Optional[str] = Field(None, min_length=1, max_length=100)
    instrumento_preferido: Optional[InstrumentoPreferido] = None


class UsuarioResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    nombre: str
    apellidos: str
    instrumento_preferido: str
    estado_cuenta: str
    fecha_registro: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# 2. ESQUEMAS DE TAREAS ASÍNCRONAS (CELERY)

class TareaTranscripcionResponse(BaseModel):
    task_id: str
    song_id: UUID
    tipo_pipeline: str
    estado: str
    progreso_porcentaje: int
    mensaje_diagnostico: Optional[str] = None
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# 3. ESQUEMAS DE CANCIONES (BIBLIOTECA Y VISOR)


class CancionUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=200)
    autor: Optional[str] = Field(None, max_length=150)


class CancionResumenResponse(BaseModel):
    id: UUID
    user_id: UUID
    titulo: str
    autor: Optional[str] = None
    origen_entrada: str
    formato_original: str
    duracion_segundos: Optional[float] = None
    tempo_bpm: Optional[float] = None
    tonalidad_original: Optional[str] = None
    compas: Optional[str] = None
    fecha_creacion: datetime
    tareas: List[TareaTranscripcionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CancionDetalleResponse(CancionResumenResponse):
    ruta_musicxml: Optional[str] = None
    ruta_midi: Optional[str] = None
    estructura_musical: Optional[Dict[str, Any]] = None
    analisis_armonico: Optional[Dict[str, Any]] = None


# 4. ESQUEMAS DE PROGRESO DE PRÁCTICA (MIDI)

class ProgresoCreate(BaseModel):
    modo_practica: ModoPractica
    tempo_practica: float = Field(..., gt=0)
    porcentaje_precision: float = Field(..., ge=0.0, le=100.0)
    repeticiones_completadas: int = Field(default=1, ge=1)


class ProgresoResponse(BaseModel):
    id: UUID
    user_id: UUID
    song_id: UUID
    fecha_sesion: datetime
    modo_practica: str
    tempo_practica: float
    porcentaje_precision: float
    repeticiones_completadas: int

    model_config = ConfigDict(from_attributes=True)