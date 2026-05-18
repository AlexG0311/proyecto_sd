import pika
import os
import time

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'admin')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'admin123')

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)

def callback(ch, method, properties, body):
    mensaje = body.decode()
    print(f" [✓] Recibido: {mensaje}")
    print(f" [✉] Enviando correo para: {mensaje}")
    # Aquí iría la lógica real de envío de correo (smtplib)
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Esperar a que RabbitMQ esté listo
time.sleep(5)

connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST, RABBITMQ_PORT, '/', credentials))
channel = connection.channel()
channel.queue_declare(queue='campaigns_queue', durable=True)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='campaigns_queue', on_message_callback=callback)

print(" [*] Esperando mensajes desde RabbitMQ...")
try:
    channel.start_consuming()
except KeyboardInterrupt:
    print(" [*] Deteniendo consumidor...")
    connection.close()
