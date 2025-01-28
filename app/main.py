from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
import mariadb, time, os

# Create a FastAPI instance
app = FastAPI()

# Load environment variables
load_dotenv()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow from any domain
    allow_credentials=True, # Allow cookies and tokens
    allow_methods=["POST"], # Only allow POST requests
    allow_headers=["*"], # allow any header type
)
      
# Global database connection pool
pool = None

# Database credentials
user = os.getenv('MYSQL_USER')
password = os.getenv('MYSQL_PASSWORD')
database = os.getenv('MYSQL_DATABASE')
host = os.getenv('HOST')
port = os.getenv('PORT')

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
@app.post("/calculate")
async def add_calculation(calculation: str):
    try:
        with log_file_path.open("a") as file:
            file.write(f"[INFO] New calculation: {calculation}\n")
        return {"message": "Calculation logged successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing to log: {e}")

# To run the FastAPI app, use the following command in the terminal:
# uvicorn main:app --host 0.0.0.0 --port 3000 --reload
