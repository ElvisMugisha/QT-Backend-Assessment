# Project Walkthrough & Explanation Guide

This guide is designed to help you **present** your solution. It explains how the components "talk" to each other and provides a script for demonstrating the project.

---

## 1. The Big Picture: How it works

Your application is a **Secure User Status System**. It consists of three main parts that work together like a relay team.

### The Relay Team (Architecture)

1.  **The Bouncer (Nginx):**
    - **Location:** Sitting at the front door (Port 443).
    - **Job:** "I don't let anyone in unless they have a valid ID card (Certificate) signed by our Boss (CA)."
    - **Action:** It checks the certificate. If valid, it reads the name on the card (Email) and shouts it to the Backend.

2.  **The Clerk (Django Application):**
    - **Location:** Working in the back office (Port 8000), protected by the Bouncer.
    - **Job:** "I trust whatever name the Bouncer shouts. I'll update the record file (Database) for that person."
    - **Action:** It updates the `User` table (Last Seen, IP) and then hands a message to the Broadcaster.

3.  **The Broadcaster (UDP Singleton):**
    - **Location:** Same office as the Clerk.
    - **Job:** "I shout the update to the whole building so everyone knows."
    - **Action:** Sends a binary data packet over the network (UDP Port 6667) saying "User X is here!".

---

## 2. Step-by-Step Execution Flow

Here is what happens technically when you run the client script:

### Step 1: The Connection (mTLS Handshake)

- **Action:** You run `python client/client.py`.
- **What happens:** The script initiates a TLS connection to `https://localhost`. It presents `client.crt` (your ID).
- **Security:** Nginx validates the certificate against `ca.crt`. **This is the authentication.** No passwords are sent.

### Step 2: The Handoff (Reverse Proxy)

- **Action:** Nginx accepts the connection.
- **What happens:** Nginx extracts the "Common Name" (CN) from your certificate (e.g., `valid_user@qt-test.com`).
- **Injection:** It adds a special HTTP Header `X-Subject-CN: valid_user@qt-test.com` and forwards the request to Django.

### Step 3: Logic & Persistence (Django)

- **Action:** Django receives the PATCH request.
- **Code:** `server/apps/accounts/middleware.py` reads the `X-Subject-CN` header.
- **Database:** It finds the User with that email in PostgreSQL and updates their `last_seen_ns`.

### Step 4: The Broadcast (UDP)

- **Action:** After saving to the DB, Django triggers `broadcaster.send()`.
- **Packet:** It packs the data into binary format (bytes) and sends it to `255.255.255.255` on port 6667.
- **Receiver:** The `udp_listener.py` script (running separately) catches this packet, decodes the binary, and prints the human-readable info.

---

## 3. Live Demo Script (What to do & Say)

Use this script during your interview presentation.

### **Phase 1: Setup**

"First, I'll start the infrastructure. I'm using Docker Compose to orchestrate Nginx, Postgres, and the Django Application."

**Command:**

```bash
docker-compose up --build -d
```

_(Wait for containers to start... "You can see the database initializing and the web server coming online.")_

### **Phase 2: The Listener (Task 2)**

"Now, I'll start the UDP listener. This represents other services in the network listening for status updates. It handles raw binary packets."

**Command (Open a NEW terminal):**

> Note: We run this inside the container to see docker network traffic clearly.

```bash
docker-compose exec web python udp_listener.py
```

_(Leave this running visible on one side of the screen)_

### **Phase 3: The Client (Task 1)**

"Now I will act as a client. This Python script uses my client certificate to authenticate securely."

**Command (Open another NEW terminal):**

```bash
python client/client.py
```

### **Phase 4: The Reveal**

1.  **Client Terminal:** You should see `Success! (204 No Content)`.
    - _Say:_ "The server accepted my mTLS connection and processed the request."
2.  **Listener Terminal:** You should see a new block of text.
    - _Say:_ "And here, instantly, the listener received the UDP broadcast with the user's email and new timestamp."

---

## 4. Troubleshooting Questions

**Q: Why separate Nginx and Django?**
A: "Performance and Security. Nginx handles the heavy TLS encryption efficiently, allowing Django to focus purely on business logic."

**Q: How does the server know who I am?**
A: "It extracts the 'Common Name' field from my x509 Client Certificate. I built a custom Middleware in Django to read this from the headers passed by Nginx."

**Q: What happens if I don't send a cert?**
A: "Nginx will reject the connection immediately during the handshake. The request never even reaches the application."
