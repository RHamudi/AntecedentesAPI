import subprocess
from seleniumbase import Driver
from celery import Celery
import subprocess
from sqlalchemy.orm import Session
from fastapi import Depends
import os

from db.config.postgress import SessionLocal
from db.models.user import Task

app = Celery(
    'tasks',
    broker='redis://default:oVmpqjGJuf92rEgPIOsY8E992pquziwv@redis-14764.c9.us-east-1-4.ec2.redns.redis-cloud.com:14764/0',
    backend='redis://default:oVmpqjGJuf92rEgPIOsY8E992pquziwv@redis-14764.c9.us-east-1-4.ec2.redns.redis-cloud.com:14764/0'
)

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