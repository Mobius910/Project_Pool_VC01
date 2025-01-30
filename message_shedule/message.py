import schedule
import time
import requests

# Run every 3 days
schedule.every(3).days.do(message)



def get_settings():
    response = requests.get("http://fastapi:8000/get_settings")
    print(response.status_code)  # HTTP status code (e.g., 200)
    print(response.text)         # Response body as text
    print(response.json())       # Parse JSON response (if applicable)


def message():
    url = "http://fastapi:8000/send_email"
    data = {"subject": "Test Zwembad", "message": "Het is tijd voor een nieuwe meting van het zwembad! \n Probeer in de komende 24h een nieuwe meting te doen. \n \n Met vriendelijke groeten"}
    
    
    response = requests.post(url, json=data)
    print(response.status_code)  # HTTP status code (e.g., 200, 201)
    print(response.json())       # Parse JSON response




while True:
    get_settings()
    schedule.run_pending()
    time.sleep(3600)  # Check every hour










