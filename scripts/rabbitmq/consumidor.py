import pika
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'admin')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'admin123')

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')

QUEUE = 'email_campaigns'


def send_email(mensaje):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = mensaje['subject']
    msg['From']    = f"{mensaje['from_name']} <{mensaje['from_addr']}>"
    msg['To']      = mensaje['to_email']

    if mensaje.get('body'):
        msg.attach(MIMEText(mensaje['body'], 'plain'))
    if mensaje.get('body_html'):
        msg.attach(MIMEText(mensaje['body_html'], 'html'))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(mensaje['from_addr'], mensaje['to_email'], msg.as_string())


def callback(ch, method, properties, body):
    mensaje = json.loads(body)
    print(f">>> Procesando: {mensaje['to_email']} | Campaña: {mensaje['campaign_name']}")

    try:
        send_email(mensaje)
        print(f"    ✓ Enviado a {mensaje['to_email']}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"    ✗ Error enviando a {mensaje['to_email']}: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def main():
    print(">>> Consumidor iniciado")

    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE, on_message_callback=callback)

    print(">>> Esperando mensajes en la cola...")
    channel.start_consuming()


if __name__ == '__main__':
    main()