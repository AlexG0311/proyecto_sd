#!/usr/bin/env python3
import pika
import time

credentials = pika.PlainCredentials('admin', 'admin123')

def callback(ch, method, properties, body):
    mensaje = body.decode()
    print(f" [✓] Recibido: {mensaje}")
    print(f" [✉] Enviando correo para: {mensaje}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, '/', credentials))
channel = connection.channel()
channel.queue_declare(queue='campaigns_queue', durable=True)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='campaigns_queue', on_message_callback=callback)

print(" [*] Esperando mensajes. Presiona Ctrl+C para salir")
try:
    channel.start_consuming()
except KeyboardInterrupt:
    print(" [*] Deteniendo consumidor...")
    connection.close()
