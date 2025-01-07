# FastAPI + Kafka + MongoDB Twitter Login Project

### Project Overview

This project is a FastAPI-based application designed to handle Twitter login requests, manage user authentication, and integrate with Kafka for asynchronous message processing. It includes a MongoDB database for storing user information and task statuses, ensuring a secure and scalable workflow.

#### Core Features
1. **User Management**:
   - Users can register via the `/register` endpoint, providing a `username` and `password`.
   - Passwords are securely hashed using `bcrypt`, and JWT tokens are issued for authentication.

2. **Twitter Login**:
   - Authenticated users can send login requests to the `/twitter-login` endpoint.
   - Requests are sent to a Kafka topic (`twitter_login_requests`) for processing by a Kafka consumer.

3. **Task and Status Tracking**:
   - The Kafka consumer simulates the Twitter login and updates the task status (e.g., success or failure) in the database.

#### Database Relationships
The project uses MongoDB to manage three collections:

1. **Users**:
   - Stores registered user details, including `username` and `hashed_password`.
   - Each user has a unique `_id`.

2. **Twitter Users**:
   - Tracks Twitter account details, including `username`, `encrypted_password`, `phone_number`, and `email`.
   - References the corresponding `user_id` from the `users` collection to identify which user initiated the request.

3. **Task Statuses**:
   - Tracks the status of login tasks (e.g., success or failure) with `task_id`, `status`, and the associated `user_id` from the `users` collection.

#### Data Flow
1. **Register**: Users register with `/register`, and their credentials are securely stored in the `users` collection. A JWT token is returned for authentication.
2. **Login**: Users authenticate via `/login` and receive a JWT token.
3. **Twitter Login**: Authenticated users send requests to `/twitter-login`. The system:
   - Identifies the user using the JWT token.
   - Links the request to the user in the `users` collection.
   - Processes the request through Kafka, with results stored in `twitter_users` and `task_statuses`.

This architecture ensures clear relationships between users, their Twitter accounts, and task statuses while maintaining security and scalability.

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
│   │   ├── dependencies.py          # Reusable JWT validation dependency
│   │   ├── hash_utils.py            # Password hashing and verification utilities
│   │   ├── jwt_utils.py             # JWT creation and validation functions
│   │   └── helpers.py
│   ├── kafka
│   │   └── producer.py
│   ├── main.py                      # FastAPI app with endpoints
│   ├── models
│   │   ├── user.py                  # Pydantic models for register and login
│   │   ├── twitter.py               # Pydantic models for /twitter-login
│   └── tests
├── kafka_consumer
│   ├── consumer.py                  # Kafka consumer logic
│   ├── database.py                  # MongoDB interaction for user and task collections
├── poetry.lock
├── pyproject.toml                   # Poetry dependencies
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

## JWT Authentication

### Overview

The project now includes JWT-based authentication to ensure secure access to protected endpoints.

### Implementation Details

#### Registration (`/register`)

- Users can register with a username and password.
- Passwords are securely hashed using bcrypt (via passlib).
- A JWT token is returned upon successful registration.

#### Login (`/login`)

- Authenticates users by verifying their credentials against the database.
- Returns a JWT token with the user’s username in the payload (`sub` claim).

#### Protected Endpoint (`/twitter-login`)

- Access is restricted to authenticated users with a valid JWT token.
- Tokens are validated using a reusable dependency, ensuring security and ease of integration for other routes.

### Supporting Files and Modules

- **JWT Utilities** (`app/core/security/jwt_utils.py`): Contains functions for generating and validating JWT tokens.
- **Password Hashing** (`app/core/security/hash_utils.py`): Handles secure password hashing and verification.
- **Token Validation Dependency** (`app/core/security/dependencies.py`): Provides a reusable dependency for validating tokens in protected routes.

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
