from contextlib import asynccontextmanager
import shutil
import os
from uuid import uuid4
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from sqlalchemy import and_
from task import process_file
from db.models.user import User
from db.schemas import schemas
from sqlalchemy.orm import Session
from db.config.postgress import Base, engine, SessionLocal

UPLOAD_FOLDER = "uploads"

Base.metadata.create_all(bind=engine)
# Dependência para obter a sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

@app.post("/upload/")
def upload_excel(file: UploadFile = File(...)):
    task_id = str(uuid4())  # Gera um ID único para a tarefa
    task_folder = os.path.join(UPLOAD_FOLDER, task_id)
    os.makedirs(task_folder, exist_ok=True)  # Cria uma pasta para a tarefa

    file_path = os.path.join(task_folder, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Verifica se o arquivo realmente foi salvo e não está vazio
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            # Chama o processamento assíncrono
            process_file.delay(task_id)
            return {"task_id": task_id, "message": "Arquivo enviado, processamento em andamento"}
        else:
            return {"error": "Falha ao salvar o arquivo"}
    except Exception as e:
        return {"error": f"Erro ao salvar o arquivo: {str(e)}"}

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@app.post("/users")
def create_user(request: schemas.UserCreate, db: Session = Depends(get_db)):
    # Verifica se o e-mail já está cadastrado
    db_user = db.query(User).filter(User.email == request.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    
    # Cria o novo usuário
    new_user = User(name=request.name, email=request.email, senha=request.senha)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.post("/login")
def authenticate(request: schemas.LoginUser, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(and_(User.email == request.email, User.senha == request.senha)).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="E-mail ou senha invalida")
    
    return {"message": "Usuario authenticado com sucesso"}

@app.get("/uploads/{id}/certificados")
async def count_certificates(id: str):
    directory = f"uploads/{id}/certificados"
    
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return {"message": "Diretório não encontrado", "count": 0}

    file_count = len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
    
    return {"message": "Contagem realizada com sucesso", "count": file_count}