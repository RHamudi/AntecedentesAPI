#!/bin/bash

# Inicia o Uvicorn para rodar o FastAPI
uvicorn app:app --host 0.0.0.0 --port $PORT &

# Inicia o Celery worker
celery -A task worker -l info --pool=solo &

# Inicia o Celery Flower para monitoramento
celery -A task flower --address=127.0.0.6 --port=5566 &

# Aguarda processos para evitar que o script finalize
wait
