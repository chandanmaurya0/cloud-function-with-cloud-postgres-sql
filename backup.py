import json
import time
from google.cloud.sql.connector import Connector
import pg8000
import functions_framework
import logging
import os

# Hard-coded configuration values (replace with your actual values)
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create a connector instance (reuse across requests)
connector = Connector()

# Global connection pool
connection = None

def connect():
    # Add retry logic for connection
    max_retries = 3
    retry_count = 0
    last_exception = None
    
    while retry_count < max_retries:
        try:
            logging.info(f"Attempting to connect to database (attempt {retry_count + 1}/{max_retries})")
            conn = connector.connect(
                INSTANCE_CONNECTION_NAME,
                "pg8000",
                user=DB_USER,
                password=DB_PASSWORD,
                db=DB_NAME,
                # Add connection timeout parameters
                timeout=30,  # seconds
            )
            logging.info("Successfully connected to database")
            return conn
        except Exception as e:
            last_exception = e
            logging.error(f"Connection attempt {retry_count + 1} failed: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                # Exponential backoff
                sleep_time = 2 ** retry_count
                logging.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
    
    # If we get here, all retries failed
    logging.error(f"All connection attempts failed: {str(last_exception)}")
    raise last_exception


@functions_framework.http
def list_users(request):
    global connection
    try:
        # Check if connection is still alive, reconnect if needed
        if connection is None:
            logging.info("No existing connection, creating new connection")
            connection = connect()
        else:
            try:
                # Test if connection is still alive
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                logging.info("Existing connection is valid")
            except Exception:
                logging.info("Existing connection is invalid, reconnecting")
                try:
                    connection.close()
                except:
                    pass  # Ignore errors when closing dead connection
                connection = connect()

        # Execute query with timeout
        start_time = time.time()
        cursor = connection.cursor()
        cursor.execute("SELECT user_id, username, email FROM users;")
        rows = cursor.fetchall()
        users = [{"user_id": row[0], "username": row[1], "email": row[2]} for row in rows]
        cursor.close()
        
        query_time = time.time() - start_time
        logging.info(f"Query executed successfully in {query_time:.2f} seconds")
        
        return json.dumps(users), 200, {"Content-Type": "application/json"}
    except Exception as e:
        logging.error(f"Error executing query: {str(e)}")
        error_type = type(e).__name__
        error_details = {
            "error_type": error_type,
            "error_message": str(e),
            "suggestion": "Check Cloud SQL connection settings and VPC connector configuration"
        }
        return json.dumps(error_details), 500, {"Content-Type": "application/json"}