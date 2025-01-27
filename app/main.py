from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
import mariadb, time, os, socket

# Create a FastAPI instance
app = FastAPI()

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

# Database connection
@app.on_event("startup")
def database_connection():
    # Attemps to create a connection with database every 30 seconds 10 times
    global pool
    retries = 10
    for attempt in range(retries):
        try:
            pool = mariadb.ConnectionPool(user="#", password="#", host="#", port=3306, database="#", pool_name="#", pool_size=5)
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


# 
@app.get("/", response_class=HTMLResponse)
async def show_log(request: Request):
    # Path to the logfile
    log_file_path = Path("logfile.log")
    log_content = []

    if log_file_path.exists():
        # Read the log file
        with log_file_path.open("r") as file:
            log_content = file.readlines()
    else:
        log_content = ["Log file not found."]
        # Write error to log file
        with log_file_path.open("a") as file:
            file.write("[ERROR] Log file not found.\n")

    return templates.TemplateResponse("logviewer.html", {"request": request, "log_content": log_content})

# To run the FastAPI app, use the following command in the terminal:
# uvicorn app:app --reload
