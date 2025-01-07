# FastAPI + Kafka + MongoDB Twitter Login Project

## Prerequisites

Before you begin, ensure you have the following installed and available:

1. **Python 3.10+**
2. [**Poetry**](https://python-poetry.org/docs/#installation) for managing dependencies
3. **Apache Kafka** (locally or via Docker Compose)
4. **MongoDB** (locally or via Docker)
5. **Redis** (for rate-limiting via `fastapi-limiter`)
6. **OpenSSL** or similar for generating a key (or simply use Python’s `Fernet.generate_key()`)

---

## Project Structure Recap

```
.
├── README.md
├── app
│   ├── __init__.py
│   ├── api
│   ├── core
│   │   └── security
│   ├── kafka
│   │   └── producer.py
│   ├── main.py
│   ├── models
│   │   └── twitter.py
│   └── tests
├── kafka_consumer
│   ├── consumer.py
│   └── database.py
├── poetry.lock
├── pyproject.toml
└── pytest.ini
```

---

## Environment Variables

Create a `.env` file (or use your shell environment) and define the following variables:

```bash
# Kafka broker URL (defaults to localhost:9092 if not provided)
KAFKA_BROKER_URL="localhost:9092"

# Kafka topic name (defaults to twitter_login_requests if not provided)
KAFKA_TOPIC_NAME="twitter_login_requests"

# MongoDB connection string (defaults to mongodb://localhost:27017)
MONGO_URI="mongodb://localhost:27017"

# Name of your MongoDB database (defaults to twitter_login_kafka)
DATABASE_NAME="twitter_login_kafka"

# Encryption key used by Fernet for encrypting user passwords in the DB
# Generate using: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY="<paste-your-generated-key-here>"
```

> **Note:** These defaults can be changed in your code or environment, but it’s recommended to keep them in a `.env` file and load them securely.

---

## Installation Steps

1. **Clone the repository**  
   ```bash
   git clone <your-repo-url>.git
   cd <your-repo-directory>
   ```

2. **Install dependencies using Poetry**  
   ```bash
   poetry install
   ```

3. **Set up environment variables**  
   - Create a `.env` file in your project root and add the variables listed above.  
   - Alternatively, export them in your shell, e.g.:
     ```bash
     export KAFKA_BROKER_URL="localhost:9092"
     export MONGO_URI="mongodb://localhost:27017"
     ...
     ```

4. **(Optional) Generate a new Fernet key**  
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
   Copy and paste the generated key as your `ENCRYPTION_KEY`.

---

## Setting Up Services

### Start MongoDB

If running locally without Docker:
```bash
mongod --dbpath /path/to/your/db
```
*(Adjust the path as necessary.)*

If using Docker:
```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  mongo:latest
```

### Start Kafka

Example using Docker Compose:

```yaml
# docker-compose.yml
version: '3.8'
services:
  zookeeper:
    image: bitnami/zookeeper:latest
    environment:
      - ZOO_ENABLE_AUTH=no
    ports:
      - "2181:2181"

  kafka:
    image: bitnami/kafka:latest
    ports:
      - "9092:9092"
    environment:
      - KAFKA_BROKER_ID=1
      - KAFKA_LISTENERS=PLAINTEXT://:9092
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092
      - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
    depends_on:
      - zookeeper
```

Start Kafka with:
```bash
docker-compose up -d
```

Alternatively, if you have Kafka installed locally, start Zookeeper and Kafka:
```bash
# Start Zookeeper
zookeeper-server-start.sh config/zookeeper.properties

# Start Kafka
kafka-server-start.sh config/server.properties
```

### Start Redis

If running locally without Docker:
```bash
redis-server
```

If using Docker:
```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:latest
```

---

## Run the FastAPI Application

From within the project directory:
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Visit `http://localhost:8000` to see the welcome message.

---

## Run the Kafka Consumer

In a separate terminal, run:
```bash
poetry run python kafka_consumer/consumer.py
```

The consumer will connect to Kafka, listen for messages on the `twitter_login_requests` topic, and process them by inserting data into MongoDB.

---

## Testing the `/twitter-login` Endpoint

1. **Send a POST request** to `http://localhost:8000/twitter-login` with a JSON body containing the required fields (`username`, `password`, `phone_number`) and optional `email`. For example:

   ```bash
   curl -X POST -H "Content-Type: application/json" \
   -d '{
     "username": "testuser",
     "password": "p@ssw0rd!",
     "phone_number": "+1234567890",
     "email": "test@example.com"
   }' \
   http://localhost:8000/twitter-login
   ```

2. **Check the response** – You should see a JSON object containing a `task_id`. Example response:
   ```json
   {
     "task_id": "ece24c90-7e66-4282-942f-97ae8582fe42"
   }
   ```

3. **Observe the Consumer logs** – If the consumer is running, you’ll see messages in the terminal indicating that it has received a new message and processed the task.

4. **Check MongoDB** – Verify that collections `twitter_users` and `task_statuses` are created or updated with the correct data.

---

## Common Configuration & Troubleshooting

1. **Environment Variables**:  
   - Ensure your `.env` or shell variables are accessible to your Python environment.  
   - Double-check `ENCRYPTION_KEY` is correctly set, especially if you see encryption or decryption errors.

2. **Kafka Connection**:  
   - Ensure `KAFKA_BROKER_URL` matches the actual broker host (especially if Docker uses a different network).

3. **MongoDB Connection**:  
   - Confirm that the `MONGO_URI` is reachable. If you see authentication errors, verify username/password if configured.

4. **Redis Connection**:  
   - If you see rate-limiter errors, ensure Redis is running on `redis://localhost:6379`. Adjust the host/port if using Docker.

5. **Port Conflicts**:  
   - If Kafka or Redis are not starting, check if the ports (9092 for Kafka, 6379 for Redis) are already in use.

---

## Additional Notes

- **Security**: For real-world usage, do not store passwords in plaintext, even briefly. Here, encryption is done via Fernet, but always consider hashing or additional security measures.
- **Logging**: Adjust the logging level (`logging.basicConfig(level=logging.INFO)`) to debug or error as needed.
- **Production**: For production, consider using a process manager (e.g., Gunicorn) for serving FastAPI, a robust Kafka configuration, and a secure MongoDB deployment.
- **Rate Limiting**: Currently uses `fastapi-limiter`. Tweak `RateLimiter(times=5, seconds=60)` in `main.py` to change request rate limit.

---

**Enjoy building with FastAPI, Kafka, and MongoDB!** If you run into any issues or need additional explanations, feel free to ask for clarifications.
