# QT Global Software Assessment - Senior Backend Engineer

This repository contains the implementation of the Senior Python Backend take-home assignment. It is a production-ready, Dockerized User Status Service secured by mTLS (Mutual TLS) with UDP broadcasting capabilities.

## Architecture

*   **Ingress**: **Nginx** acting as a TLS termination proxy. It enforces `ssl_verify_client on`, verifies client certificates against a private CA, and extracts the identity (CN) to HTTP headers.
*   **Application**: **Django** (WSGI/Gunicorn) handling business logic. It authenticates users via the Trusted Header Pattern (middleware) and manages user state in PostgreSQL.
*   **Persistence**: **PostgreSQL** 15 (Alpine).
*   **Broadcasting**: **UDP** multicast/broadcast mechanism that announces Real-Time user updates to the network.

## Directory Structure

*   `server/`: Django application source code (Models, Middleware, Views).
*   `client/`: Python mTLS client script for testing.
*   `certs/`: Scripts to generate RFC-compliant Self-Signed Certificates (CA, Server, Client).
*   `config/nginx/`: Nginx proxy configuration.
*   `udp_listener.py`: Utility script to decode and print UDP broadcast packets.
*   `docker-compose.yml`: Full stack orchestration.

## Prerequisites

*   Docker & Docker Compose
*   Python 3.x (For running the client locally)

## Quick Start (Run in < 2 mins)

### 1. Setup Python Environment
Create and activate a virtual environment to manage dependencies securely.

```bash
# Create virtual environment
python -m venv env

# Activate it (Windows)
.\env\Scripts\activate
# OR (Mac/Linux)
source env/bin/activate

# Install dependencies
pip install -r client/requirements.txt
pip install -r server/requirements.txt
```

### 2. Configure Environment
Create a `.env` file from the example template to configure secrets and database credentials.
```bash
cp .env.example .env
```
*(You can adjust the values in `.env` if needed, but the defaults are set for local testing)*

### 3. Generate Certificates
Generate the required Self-Signed Certificates using the automated script. Nginx will use these to secure the connection.

```bash
python certs/gen_certs.py
```
*Creates: `ca.crt`, `server.crt`, `client.crt` and keys in `certs/`.*

### 4. Boot the Server
Start the entire stack. Database migrations are applied automatically on boot.

```bash
docker-compose up --build
```
> **Note**: The Nginx proxy listens on `https://localhost:443`.

### 5. Verify UDP Broadcasting
Since Docker networks isolate broadcast traffic from the host machine (especially on Windows/Mac), run the listener **inside** the application container to see the broadcasts clearly.

Open a **new terminal**:
```bash
# 1. Copy the listener script into the container
docker cp udp_listener.py qt-assessment-web-1:/app/

# 2. Run the listener inside the container network
docker-compose exec web python udp_listener.py
```
*Keep this terminal open. It will print packets as they arrive.*

### 6. Run the Client (Test Success)
Open a **third terminal** to simulate a valid client request.

```bash
# Run the client
python client/client.py
```

**Expected Output:**
*   **Client Terminal**: `Success! (204 No Content)`
*   **UDP Listener Terminal**:
    ```text
    ----------------------------------------
    Source Packet: ('172.x.x.x', 6666)
    User Email   : valid_user@qt-test.com
    Last Seen    : 2025-12-20 ...
    Client IP    : 172.x.x.x
    Client Port  : 62453
    ----------------------------------------
    ```

## Testing Scenarios

You can validate the security logic by running these additional scenarios:

**1. Invalid Identity (Bad Cert)**
Use a certificate with a Common Name (CN) that is *not* an email address.
```bash
python client/client.py --cert certs/bad_client.crt --key certs/bad_client.key
```
*Result: `400 Bad Request` ("CN must be a valid email address")*

**2. No Identity (Security Breach Attempt)**
Try to access the API without a client certificate.
```bash
curl -k https://localhost/api/client
```
*Result: `400 Bad Request` (Nginx rejects the handshake: "No required SSL certificate was sent")*

## Technical Design Decisions

1.  **TLS Termination at Edge**: Nginx handles the heavy lifting of encryption and certificate verification. This keeps the Python application simple and focused on business logic.
2.  **Middleware Authentication**: A custom Django Middleware (`MTLSAuthenticationMiddleware`) trusts the headers provided by Nginx to authenticate the user, adhering to the "Separation of Concerns" principle.
3.  **Singleton Broadcaster**: The UDP Broadcaster is implemented as a thread-safe Singleton to ensure efficient socket reuse.
4.  **Robust Cert Generation**: The `gen_certs.py` script generates X.509 v3 certificates with Subject Alternative Names (SAN) to ensure compatibility with modern SSL libraries (resolving `Hostname mismatch` errors).
