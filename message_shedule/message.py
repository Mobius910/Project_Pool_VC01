import schedule
import time
import requests


# Run every 3 days
schedule.every(interval).days.do(message)



def get_settings(url):
    response = requests.get(url)
    print(response.status_code)  # HTTP status code (e.g., 200)
    print(response.text)         # Response body as text
    print(response.json())       # Parse JSON response (if applicable)


    interval = int(response.json()["notification"])
    return interval


def message():
    url = "http://fastapi:8000/send_email"
    data = {"subject": "Test Zwembad", "message": "Het is tijd voor een nieuwe meting van het zwembad! \n Probeer in de komende 24h een nieuwe meting te doen. \n \n Met vriendelijke groeten"}
    
    
    response = requests.post(url, json=data)
    print(response.status_code)  # HTTP status code (e.g., 200, 201)
    print(response.json())       # Parse JSON response


def update_schedule():
    """Fetch the interval and update the schedule dynamically."""
    global interval
    new_interval = get_settings("http://fastapi:8000/get_settings")

    if new_interval != interval:
        print(f"Updating schedule: {new_interval} days")
        interval = new_interval
        schedule.clear()  # Remove old schedules
        schedule.every(interval).days.do(message)


# Initialize interval
interval = get_settings("http://fastapi:8000/get_settings")
schedule.every(interval).days.do(message)  # Schedule first run



while True:
    update_schedule()  # Check for updates
    schedule.run_pending()
    time.sleep(3600)  # Check every hour










