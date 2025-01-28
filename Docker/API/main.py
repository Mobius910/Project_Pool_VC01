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
DB_USER = "monitor"
DB_PASSWORD = "monitor"
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


#get User name
@app.get("/user")
def get_user():
    with closing(pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM milestone2 LIMIT 1")
            result = cursor.fetchone()

    return {"name": result[0]}


#post new name
class NameRequest(BaseModel):
    name: str

@app.post("/update_user")
def update_user(new_name: NameRequest):
    # Extract the new name from the request body
    new_name_value = new_name.name

    # Connect to the database and update the name
    with closing(pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )) as connection:
        with connection.cursor() as cursor:
            # Update the name in the database
            cursor.execute("UPDATE milestone2 SET name = %s WHERE id = 1", (new_name_value,))
            connection.commit()

    return {"message": f"Name updated to {new_name_value}"}