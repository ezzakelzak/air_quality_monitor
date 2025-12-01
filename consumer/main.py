import json
import os
import time
from kafka import KafkaConsumer
import psycopg2

# Configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'kafka:9092')
TOPIC = 'air_quality_measurements'
PG_HOST = os.getenv('POSTGRES_HOST', 'postgres')
PG_USER = os.getenv('POSTGRES_USER', 'admin')
PG_PASS = os.getenv('POSTGRES_PASSWORD', 'admin')
PG_DB = os.getenv('POSTGRES_DB', 'ecologie_data')

def get_db_connection():
    try:
        return psycopg2.connect(
            host=PG_HOST,
            user=PG_USER,
            password=PG_PASS,
            dbname=PG_DB
        )
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return None

def main():
    print("Starting Python Consumer...")
    
    # Wait for services to be ready
    time.sleep(30)

    # Connect to DB
    conn = None
    while conn is None:
        conn = get_db_connection()
        if conn is None:
            print("Waiting for Postgres...")
            time.sleep(5)
    
    cur = conn.cursor()
    print("Connected to Postgres.")

    # Connect to Kafka
    consumer = None
    while consumer is None:
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='air_quality_group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            print("Connected to Kafka.")
        except Exception as e:
            print(f"Waiting for Kafka ({e})...")
            time.sleep(5)

    print("Listening for messages...")
    for message in consumer:
        data = message.value
        print(f"Received data for {data.get('city')}")
        
        try:
            # Check if connection is alive
            if conn.closed:
                print("Connection closed, reconnecting...")
                conn = get_db_connection()
                cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO raw_measurements 
                (city, latitude, longitude, timestamp, pm10, pm2_5, no2, o3, so2, aqi)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    data['city'],
                    data['latitude'],
                    data['longitude'],
                    data['timestamp'],
                    data['pm10'],
                    data['pm2_5'],
                    data['no2'],
                    data['o3'],
                    data['so2'],
                    data['aqi']
                )
            )
            conn.commit()
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            print(f"DB Connection lost ({e}), reconnecting...")
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                
                cur.execute(
                    """
                    INSERT INTO raw_measurements 
                    (city, latitude, longitude, timestamp, pm10, pm2_5, no2, o3, so2, aqi)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        data['city'],
                        data['latitude'],
                        data['longitude'],
                        data['timestamp'],
                        data['pm10'],
                        data['pm2_5'],
                        data['no2'],
                        data['o3'],
                        data['so2'],
                        data['aqi']
                    )
                )
                conn.commit()
                print("Retry successful.")
            except Exception as retry_e:
                print(f"Retry failed: {retry_e}")
        except Exception as e:
            print(f"Error inserting data: {e}")
            if not conn.closed:
                conn.rollback()

if __name__ == "__main__":
    main()
