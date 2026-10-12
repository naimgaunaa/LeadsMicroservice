import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./leads.db")

# SQLite requiere este argumento cuando se usa con threads de FastAPI/dependencias.
# Para PostgreSQL/MySQL en la nube no se aplica.
engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    # Pool mínimo para una sola instancia. El pooler de sesión de Supabase limita
    # a 15 clientes, así que se usa un pool chico sin overflow y con reciclado.
    engine_args["pool_size"] = 3
    engine_args["max_overflow"] = 0
    engine_args["pool_recycle"] = 180
    engine_args["pool_pre_ping"] = True
    engine_args["pool_timeout"] = 10

engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

