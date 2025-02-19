import schedule
import time
import requests, os
from dotenv import load_dotenv

base_url = os.getenv('URL', "http://192.168.238.189:8000")

# Function to fetch settings
def get_settings(url):
    response = requests.get(url)
    print(response.status_code)  # HTTP status code (e.g., 200)
    print(response.text)         # Response body as text
    print(response.json())       # Parse JSON response (if applicable)

    return int(response.json()["notification"])  # Return interval as an integer


# Function to send the email
def message():
    url = base_url + "/send_email"
    data = {"subject": "Test Zwembad", "message": "Het is tijd voor een nieuwe meting van het zwembad! \nProbeer in de komende 24h een nieuwe meting te doen. \n \n Met vriendelijke groeten"}

    print("Sending email...")
    response = requests.post(url, json=data)
    print(response.status_code)  # HTTP status code (e.g., 200, 201)
    print(response.json())       # Parse JSON response


# Initialize interval before scheduling
interval = get_settings(base_url + "/get_settings")

# Schedule the job with the retrieved interval
schedule.every(interval).days.do(message)


def update_schedule():
    """Fetch the interval and update the schedule dynamically."""
    global interval  # Indicate that we're modifying the global variable
    new_interval = get_settings(base_url + "/get_settings")

    if new_interval != interval:
        print(f"Updating schedule: {new_interval} days")
        interval = new_interval
        schedule.clear()  # Remove old schedules
        schedule.every(interval).days.do(message)


# Run the scheduler loop
while True:
    update_schedule()  # Check for updates
    schedule.run_pending()
    message()
    time.sleep(3600)  # Check every hour
