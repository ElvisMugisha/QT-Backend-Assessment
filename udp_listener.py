import socket
import struct
import argparse
import sys
import datetime

def run_listener(port):
    """
    Listens for UDP broadcast packets and decodes them.
    Payload Format (Big Endian):
    - Email Length (1 byte, B)
    - Email (N bytes, s)
    - Last Seen (8 bytes, Q)
    - IP Length (1 byte, B)
    - IP (M bytes, s)
    - Port (2 bytes, H)
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # Binding to 0.0.0.0 allows receiving broadcasts
        sock.bind(('0.0.0.0', port))
        print(f"Listening for UDP Broadcasts on port {port}...")
    except Exception as e:
        print(f"Error binding to port {port}: {e}")
        sys.exit(1)

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            # Minimal size check: 1(len) + 1(email) + 8(time) + 1(len) + 1(ip) + 2(port) = 14 bytes min
            if len(data) < 14:
                print(f"Received malformed packet (too short) from {addr}")
                continue

            offset = 0

            # 1. Email Length
            email_len = struct.unpack_from('>B', data, offset)[0]
            offset += 1

            if len(data) < offset + email_len:
                print("Malformed packet: Email length mismatch")
                continue

            # 2. Email
            email_bytes = struct.unpack_from(f'>{email_len}s', data, offset)[0]
            email = email_bytes.decode('utf-8')
            offset += email_len

            # 3. Last Seen
            last_seen_ns = struct.unpack_from('>Q', data, offset)[0]
            offset += 8

            # 4. IP Length
            ip_len = struct.unpack_from('>B', data, offset)[0]
            offset += 1

            # 5. IP
            ip_bytes = struct.unpack_from(f'>{ip_len}s', data, offset)[0]
            ip_str = ip_bytes.decode('utf-8')
            offset += ip_len

            # 6. Port
            client_port = struct.unpack_from('>H', data, offset)[0]

            # Pretty Print
            timestamp = datetime.datetime.fromtimestamp(last_seen_ns / 1e9)
            print("-" * 40)
            print(f"Source Packet: {addr}")
            print(f"User Email   : {email}")
            print(f"Last Seen    : {timestamp} ({last_seen_ns})")
            print(f"Client IP    : {ip_str}")
            print(f"Client Port  : {client_port}")
            print("-" * 40)

        except KeyboardInterrupt:
            print("\nStopping listener.")
            break
        except Exception as e:
            print(f"Error processing packet: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UDP Broadcast Listener")
    parser.add_argument("--port", type=int, default=6667, help="Port to listen on (default: 6667)")
    args = parser.parse_args()

    run_listener(args.port)
