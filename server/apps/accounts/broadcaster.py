import socket
import struct
import logging

logger = logging.getLogger(__name__)

class UDPBroadcaster:
    """
    Singleton UDP Broadcaster.
    Binds to a fixed port (default 6666) and broadcasts packets to a target port (default 6667).
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UDPBroadcaster, cls).__new__(cls)
            cls._instance._sock = None
            cls._instance._initialized = False
        return cls._instance

    def initialize(self, bind_port=6666, target_port=6667):
        if self._initialized:
            return

        self.target_port = target_port

        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # Re-use address to avoid conflicts during restarts
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind to specific port as requested "Send from port 6666"
            self._sock.bind(('', bind_port))

            self._initialized = True
            logger.info(f"UDP Broadcaster initialized. Bound to {bind_port}, targeting {target_port}")
        except Exception as e:
            logger.error(f"Failed to initialize UDP Broadcaster: {e}")
            self._sock = None

    def send(self, email: str, last_seen_ns: int, ip: str, port: int):
        """
        Broadcasts the binary payload.
        Format (Big Endian):
        - Email Length (1 byte)
        - Email (UTF-8 bytes)
        - Last Seen Nanoseconds (8 bytes / Q)
        - IP Length (1 byte)
        - IP String (UTF-8 bytes)  <-- Storing as string is simpler than packing 4/16 bytes for IPv4/6 mix
        - Port (2 bytes / H)
        """
        if not self._sock:
            # Try to re-init if not running? Or just log error.
            # For this assessment, we log.
            logger.error("UDP Broadcaster not initialized. Skipping broadcast.")
            return

        try:
            email_bytes = email.encode('utf-8')
            ip_bytes = ip.encode('utf-8')

            # Struct Format:
            # B = unsigned char (1 byte)
            # {len}s = string of length
            # Q = unsigned long long (8 bytes)
            # H = unsigned short (2 bytes)

            fmt = f'>B{len(email_bytes)}sQB{len(ip_bytes)}sH'

            payload = struct.pack(
                fmt,
                len(email_bytes),
                email_bytes,
                last_seen_ns,
                len(ip_bytes),
                ip_bytes,
                port
            )

            # Broadcast to 255.255.255.255
            self._sock.sendto(payload, ('<broadcast>', self.target_port))
            logger.debug(f"Broadcast sent for {email}")

        except Exception as e:
            logger.error(f"Broadcast failed: {e}")

# Global instance
broadcaster = UDPBroadcaster()
