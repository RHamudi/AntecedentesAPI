import subprocess
from celery import Celery

app = Celery('task', broker="amqp://localhost")


@app.task
def process_file(file_id):
    try:
        subprocess.run(["python", f'script/final.py', file_id], capture_output=True, text=True)
        
    except Exception as e:

        raise e