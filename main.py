# https://github.com/GoogleCloudPlatform/cloud-sql-python-connector/blob/31ec9ca2a25d3fcb378d89d78684993fc3bd0d3b/samples/notebooks/postgres_python_connector.ipynb

import json
import time
import functions_framework
import logging
import os
import sqlalchemy
from google.cloud.sql.connector import Connector

# Configuration values from environment variables
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST", None)  # Private IP of Cloud SQL
DB_PORT = int(os.getenv("DB_PORT", 5432))  # Default PostgreSQL port

# Configure logging
logging.basicConfig(level=logging.INFO)


# Function to create database connection based on configuration
def create_connection_pool():
    # Check if we should use private IP or instance connection name
    if DB_HOST:
        # Connect using private IP and port
        logging.info(f"Connecting to Cloud SQL using private IP: {DB_HOST}:{DB_PORT}")
        db_url = sqlalchemy.engine.url.URL.create(
            drivername="postgresql+pg8000",
            username=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
        )

        # Create SQLAlchemy engine with the connection URL
        return sqlalchemy.create_engine(
            db_url,
            pool_size=5,  # Maximum number of connections in the pool
            max_overflow=2,  # Maximum number of connections that can be created beyond pool_size
            pool_timeout=30,  # Seconds to wait before timing out on getting a connection from the pool
            pool_recycle=1800,  # Recycle connections after 30 minutes
            pool_pre_ping=True,  # Enable connection health checks
        )
    else:
        # Connect using instance connection name
        logging.info(
            f"Connecting to Cloud SQL using instance connection name: {INSTANCE_CONNECTION_NAME}"
        )
        # Initialize Connector object
        connector = Connector()

        # Function to return the database connection object
        def getconn():
            try:
                conn = connector.connect(
                    INSTANCE_CONNECTION_NAME,
                    "pg8000",  # Using pg8000 driver for PostgreSQL
                    user=DB_USER,
                    password=DB_PASSWORD,
                    db=DB_NAME,
                )
                return conn
            except Exception as e:
                logging.error(f"Error connecting to database: {str(e)}")
                raise e

        # Create connection pool with 'creator' argument to our connection object function
        return sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            pool_size=5,  # Maximum number of connections in the pool
            max_overflow=2,  # Maximum number of connections that can be created beyond pool_size
            pool_timeout=30,  # Seconds to wait before timing out on getting a connection from the pool
            pool_recycle=1800,  # Recycle connections after 30 minutes
            pool_pre_ping=True,  # Enable connection health checks
        )


# Create the connection pool
pool = create_connection_pool()


def execute_with_retry(query_func, max_retries=3):
    """Execute a database query with retry logic and exponential backoff"""
    retry_count = 0
    last_exception = None

    while retry_count < max_retries:
        try:
            logging.info(
                f"Attempting to execute query (attempt {retry_count + 1}/{max_retries})"
            )
            result = query_func()
            logging.info("Query executed successfully")
            return result
        except Exception as e:
            last_exception = e
            logging.error(f"Query attempt {retry_count + 1} failed: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                # Exponential backoff
                sleep_time = 2**retry_count
                logging.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)

    # If we get here, all retries failed
    logging.error(f"All query attempts failed: {str(last_exception)}")
    raise last_exception


@functions_framework.http
def list_users(request):
    try:
        # Define the query function to be executed with retry logic
        def query_func():
            start_time = time.time()

            # Use SQLAlchemy to execute the query
            with pool.connect() as conn:
                # Create a SQLAlchemy text object for the query
                query = sqlalchemy.text("SELECT user_id, username, email FROM users")
                result = conn.execute(query)
                rows = result.fetchall()

                # Convert rows to dictionaries
                users = [
                    {"user_id": row[0], "username": row[1], "email": row[2]}
                    for row in rows
                ]

            query_time = time.time() - start_time
            logging.info(f"Query executed successfully in {query_time:.2f} seconds")
            return users

        # Execute the query with retry logic
        users = execute_with_retry(query_func)

        return json.dumps(users), 200, {"Content-Type": "application/json"}
    except Exception as e:
        logging.error(f"Error executing query: {str(e)}")
        error_type = type(e).__name__
        error_details = {
            "error_type": error_type,
            "error_message": str(e),
        }
        return json.dumps(error_details), 500, {"Content-Type": "application/json"}
