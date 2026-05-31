import pika
import pymysql
import json
import time
import os
import uuid
from datetime import datetime

# Configuración
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'admin')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'admin123')

DB_HOST = os.getenv('DB_HOST', 'proxysql')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'suitecrm_user')
DB_PASS = os.getenv('DB_PASS', 'secret')
DB_NAME = os.getenv('DB_NAME', 'suitecrm_a')

QUEUE = 'email_campaigns'


def get_db():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )


def get_rabbit():
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
    return connection, channel


def get_pending_campaigns(db):
    """Obtiene campañas activas con su email_marketing y template"""
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT 
                c.id        AS campaign_id,
                c.name      AS campaign_name,
                c.start_date,
                em.id       AS marketing_id,
                em.from_name,
                em.from_addr,
                em.template_id,
                et.subject,
                et.body_html,
                et.body
            FROM campaigns c
            JOIN email_marketing em ON em.campaign_id = c.id AND em.deleted = 0
            JOIN email_templates et ON et.id = em.template_id AND et.deleted = 0
            WHERE c.status = 'Active'
              AND c.deleted = 0
              AND c.campaign_type = 'Email'
        """)
        return cursor.fetchall()


def get_prospects(db, marketing_id, campaign_id):
    """Obtiene destinatarios de la campaña que no han recibido el correo"""
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT
                p.id        AS prospect_id,
                p.first_name,
                p.last_name,
                ea.email_address
            FROM email_marketing_prospect_lists empl
            JOIN prospect_lists pl ON pl.id = empl.prospect_list_id AND pl.deleted = 0
            JOIN prospect_lists_prospects plp ON plp.prospect_list_id = pl.id AND plp.deleted = 0
            JOIN prospects p ON p.id = plp.related_id AND p.deleted = 0
            JOIN email_addr_bean_rel eabr ON eabr.bean_id = p.id 
                AND eabr.bean_module = 'Prospects' 
                AND eabr.deleted = 0
            JOIN email_addresses ea ON ea.id = eabr.email_address_id AND ea.deleted = 0
            WHERE empl.prospect_list_id IN (
                SELECT prospect_list_id 
                FROM email_marketing_prospect_lists 
                WHERE email_marketing_id = %s
            )
            AND p.id NOT IN (
                SELECT target_id FROM campaign_log
                WHERE campaign_id = %s
                  AND activity_type = 'sent'
                  AND deleted = 0
            )
        """, (marketing_id, campaign_id))
        return cursor.fetchall()


def register_sent(db, campaign_id, marketing_id, prospect_id, list_id):
    """Registra en campaign_log que el correo fue encolado"""
    with db.cursor() as cursor:
        cursor.execute("""
            INSERT INTO campaign_log 
                (id, campaign_id, marketing_id, target_id, target_type,
                 activity_type, activity_date, deleted, date_modified)
            VALUES (%s, %s, %s, %s, 'Prospects', 'sent', %s, 0, %s)
        """, (
            str(uuid.uuid4()),
            campaign_id,
            marketing_id,
            prospect_id,
            datetime.now(),
            datetime.now()
        ))
    db.commit()


def main():
    print(">>> Productor iniciado")

    while True:
        try:
            db = get_db()
            connection, channel = get_rabbit()

            campaigns = get_pending_campaigns(db)
            print(f">>> Campañas activas encontradas: {len(campaigns)}")

            for campaign in campaigns:
                prospects = get_prospects(
                    db,
                    campaign['marketing_id'],
                    campaign['campaign_id']
                )
                print(f">>> Campaña '{campaign['campaign_name']}': {len(prospects)} destinatarios pendientes")

                for prospect in prospects:
                    mensaje = {
                        'campaign_id':   campaign['campaign_id'],
                        'campaign_name': campaign['campaign_name'],
                        'marketing_id':  campaign['marketing_id'],
                        'from_name':     campaign['from_name'],
                        'from_addr':     campaign['from_addr'],
                        'subject':       campaign['subject'],
                        'body_html':     campaign['body_html'],
                        'body':          campaign['body'],
                        'to_name':       f"{prospect['first_name']} {prospect['last_name']}",
                        'to_email':      prospect['email_address'],
                        'prospect_id':   prospect['prospect_id'],
                    }

                    channel.basic_publish(
                        exchange='',
                        routing_key=QUEUE,
                        body=json.dumps(mensaje),
                        properties=pika.BasicProperties(delivery_mode=2)
                    )

                    register_sent(
                        db,
                        campaign['campaign_id'],
                        campaign['marketing_id'],
                        prospect['prospect_id'],
                        None
                    )

                    print(f"    → Encolado: {prospect['email_address']}")

            connection.close()
            db.close()

        except Exception as e:
            print(f">>> ERROR: {e}")

        print(">>> Esperando 60 segundos...")
        time.sleep(60)


if __name__ == '__main__':
    main()