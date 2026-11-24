import enum
import uuid
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Float,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from app.database import Base


class InstrumentoPreferido(str, enum.Enum):
    PIANO = "piano"
    GUITARRA = "guitarra"


class OrigenEntrada(str, enum.Enum):
    AUDIO_AMT = "AUDIO_AMT"
    IMAGE_OMR = "IMAGE_OMR"


class FormatoOriginal(str, enum.Enum):
    MP3 = "MP3"
    WAV = "WAV"
    PDF = "PDF"
    PNG = "PNG"
    JPG = "JPG"


class TipoPipeline(str, enum.Enum):
    AMT_BASIC_PITCH = "AMT_BASIC_PITCH"
    OMR_AUDIVERIS = "OMR_AUDIVERIS"


class EstadoTarea(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    PROCESANDO = "PROCESANDO"
    ANALIZANDO_ARMONIA = "ANALIZANDO_ARMONIA"
    COMPLETADO = "COMPLETADO"
    ERROR = "ERROR"


class ModoPractica(str, enum.Enum):
    PARTITURA = "PARTITURA"
    FALLING_NOTES = "FALLING_NOTES"
    ACORDES = "ACORDES"
    MIDI_EVALUACION = "MIDI_EVALUACION"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    instrumento_preferido = Column(String(20), default=InstrumentoPreferido.PIANO.value, nullable=False)
    estado_cuenta = Column(String(20), default="ACTIVA", server_default="ACTIVA", nullable=False)
    fecha_registro = Column(DateTime, server_default=func.now(), nullable=False)

    canciones = relationship("Cancion", back_populates="usuario", cascade="all, delete-orphan")
    progresos = relationship("ProgresoTutorial", back_populates="usuario", cascade="all, delete-orphan")


class Cancion(Base):
    __tablename__ = "canciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    titulo = Column(String(200), nullable=False)
    autor = Column(String(150), nullable=True)
    origen_entrada = Column(String(20), index=True, nullable=False)
    formato_original = Column(String(10), nullable=False)
    duracion_segundos = Column(Float, nullable=True)
    tempo_bpm = Column(Float, default=120.0, server_default="120.0", nullable=True)
    tonalidad_original = Column(String(20), nullable=True)
    compas = Column(String(10), default="4/4", server_default="4/4", nullable=True)

    ruta_archivo_original = Column(String(500), nullable=False)
    ruta_musicxml = Column(String(500), nullable=True)
    ruta_midi = Column(String(500), nullable=True)

    estructura_musical = Column(JSONB, nullable=True)
    analisis_armonico = Column(JSONB, nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)

    usuario = relationship("Usuario", back_populates="canciones")
    tareas = relationship("TareaTranscripcion", back_populates="cancion", cascade="all, delete-orphan")
    progresos = relationship("ProgresoTutorial", back_populates="cancion", cascade="all, delete-orphan")

    __table_args__ = (
        Index(
            "idx_canciones_estructura_musical_gin",
            "estructura_musical",
            postgresql_using="gin",
        ),
        Index(
            "idx_canciones_analisis_armonico_gin",
            "analisis_armonico",
            postgresql_using="gin",
        ),
    )


class TareaTranscripcion(Base):
    __tablename__ = "tareas_transcripcion"

    task_id = Column(String(100), primary_key=True)
    song_id = Column(
        UUID(as_uuid=True),
        ForeignKey("canciones.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    tipo_pipeline = Column(String(30), nullable=False)
    estado = Column(
        String(30),
        index=True,
        default=EstadoTarea.PENDIENTE.value,
        server_default="PENDIENTE",
        nullable=False,
    )
    progreso_porcentaje = Column(Integer, default=0, server_default="0", nullable=False)
    mensaje_diagnostico = Column(Text, nullable=True)
    fecha_inicio = Column(DateTime, server_default=func.now(), nullable=False)
    fecha_fin = Column(DateTime, nullable=True)

    cancion = relationship("Cancion", back_populates="tareas")


class ProgresoTutorial(Base):
    __tablename__ = "progreso_tutorial"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    song_id = Column(
        UUID(as_uuid=True),
        ForeignKey("canciones.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    fecha_sesion = Column(DateTime, server_default=func.now(), nullable=False)
    modo_practica = Column(String(30), index=True, nullable=False)
    tempo_practica = Column(Float, nullable=False)
    porcentaje_precision = Column(Float, nullable=False)
    repeticiones_completadas = Column(Integer, default=1, server_default="1", nullable=False)

    usuario = relationship("Usuario", back_populates="progresos")
    cancion = relationship("Cancion", back_populates="progresos")