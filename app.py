import shutil
from typing import Union
import os
from uuid import uuid4
from fastapi import FastAPI, UploadFile, File
from task import process_file


app = FastAPI()
UPLOAD_FOLDER = "uploads"

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