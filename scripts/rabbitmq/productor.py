#!/usr/bin/env python3
import pika
import sys

credentials = pika.PlainCredentials('admin', 'admin123')
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, '/', credentials))
channel = connection.channel()
channel.queue_declare(queue='campaigns_queue', durable=True)

if len(sys.argv) > 1:
    message = ' '.join(sys.argv[1:])
else:
    message = "Campaña de prueba"

channel.basic_publish(
    exchange='',
    routing_key='campaigns_queue',
    body=message,
    properties=pika.BasicProperties(delivery_mode=2)
)

print(f" [x] Enviado: {message}")
connection.close()
