# Cloud Function with Cloud SQL

This is a Google Cloud Function that connects to a PostgreSQL database in Cloud SQL and retrieves user data.

## Overview

The function `list_users` is an HTTP-triggered Cloud Function that:
- Connects to a PostgreSQL database in Cloud SQL
- Retrieves all users from the `users` table
- Returns the data as a JSON response

## Prerequisites

- Python 3.7 or higher
- Google Cloud SDK
- A Google Cloud SQL PostgreSQL instance
- Appropriate permissions to access the Cloud SQL instance

## Setup

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd cloud-function-with-cloud-sql
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with the following variables:
   ```
   INSTANCE_CONNECTION_NAME=<your-project>:<your-region>:<your-instance>
   DB_USER=<database-user>
   DB_PASSWORD=<database-password>
   DB_NAME=<database-name>
   ```

## Database Schema

The function expects a `users` table with the following schema:
```sql
CREATE TABLE users (
  user_id INTEGER PRIMARY KEY,
  username VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL
);
```

## Running Locally

1. Make sure you have the Functions Framework installed:
   ```bash
   pip install functions-framework
   ```

2. Run the function locally:
   ```bash
   functions-framework --target=list_users --debug
   ```

3. Test the function:
   ```bash
   curl http://localhost:8080
   ```

### Local Database Connection Options

For local development, you have two main options:

#### Option 1: Cloud SQL Auth Proxy

1. Install the Cloud SQL Auth Proxy:
   ```bash
   curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.0.0/cloud-sql-proxy.darwin.amd64
   chmod +x cloud-sql-proxy
   ```

2. Run the proxy:
   ```bash
   ./cloud-sql-proxy <INSTANCE_CONNECTION_NAME>
   ```

3. Update your `.env` file to connect to localhost:
   ```
   INSTANCE_CONNECTION_NAME=<your-project>:<your-region>:<your-instance>
   DB_USER=<database-user>
   DB_PASSWORD=<database-password>
   DB_NAME=<database-name>
   ```

#### Option 2: Local PostgreSQL

For completely local development, you can use a local PostgreSQL instance and modify your connection code accordingly.

## Deployment

Deploy the function to Google Cloud:

```bash
gcloud functions deploy list_users \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated
```

## Environment Variables for Deployment

When deploying to Google Cloud, set these environment variables:

```bash
gcloud functions deploy list_users \
  --set-env-vars INSTANCE_CONNECTION_NAME=<your-project>:<your-region>:<your-instance>,DB_USER=<database-user>,DB_PASSWORD=<database-password>,DB_NAME=<database-name>
```

## Security Considerations

- For production, avoid using `--allow-unauthenticated`
- Store sensitive information like database credentials in Secret Manager
- Consider using IAM database authentication instead of passwords