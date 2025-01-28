from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import socket
import pymysql
from contextlib import closing


app = FastAPI()

# Add cors
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database configuration
DB_USER = "root"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "pool_monitor_vc01"



@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# Get hostname
@app.get("/hostname")
def get_hostname():
    hostname = socket.gethostname()
    return {"hostname": hostname}


