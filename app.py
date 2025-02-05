from contextlib import asynccontextmanager
import shutil
import os
from uuid import uuid4
from fastapi import Depends, FastAPI, UploadFile, File
from task import process_file
from db.models.user import User
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
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    process_file.delay(task_id)

    return {"task_id": task_id, "message": "Arquivo enviado, processamento em andamento"}

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

# @app.get("/executar/{id}")
# def read_root(id: str):
#     try:
#         resultado = subprocess.run(["python", f'script/final.py', id], capture_output=True, text=True)
#         return {"saida": resultado.stdout, "erro": resultado.stderr}
#     except Exception as e:
#         return {"erro": str(e)}


# @celery_app.task(name='app.process_file')
# def process_file(file_id):
#     try:
#         subprocess.run(["python", f'script/final.py', file_id], capture_output=True, text=True)

#         # redis_client.set(f"task:{file_id}", "concluído")

#     except Exception as e:
#         # redis_client.set(f"task:{file_id}", "Erro")
#         raise e