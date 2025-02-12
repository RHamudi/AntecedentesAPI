from contextlib import asynccontextmanager
import shutil
import os
from uuid import uuid4
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import and_
from task import process_file
from db.models.user import User, Task
from db.schemas import schemas
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from db.config.postgress import Base, engine, SessionLocal
import tempfile
import zipfile

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite qualquer origem
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

@app.post("/upload/{idUser}")
def upload_excel(idUser: int,file: UploadFile = File(...), db: Session = Depends(get_db)):
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
            process_file.delay(task_id, file.filename)
            new_task = Task(id = task_id, user= idUser, fileName = file.filename)
            db.add(new_task)
            db.commit()            
            db.refresh(new_task)
            return {"task_id": task_id, "message": "Arquivo enviado, processamento em andamento"}
        else:
            return {"error": "Falha ao salvar o arquivo"}
    except Exception as e:
        return {"error": f"Erro ao salvar o arquivo: {str(e)}"}
    
@app.get("/uploads/{id}/download")
async def download_certificates(id: str):
    base_directory = f"uploads/{id}"

    # Verifica se o diretório existe
    if not os.path.exists(base_directory) or not os.path.isdir(base_directory):
        return {"message": "Diretório não encontrado"}

    # Criando um arquivo ZIP temporário
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    zip_path = temp_zip.name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(base_directory):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, base_directory)  # Mantém a estrutura dentro do ZIP
                zipf.write(file_path, arcname)

    # Fecha o arquivo temporário
    temp_zip.close()

    return FileResponse(zip_path, media_type="application/zip", filename=f"{id}_arquivos.zip")

@app.get("/tasks/{id}")
def getTasks(id: str,db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.user == id).all()
    return tasks

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
    
    return {"message": "Usuario authenticado com sucesso","idUser": db_user.id}
