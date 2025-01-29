from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import mariadb, time, os, requests, smtplib, socket, pymysql
from datetime import datetime
from contextlib import closing
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Create a FastAPI instance
app = FastAPI()

# Load environment variables
load_dotenv()

# Add cors
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database credentials
user = os.getenv('MYSQL_USER')
password = os.getenv('MYSQL_PASSWORD')
database = os.getenv('MYSQL_DATABASE')
host = os.getenv('HOST')
port = int(os.getenv('PORT'))


# Global database connection pool
pool = None

# Database connection
@app.on_event("startup")
def database_connection():
    # Attemps to create a connection with database every 30 seconds 10 times
    global pool
    retries = 10
    for attempt in range(retries):
        try:
            pool = mariadb.ConnectionPool(user=user, password=password, host=host, port=port, database=database, pool_name="pm_vc01", pool_size=5)
            print("Database connection established")
            return
        except Exception as e:
            print(f"Database connection failed: {e}. Retrying {attempt + 1}/{retries}")
            time.sleep(30)
    raise Exception("Database not reachable after retries")

# Disconnects database connection when API is turned off.
@app.on_event("shutdown")
def shutdown():
    if pool:
        pool.close()
        print("Database connection closed")

# API queries database for data
def query_db(query, parameters=None):
    if not pool:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = None
    result = None
    try:
        conn = pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, parameters)
        if query.strip().upper().startswith("SELECT"):
            # Fetch database results
            result = cursor.fetchall()
        conn.commit()
    except mariadb.Error as e:
        print("Error executing SQL query:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return result

# Path to the logfile
log_file_path = Path("logfile.log")

# API route to read log file
@app.get("/log")
async def get_log():
    if log_file_path.exists():
        with log_file_path.open("r") as file:
            log_content = file.readlines()
    else:
        log_content = ["Log file not found."]
        # Write error to log file
        with log_file_path.open("a") as file:
            file.write("[ERROR] Log file not found.\n")
    return JSONResponse(content={"log": log_content})

# Pydantic model for History
class history(BaseModel):
    date: datetime
    ph_value: float
    chlorine_ppm: float
    ph_plus: float
    ph_min: float
    chlorine: float   

@app.get("/history")
async def get_history() :
    try :
        query = "SELECT * FROM History" # env var
        result = query_db(query)
        if not result:
            raise HTTPException(status_code=404, detail="No user found")
        return {"history": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/history")
async def post_history() :
    try :
        # Extract values correctly from the Pydantic model
        date = history.date
        ph_value = history.ph_value
        chlorine_ppm = history.chlorine_ppm
        ph_plus = history.ph_plus
        ph_min = history.ph_min
        chlorine = history.chlorine

        # Insert the data into the database
        query_db(
            """
            INSERT INTO History (date, ph_value, chlorine_ppm, ph_plus, ph_min, chlorine)
            VALUES (?, ?, ?, ?, ?, ?,
            """,
            (date, ph_value, chlorine_ppm, ph_plus, ph_min, chlorine)
        )

        return {"message": "History successfully updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Pydantic model voor zwembadinstellingen
class Email(BaseModel):
    subject: str
    message: str


@app.post("/send_email")
def email(content: Email):
    try :
        result =  query_db("SELECT email_receiver FROM Settings LIMIT 1")

        # Email credentials
        sender_email = os.getenv('REMINDER_EMAIL') # Your Gmail address
        app_password = os.getenv('REMINDER_APP_PASSWORD')  # Your App Password from Google
        recipient_email =  result[0]["email_receiver"] # Recipient's email address

        # Set up the SMTP server
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # Email content
        subject = content.subject
        body = content.message

        # Create the email
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Connect to the SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, app_password)  # Log in to your email account
            server.sendmail(sender_email, recipient_email, message.as_string())  # Send email
            return("Email sent successfully!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# GET endpoint: Huidige instellingen ophalen
@app.get("/get_settings")
def get_settings():
    try:
        result = query_db("SELECT * FROM Settings LIMIT 1")
        if not result:
            raise HTTPException(status_code=404, detail="Geen instellingen gevonden")
        return result[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Pydantic model voor zwembadinstellingen
class PoolSettings(BaseModel):
    pool_volume: int
    ph_desired: float
    chlorine_desired: float
    ph_plus_dose: float
    ph_min_dose: float
    chlorine_dose: float
    notification_time: int
    email_receiver: str

@app.post("/post_settings")
def post_settings(settings: PoolSettings):
    try:
        # Extract values correctly from the Pydantic model
        volume = settings.pool_volume
        ph_current = settings.ph_desired
        chlorine_current = settings.chlorine_desired
        ph_plus_add = settings.ph_plus_dose
        ph_min_add = settings.ph_min_dose
        chlorine_add = settings.chlorine_dose
        notifi_time = settings.notification_time
        email = settings.email_receiver

        # update the data into the database
        query_db(
            """
            UPDATE Settings
            SET pool_volume = ?, 
                ph_desired = ?, 
                chlorine_desired = ?, 
                ph_plus_dose = ?, 
                ph_min_dose = ?, 
                chlorine_dose = ?, 
                notification = ?, 
                email_receiver = ?
            LIMIT 1
            """,
            (volume, ph_current, chlorine_current, ph_plus_add, ph_min_add, chlorine_add, notifi_time, email)
        )

        return {"message": "Settings successfully updated"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# To run the FastAPI app, use the following command in the terminal:
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload