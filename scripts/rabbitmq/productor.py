import pika
import os
import time
import mysql.connector

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'admin')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'admin123')

DB_HOST = os.getenv('DB_HOST', 'proxysql')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'suitecrm_user')
DB_PASS = os.getenv('DB_PASS', 'secret')
DB_NAME = os.getenv('DB_NAME', 'suitecrm_a')

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)

# Esperar a que RabbitMQ y BD estén listos
time.sleep(10)

connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST, RABBITMQ_PORT, '/', credentials))
channel = connection.channel()
channel.queue_declare(queue='campaigns_queue', durable=True)

# Conectar a la base de datos
db = mysql.connector.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME
)
cursor = db.cursor()

while True:
    try:
        # Buscar campañas no enviadas (ajusta el nombre real de la tabla y columna)
        cursor.execute("SELECT id, name, email, message FROM campaigns WHERE sent = 0 LIMIT 10")
        campaigns = cursor.fetchall()
        
        for (id, name, email, message) in campaigns:
            mensaje = f"Campaña: {name} | Email: {email} | Mensaje: {message}"
            channel.basic_publish(
                exchange='',
                routing_key='campaigns_queue',
                body=mensaje,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            # Marcar como enviada
            cursor.execute("UPDATE campaigns SET sent = 1 WHERE id = %s", (id,))
            db.commit()
            print(f" [x] Publicada campaña {id}")
        
    except Exception as e:
        print(f" [!] Error: {e}")
    
    time.sleep(60)  # Esperar 60 segundos antes de la siguiente consulta
