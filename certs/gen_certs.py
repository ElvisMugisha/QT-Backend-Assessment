import subprocess
import sys
import os

def run_command(cmd):
    """Run a shell command and check for errors."""
    print(f"Running: {cmd}")
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        sys.exit(1)

def main():
    target_dir = "."
    if os.path.basename(os.getcwd()) != "certs":
        if os.path.exists("certs"):
            target_dir = "certs"
        else:
            print("Error: Could not find 'certs' directory.")
            sys.exit(1)

    print(f"Generating certificates in '{target_dir}'...")

    # CA Config & Generation
    ca_cnf = os.path.join(target_dir, "ca.cnf")
    with open(ca_cnf, "w") as f:
        f.write("""
            [req]
            distinguished_name = req_distinguished_name
            x509_extensions = v3_ca
            prompt = no

            [req_distinguished_name]
            CN = QT_Assessment_CA

            [v3_ca]
            basicConstraints = critical,CA:TRUE
            keyUsage = critical, digitalSignature, cRLSign, keyCertSign
        """)

    run_command(f'openssl req -x509 -newkey rsa:2048 -nodes -keyout {target_dir}/ca.key -out {target_dir}/ca.crt -days 365 -config {ca_cnf}')


    # Server Config & Generation (With SAN)
    server_cnf = os.path.join(target_dir, "server.cnf")
    with open(server_cnf, "w") as f:
        f.write("""
            [req]
            distinguished_name = req_distinguished_name
            req_extensions = v3_req
            prompt = no

            [req_distinguished_name]
            CN = localhost

            [v3_req]
            basicConstraints = CA:FALSE
            keyUsage = critical, digitalSignature, keyEncipherment
            extendedKeyUsage = serverAuth
            subjectAltName = @alt_names

            [alt_names]
            DNS.1 = localhost
            IP.1 = 127.0.0.1
        """)

    run_command(f'openssl genrsa -out {target_dir}/server.key 2048')
    run_command(f'openssl req -new -key {target_dir}/server.key -out {target_dir}/server.csr -config {server_cnf}')
    # Note: When signing with CA, we must explicitly include extensions from the config or an extfile
    run_command(f'openssl x509 -req -in {target_dir}/server.csr -CA {target_dir}/ca.crt -CAkey {target_dir}/ca.key -CAcreateserial -out {target_dir}/server.crt -days 365 -sha256 -extfile {server_cnf} -extensions v3_req')


    # Client Config & Generation
    client_cnf = os.path.join(target_dir, "client.cnf")
    with open(client_cnf, "w") as f:
        f.write("""
            [req]
            distinguished_name = req_distinguished_name
            req_extensions = v3_req
            prompt = no

            [req_distinguished_name]
            CN = valid_user@qt-test.com

            [v3_req]
            basicConstraints = CA:FALSE
            keyUsage = critical, digitalSignature, keyEncipherment
            extendedKeyUsage = clientAuth
        """)

    run_command(f'openssl genrsa -out {target_dir}/client.key 2048')
    run_command(f'openssl req -new -key {target_dir}/client.key -out {target_dir}/client.csr -config {client_cnf}')
    run_command(f'openssl x509 -req -in {target_dir}/client.csr -CA {target_dir}/ca.crt -CAkey {target_dir}/ca.key -CAcreateserial -out {target_dir}/client.crt -days 365 -sha256 -extfile {client_cnf} -extensions v3_req')

    # Invalid Client
    run_command(f'openssl genrsa -out {target_dir}/bad_client.key 2048')
    run_command(f'openssl req -new -key {target_dir}/bad_client.key -out {target_dir}/bad_client.csr -subj "/CN=not_an_email"')
    run_command(f'openssl x509 -req -in {target_dir}/bad_client.csr -CA {target_dir}/ca.crt -CAkey {target_dir}/ca.key -CAcreateserial -out {target_dir}/bad_client.crt -days 365 -sha256')

    # Cleanup
    for f in ["server.csr", "client.csr", "bad_client.csr", "ca.cnf", "server.cnf", "client.cnf"]:
        path = os.path.join(target_dir, f)
        if os.path.exists(path):
            os.remove(path)

    print("\nCertificate generation complete (v3 SAN compliant).")

if __name__ == "__main__":
    main()
