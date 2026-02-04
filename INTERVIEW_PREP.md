# Interview Preparation Guide: QT Global Software Assessment

**Project Title:** Verified User Status Service (mTLS + UDP)
**Stack:** Python (Django), Nginx, PostgreSQL, Docker

---

## 1. Executive Summary (The "Elevator Pitch")

"I built a secure, high-performance User Status Service designed to run in a containerized environment. It features **Mutual TLS (mTLS)** authentication terminated at an Nginx edge proxy, which securely identifies clients without passwords. The core application logic acts as a Source of Truth for user activity, updating a PostgreSQL database and immediately broadcasting real-time status updates to the local network via **UDP multicast**, allowing other services to react to user presence instantly."

---

## 2. Architecture Overview

You used a **Microservices-ready** architecture with 3 main containers:

1.  **Nginx (The Gatekeeper):**
    - **Role:** TLS Termination Proxy.
    - **Why:** Offloads encryption overhead from the application. Nginx is faster and more robust for SSL handshakes than Python/Java.
    - **Configuration:** Enforces `ssl_verify_client on`. Verifies the client's certificate against your self-signed CA. Extracts the `CN` (Common Name) and passes it upstream as the `X-Subject-CN` header.

2.  **Django App (The Core):**
    - **Role:** Business Logic & State Management.
    - **Why:** Rapid development, robust middleware support, and easy ORM interaction.
    - **Auth:** Uses a custom `MTLSAuthenticationMiddleware`. It trusts the `X-Subject-CN` header (security relies on the fact that only Nginx can reach the app in the internal Docker network).
    - **Features:** Handles the PATCH request, updates DB, and triggers the UDP broadcast.

3.  **PostgreSQL (The Memory):**
    - **Role:** Persistent storage.
    - **Data:** Stores User email, last seen timestamp (nanoseconds), IP, and Port.

---

## 3. Deep Dive: Key Technical Decisions

### A. Security: Mutual TLS (mTLS)

- **How it works:** Instead of a password, the client presents a certificate file.
- **The Chain:** You created a **Certificate Authority (CA)** which signed both the Server and Client certificates.
- **Validation:** Nginx checks if the Client's cert was signed by the CA. If yes, it lets the request through.
- **User Identity:** The user's email is embedded in the **Common Name (CN)** field of the certificate.

### B. Networking: UDP Broadcasting

- **Why UDP?** It's "Fire and Forget." We need to announce status to _anyone_ listening without slowing down the main request waiting for ACKs. Perfect for efficient network usage.
- **Implementation:** You implemented a **Singleton `UDPBroadcaster`** class.
  - **Socket Options:** Used `SO_BROADCAST` to allow sending to `255.255.255.255`.
  - **Binary Protocol:** You designed a custom binary format to be compact (Big Endian):
    - `Email Length` (1 byte)
    - `Email` (String)
    - `Timestamp` (8 bytes, Nanoseconds)
    - `IP Length` (1 byte)
    - `IP` (String)
    - `Port` (2 bytes)
  - **Why Binary?** Requirements suggested Protocol Buffers, but a custom `struct` pack is lighter and doesn't require compiling `.proto` files, proving you understand low-level byte manipulation.

### C. Database Design

- **Schema:** `User` table with `email` (PK/Unique), `last_seen_ns` (BigInt), `ip`, `port`.
- **Nanosecond Precision:** You used Python's `time.time_ns()` and Stored it as a BigInteger (Postgres `bigint` fits 64-bit integers, ample for nanoseconds).

---

## 4. Addressing "The Elephant in the Room" (Python vs Java)

**Be prepared for:** _"The requirements asked for Java (Spring Boot) but you used Python. Why?"_

**Possible Defense Strategies:**

1.  **Speed & Robustness:** "Given the 72-hour timeframe, I chose Python to ensure I could deliver a _fully Dockerized, well-documented, and production-ready_ solution including the extra scripts (Task 2) and robust certificate generation. I prioritized a working, correct system architecture over struggling with boilerplate."
2.  **Language Agnostic Design:** "I built this system demonstrating core Backend Engineering concepts: mTLS, TCP/IP handling, Database locking, and Container orchestration. The logic (Middleware extraction, UDP socket binding) is identical in Java. I can walk you through how I would implement the `MTLSAuthenticationMiddleware` as a Spring Boot Filter if you'd like."
3.  **The "Task 2" Script:** "Task 2 explicitly allowed any language (like Rust/Go), and I used Python's `struct` library there. Used Django for consistency across the stack."

**(Note: If you actually applied for a Python role and just pasted the wrong text in the prompt, clarify that immediately!)**

---

## 5. Potential Interview Questions & Answers

**Q: How do you handle malformed packets in your UDP listener?**
**A:** "I use a `try/catch` block. I first check if the packet size is at least the minimum header size (14 bytes). If the internal length fields (like email length) specify a size larger than the remaining packet, I discard it as malformed. This prevents buffer overflow attacks or crashing the listener."

**Q: Why did you terminate TLS at Nginx instead of the Application?**
**A:** "It follows the **Sidecar/Gateway pattern**. Nginx is written in C and highly optimized for cryptography. It simplifies the application code; the app doesn't need to manage keystores or truststores, it just deals with standard HTTP and trusted headers. It also makes certificate rotation easier (reload Nginx without restarting the app)."

**Q: How do you ensure the IP and Port recorded are correct?**
**A:** "Since Nginx proxies the connection, the application sees Nginx's IP. I configured Nginx to pass the `X-Real-IP` and `$remote_port` (mapped to `X-Real-Port`) headers. My application reads these headers instead of the direct socket address."

**Q: What happens if two updates come in at the exact same time for the same user?**
**A:** "Postgres handles the row locking. The `UPDATE` statement is atomic. However, UDP is unordered, so listeners might receive packets out of order. If strict ordering was required on the listener side, I'd include a sequence number, but for 'Last Seen' status, we just trust the timestamp."

**Q: How did you implement the 'client' application's mTLS?**
**A:** "I used Python's `requests` library. I passed the tuple `(cert_path, key_path)` to the `cert` parameter. This performs the TLS handshake using the client's private key to sign the challenge from the server."
