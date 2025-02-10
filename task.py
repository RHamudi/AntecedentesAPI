import subprocess
from seleniumbase import Driver
from celery import Celery
import subprocess
from sqlalchemy.orm import Session
from fastapi import Depends
import os

from db.config.postgress import SessionLocal
from db.models.user import Task

app = Celery('task', 
            broker="rediss://red-cuik5j3qf0us73dqd4eg:7Dblq1wB3OB6EQ28I1kXsKcZ1N8dxYuy@oregon-redis.render.com:6379",
            ssl=True,  # Habilita SSL
            ssl_cert_reqs=None )

@app.task
def process_file(file_id, file_name):
    db: Session = SessionLocal()  
    try:
        subprocess.run(["python", f'script/final.py', file_id, file_name], capture_output=True, text=True)
        db_task = db.query(Task).filter(Task.id == file_id).first()
        if db_task:
            db_task.status = "Concluido"
            db.commit()  # Confirma a atualização no banco
            db.refresh(db_task)
    except Exception as e:
        raise "erro ao executar"
    finally:
        db.close()