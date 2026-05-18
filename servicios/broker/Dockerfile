FROM python:3.9-slim

WORKDIR /app

# Copiar requirements.txt desde la ubicación actual de los scripts
COPY scripts/rabbitmq/requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar los scripts
COPY scripts/rabbitmq/ .

# Por defecto ejecuta el consumidor (se puede sobrescribir con command en docker-compose)
CMD ["python", "-u", "consumidor.py"]
