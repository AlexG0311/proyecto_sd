import pika
import pymysql
import json
import time
import os
import uuid
from datetime import datetime

# ==========================
# CONFIGURACIÓN
# ==========================

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'admin')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'admin123')

DB_HOST = os.getenv('DB_HOST', 'db_haproxy')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'suitecrm_user')
DB_PASS = os.getenv('DB_PASS', 'secret')
DB_NAME = os.getenv('DB_NAME', 'suitecrm_a')

QUEUE = 'email_campaigns'

# ==========================
# CONEXIONES GLOBALES
# ==========================

db_conn = None
rabbit_conn = None
rabbit_channel = None


# ==========================
# MYSQL
# ==========================

def get_db():
    global db_conn

    try:
        if db_conn is not None and db_conn.open:
            db_conn.ping(reconnect=True)
            return db_conn
    except:
        db_conn = None

    while True:
        try:
            db_conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
                connect_timeout=30,
                read_timeout=60,
                write_timeout=60
            )

            print(">>> DB conectada")
            return db_conn

        except Exception as e:
            print(f">>> Error DB: {e}")
            print(">>> Reintentando en 5 segundos...")
            time.sleep(5)


# ==========================
# RABBITMQ
# ==========================

def get_rabbit():
    global rabbit_conn, rabbit_channel

    try:
        if rabbit_conn is not None and rabbit_conn.is_open:
            return rabbit_conn, rabbit_channel
    except:
        pass

    while True:
        try:
            credentials = pika.PlainCredentials(
                RABBITMQ_USER,
                RABBITMQ_PASS
            )

            rabbit_conn = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=RABBITMQ_HOST,
                    port=RABBITMQ_PORT,
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )

            rabbit_channel = rabbit_conn.channel()

            rabbit_channel.queue_declare(
                queue=QUEUE,
                durable=True
            )

            print(">>> RabbitMQ conectado")

            return rabbit_conn, rabbit_channel

        except Exception as e:
            print(f">>> Error RabbitMQ: {e}")
            print(">>> Reintentando en 5 segundos...")
            time.sleep(5)


# ==========================
# CAMPAÑAS ACTIVAS
# ==========================

def get_pending_campaigns(db):

    with db.cursor() as cursor:

        cursor.execute("""
            SELECT
                c.id AS campaign_id,
                c.name AS campaign_name,
                c.start_date,

                em.id AS marketing_id,
                em.from_name,
                em.from_addr,
                em.template_id,

                et.subject,
                et.body_html,
                et.body

            FROM campaigns c

            JOIN email_marketing em
                ON em.campaign_id = c.id
                AND em.deleted = 0

            JOIN email_templates et
                ON et.id = em.template_id
                AND et.deleted = 0

            WHERE c.status = 'Active'
              AND c.deleted = 0
              AND c.campaign_type = 'Email'
        """)

        return cursor.fetchall()


# ==========================
# DESTINATARIOS
# ==========================

def get_prospects(db, campaign_id):

    with db.cursor() as cursor:

        cursor.execute("""
            SELECT DISTINCT
                p.id AS prospect_id,
                p.first_name,
                p.last_name,
                ea.email_address

            FROM prospect_list_campaigns plc

            JOIN prospect_lists pl
                ON pl.id = plc.prospect_list_id
                AND pl.deleted = 0

            JOIN prospect_lists_prospects plp
                ON plp.prospect_list_id = pl.id
                AND plp.deleted = 0

            JOIN prospects p
                ON p.id = plp.related_id
                AND p.deleted = 0

            JOIN email_addr_bean_rel eabr
                ON eabr.bean_id = p.id
                AND eabr.bean_module = 'Prospects'
                AND eabr.deleted = 0

            JOIN email_addresses ea
                ON ea.id = eabr.email_address_id
                AND ea.deleted = 0

            WHERE plc.campaign_id = %s
              AND plc.deleted = 0

              AND p.id NOT IN (
                    SELECT target_id
                    FROM campaign_log
                    WHERE campaign_id = %s
                      AND activity_type = 'sent'
                      AND deleted = 0
              )
        """, (campaign_id, campaign_id))

        return cursor.fetchall()


# ==========================
# REGISTRAR ENVÍO
# ==========================

def register_sent(
    db,
    campaign_id,
    marketing_id,
    prospect_id
):

    with db.cursor() as cursor:

        cursor.execute("""
            INSERT INTO campaign_log
            (
                id,
                campaign_id,
                marketing_id,
                target_id,
                target_type,
                activity_type,
                activity_date,
                deleted,
                date_modified
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                'Prospects',
                'sent',
                %s,
                0,
                %s
            )
        """, (
            str(uuid.uuid4()),
            campaign_id,
            marketing_id,
            prospect_id,
            datetime.now(),
            datetime.now()
        ))

    db.commit()


# ==========================
# MAIN
# ==========================

def main():

    global db_conn
    global rabbit_conn
    global rabbit_channel

    print(">>> Productor iniciado")

    while True:

        try:

            db = get_db()
            _, channel = get_rabbit()

            campaigns = get_pending_campaigns(db)

            print(f">>> Campañas activas encontradas: {len(campaigns)}")

            for campaign in campaigns:

                prospects = get_prospects(
                    db,
                    campaign['campaign_id']
                )

                print(
                    f"\nDEBUG Campaign ID: "
                    f"{campaign['campaign_id']}"
                )

                print(
                    f"DEBUG Prospects: "
                    f"{prospects}"
                )

                print(
                    f">>> Campaña "
                    f"'{campaign['campaign_name']}': "
                    f"{len(prospects)} destinatarios pendientes"
                )

                for prospect in prospects:

                    mensaje = {
                        'campaign_id': campaign['campaign_id'],
                        'campaign_name': campaign['campaign_name'],
                        'marketing_id': campaign['marketing_id'],

                        'from_name': campaign['from_name'],
                        'from_addr': campaign['from_addr'],

                        'subject': campaign['subject'],
                        'body_html': campaign['body_html'],
                        'body': campaign['body'],

                        'to_name': (
                            f"{prospect['first_name']} "
                            f"{prospect['last_name']}"
                        ).strip(),

                        'to_email': prospect['email_address'],
                        'prospect_id': prospect['prospect_id']
                    }

                    channel.basic_publish(
                        exchange='',
                        routing_key=QUEUE,
                        body=json.dumps(mensaje),
                        properties=pika.BasicProperties(
                            delivery_mode=2
                        )
                    )

                    register_sent(
                        db,
                        campaign['campaign_id'],
                        campaign['marketing_id'],
                        prospect['prospect_id']
                    )

                    print(
                        f"    → Encolado: "
                        f"{prospect['email_address']}"
                    )

        except Exception as e:

            print(f">>> ERROR: {e}")

            db_conn = None
            rabbit_conn = None
            rabbit_channel = None

        print("\n>>> Esperando 60 segundos...\n")

        time.sleep(60)


if __name__ == '__main__':
    main()