import argparse
import requests
import sys
import os
from pathlib import Path

def main():
    # Resolve paths relative to the script location
    script_dir = Path(__file__).resolve().parent
    default_certs_dir = script_dir.parent / "certs"

    parser = argparse.ArgumentParser(description="QT Assessment mTLS Client")
    parser.add_argument("--url", default="https://localhost:443/api/client", help="Target URL")
    parser.add_argument("--cert", default=str(default_certs_dir / "client.crt"), help="Client Certificate")
    parser.add_argument("--key", default=str(default_certs_dir / "client.key"), help="Client Key")
    parser.add_argument("--ca", default=str(default_certs_dir / "ca.crt"), help="CA Certificate to verify server")
    args = parser.parse_args()

    # Validate paths
    if not os.path.exists(args.cert) or not os.path.exists(args.key):
        print(f"Error: Client certificate or key not found.")
        print(f"Searched: {args.cert}, {args.key}")
        sys.exit(1)

    if not os.path.exists(args.ca):
        print(f"Warning: CA certificate not found at {args.ca}. SSL verification might fail if using self-signed certs.")

    print(f"Connecting to {args.url}...")
    print(f"Using Identity: {args.cert}")

    try:
        # verify=args.ca ensures we trust the server's self-signed cert
        response = requests.patch(
            args.url,
            cert=(args.cert, args.key),
            verify=args.ca
        )

        print(f"Status Code: {response.status_code}")
        if response.status_code == 204:
            print("Success! (204 No Content)")
        else:
            print(f"Response: {response.text}")

    except requests.exceptions.SSLError as e:
        print(f"SSL/TLS Error: {e}")
        print("This often means the Server cert is not trusted by the CA provided, or the Client cert was rejected.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
