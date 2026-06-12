import pika
import json
import os
import smtplib
import time
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


def get_rabbit():
    while True:
        try:
            credentials = pika.PlainCredentials(
                RABBITMQ_USER,
                RABBITMQ_PASS
            )

            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )

            channel = connection.channel()
            channel.queue_declare(queue=QUEUE, durable=True)

            print(">>> RabbitMQ conectado")

            return connection, channel

        except Exception as e:
            print(f">>> RabbitMQ no disponible: {e}")
            print(">>> Reintentando en 5 segundos...")
            time.sleep(5)


def send_email(mensaje):

    msg = MIMEMultipart('alternative')

    msg['Subject'] = mensaje['subject']
    msg['From'] = f"{mensaje['from_name']} <{mensaje['from_addr']}>"
    msg['To'] = mensaje['to_email']

    if mensaje.get('body'):
        msg.attach(MIMEText(mensaje['body'], 'plain'))

    if mensaje.get('body_html'):
        msg.attach(MIMEText(mensaje['body_html'], 'html'))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)

        server.sendmail(
            SMTP_USER,
            mensaje['to_email'],
            msg.as_string()
        )


def callback(ch, method, properties, body):

    mensaje = json.loads(body)

    print(
        f">>> Procesando: "
        f"{mensaje['to_email']} | "
        f"Campaña: {mensaje['campaign_name']}"
    )

    try:

        send_email(mensaje)

        print(
            f"    ✓ Correo enviado a "
            f"{mensaje['to_email']}"
        )

        ch.basic_ack(
            delivery_tag=method.delivery_tag
        )

    except Exception as e:

        print(
            f"    ✗ Error enviando a "
            f"{mensaje['to_email']}: {e}"
        )

        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True
        )


def main():

    print(">>> Consumidor iniciado")

    connection, channel = get_rabbit()

    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=QUEUE,
        on_message_callback=callback
    )

    print(">>> Esperando mensajes...")

    channel.start_consuming()


if __name__ == '__main__':
    main()