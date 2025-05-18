import os
import json
from google.cloud.sql.connector import Connector
import pg8000
import functions_framework

from dotenv import load_dotenv


load_dotenv()


# Create a connector instance (reuse across requests)
connector = Connector()

# Global connection pool
connection = None

def connect():
    return connector.connect(
        os.environ["INSTANCE_CONNECTION_NAME"],
        "pg8000",
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        db=os.environ["DB_NAME"],
    )


@functions_framework.http

def list_users(request):
    global connection
    if connection is None:
        connection = connect()

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT user_id, username, email FROM users;")
        rows = cursor.fetchall()
        users = [{"user_id": row[0], "username": row[1], "email": row[2]} for row in rows]
        cursor.close()
        return json.dumps(users), 200, {"Content-Type": "application/json"}
    except Exception as e:
        return json.dumps({"error": str(e)}), 500, {"Content-Type": "application/json"}