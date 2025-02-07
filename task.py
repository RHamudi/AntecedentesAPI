import os
import subprocess
from seleniumbase import Driver
import time
from celery import Celery
from datetime import datetime
import subprocess
from selenium.webdriver.common.by import By
from seleniumbase.common.exceptions import NoSuchElementException
import argparse
import pandas as pd
import os

app = Celery('task', 
            broker="rediss://red-cuik5j3qf0us73dqd4eg:7Dblq1wB3OB6EQ28I1kXsKcZ1N8dxYuy@oregon-redis.render.com:6379",
            ssl=True,  # Habilita SSL
            ssl_cert_reqs=None )

@app.task
def process_file(file_id):
    try:
        subprocess.run(["python", f'script/final.py', file_id], capture_output=True, text=True)
    except Exception as e:
        raise "erro ao executar"