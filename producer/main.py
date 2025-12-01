import time
import json
import requests
import sys
from datetime import datetime
from confluent_kafka import Producer

# Configuration
KAFKA_BROKER = 'kafka:9092'
TOPIC_NAME = 'air_quality_measurements'
SLEEP_TIME = 3600  # 1 hour

# Top 19 French Cities 
CITIES = [
    {"name": "Paris", "latitude": 48.853, "longitude": 2.349},
    {"name": "Marseille", "latitude": 43.297, "longitude": 5.381},
    {"name": "Lyon", "latitude": 45.749, "longitude": 4.848},
    {"name": "Toulouse", "latitude": 43.604, "longitude": 1.444},
    {"name": "Nice", "latitude": 43.703, "longitude": 7.266},
    {"name": "Nantes", "latitude": 47.218, "longitude": -1.554},
    {"name": "Montpellier", "latitude": 43.611, "longitude": 3.877},
    {"name": "Strasbourg", "latitude": 48.583, "longitude": 7.750},
    {"name": "Bordeaux", "latitude": 44.833, "longitude": -0.567},
    {"name": "Lille", "latitude": 50.633, "longitude": 3.067},
    {"name": "Rennes", "latitude": 48.112, "longitude": -1.674},
    {"name": "Reims", "latitude": 49.263, "longitude": 4.035},
    {"name": "Le Havre", "latitude": 49.493, "longitude": 0.108},
    {"name": "Saint-Étienne", "latitude": 45.433, "longitude": 4.394},
    {"name": "Toulon", "latitude": 43.125, "longitude": 5.930},
    {"name": "Grenoble", "latitude": 45.188, "longitude": 5.724},
    {"name": "Dijon", "latitude": 47.322, "longitude": 5.041},
    {"name": "Angers", "latitude": 47.478, "longitude": -0.563},
    {"name": "Nîmes", "latitude": 43.837, "longitude": 4.360}
]

def get_air_quality(lat, lon):
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["pm10", "pm2_5", "nitrogen_dioxide", "ozone", "sulphur_dioxide", "european_aqi"],
        "timezone": "Europe/Paris"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def wait_until_next_hour():
    """Wait until the next hour (e.g., if it's 14:23, wait until 15:00)"""
    now = datetime.now()
    # Calculate seconds until next hour
    minutes_to_wait = 59 - now.minute
    seconds_to_wait = 60 - now.second
    total_seconds = minutes_to_wait * 60 + seconds_to_wait
    
    next_hour = (now.hour + 1) % 24
    print(f"Current time: {now.strftime('%H:%M:%S')}")
    print(f"Waiting {total_seconds} seconds until {next_hour:02d}:00...")
    time.sleep(total_seconds)

def main():
    print("Waiting for Kafka...")
    time.sleep(30) 
    
    conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'client.id': 'python-producer'
    }
    
    producer = Producer(conf)
    print("Connected to Kafka (confluent-kafka)!")
    
    # Wait until the next full hour before starting
    wait_until_next_hour()

    while True:
        print(f"Fetching data at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
        
        # Round to current hour in UTC
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        rounded_time = now_utc.replace(minute=0, second=0, microsecond=0)
        
        for city in CITIES:
            data = get_air_quality(city['latitude'], city['longitude'])
            if data and 'current' in data:
                message = {
                    "city": city['name'],
                    "latitude": city['latitude'],
                    "longitude": city['longitude'],
                    "timestamp": rounded_time.isoformat(),  # UTC avec timezone
                    "pm10": data['current']['pm10'],
                    "pm2_5": data['current']['pm2_5'],
                    "no2": data['current']['nitrogen_dioxide'],
                    "o3": data['current']['ozone'],
                    "so2": data['current']['sulphur_dioxide'],
                    "aqi": data['current']['european_aqi']
                }
                
                producer.produce(
                    TOPIC_NAME, 
                    value=json.dumps(message).encode('utf-8'), 
                    callback=delivery_report
                )
                producer.poll(0)
        
        producer.flush()
        print(f"Data sent! Sleeping for {SLEEP_TIME} seconds...")
        time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    main()
