from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import mariadb, time, os, requests, socket, pymysql
from contextlib import closing
import smtplib
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
port = os.getenv('PORT')

# Database configuration
DB_USER = "root"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "pool_monitor_vc01"

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
def query(query, parameters=None):
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

    

# API route to add a new calculation log
@app.post("/")
async def calculation():
    try :
        form_data = await requests.form()
        value = form_data.get("value")
    
        if not value:
            raise HTTPException(status_code=400, detail="No data provided")
        
        # Here you can process the data or store it
        print(f"Received data: {value}")
        
        # Optionally, send the data to another API (example)
        # raspberry_pi_url = "http://<raspberry-pi-ip>:<port>/receive-data"
        # payload = {"value": value}
        # response = requests.post(raspberry_pi_url, json=payload)
        
        return {"status": "success", "message": f"Data received: {value}"}
        #try: # moet in endpoint om index pagina calc naar raspberry te sturen.
        #    with log_file_path.open("a") as file:
        #        file.write(f"[INFO] New calculation: {calculation}\n")
        #    return {"message": "Calculation logged successfully."}
        #except Exception as e:
        #    raise HTTPException(status_code=500, detail=f"Error writing to log: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    
@app.get("/history")
async def history() :
    try :
        query = "SELECT * FROM History" # env var
        result = query(query)
        if not result:
            raise HTTPException(status_code=404, detail="No user found")
        return {"history": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/email")
async def email() :
    try :
        # Email credentials
        sender_email = os.getenv('REMINDER_EMAIL') # Your Gmail address
        app_password = os.getenv('REMINDER_APP_PASSWORD')  # Your App Password from Google
        recipient_email = "robbedoes.keppens@gmail.com"  # Recipient's email address

        # Email content
        subject = "Zwembad Meten"
        body = "Tijd om de waarden van je zwembad te meten!"

        # Set up the SMTP server
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

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
            print("Email sent successfully!")
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
    notification: int

# GET endpoint: Huidige instellingen ophalen
@app.get("/settings")
def get_settings():
    try:
        result = query("SELECT * FROM Settings LIMIT 1")
        if not result:
            raise HTTPException(status_code=404, detail="Geen instellingen gevonden")
        return result[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# To run the FastAPI app, use the following command in the terminal:
# uvicorn main:app --host 0.0.0.0 --port 3000 --reload