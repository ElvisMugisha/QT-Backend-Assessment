# Certificate Generation

This directory contains scripts to generate Self-Signed Certificates for mTLS testing.

## Prerequisites
- **OpenSSL** must be installed and in your system PATH.

## Usage

1. Run the Python generation script:
   ```bash
   python gen_certs.py
   ```
   Or if you are on Windows and Python is not configured:
   ```cmd
   python gen_certs.py
   ```
   (Ensure you can run `openssl` from your terminal).

2. Output Files:
   - `ca.crt`: The Trust Anchor (Root CA).
   - `server.crt` / `server.key`: Server certificate (CN=localhost).
   - `client.crt` / `client.key`: Valid client certificate (CN=valid_user@qt-test.com).
   - `bad_client.crt` / `bad_client.key`: Invalid client cert (CN=not_an_email).

3. Deployment:
   - These files will be mounted into the Nginx container at `/etc/nginx/certs/`.
