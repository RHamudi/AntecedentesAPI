import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuração do banco de dados
DATABASE_URL = "postgresql://myuser:0JULlN3mKYtNkzbhOOxRouLkvgqwdN9i@dpg-cuik6bl6l47c73ag8f6g-a.oregon-postgres.render.com/mydatabase_olwi"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

