import time
from django.views import View
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import User

# Minimal "Service" specific to this assessment
class ClientService:
    @staticmethod
    def update_client_state(user: User, ip_address: str, port: int) -> None:
        """
        Updates the user's state and triggers the broadcast.
        """
        user.last_seen_ns = time.time_ns()
        user.ip_address = ip_address
        user.port = port
        user.save()

        if user.ip_address: # Ensure we have data to send
             from .broadcaster import broadcaster
             broadcaster.send(user.email, user.last_seen_ns, user.ip_address, user.port)


@method_decorator(csrf_exempt, name='dispatch')
class ClientUpdateView(View):
    """
    Handles the empty HTTP PATCH request.
    Expects mTLS authentication headers.
    """

    def patch(self, request, *args, **kwargs):
        # 1. Validation Logic

        # Check for middleware errors first (SoC)
        mtls_error = getattr(request, 'mtls_error', None)
        cn = request.headers.get('X-Subject-CN')

        # Case: No Header (Nginx bypass or config error) -> 401 Unauthorized
        if not cn:
             return HttpResponse(status=401, content="Missing Client Certificate Header")

        # Case: Invalid CN Format -> 400 Bad Request
        if mtls_error == "Invalid CN format":
             return HttpResponse(status=400, content="CN must be a valid email address")

        # Case: User Not Found -> 403 Forbidden
        if mtls_error == "User not found" or not request.user.is_authenticated:
            return HttpResponse(status=403, content="User unknown")

        # 2. Extract Network Info (IP/Port)
        # In a real proxy setup, we look at X-Real-IP.
        # Port is tricky; usually the source port of the connection to Nginx is lost unless
        # Nginx passes it via a custom header (e.g. X-Real-Port).
        # Standard configs often miss this. We will assume we need to extract what we can.
        # Spec says: "Update port". This implies the CLIENT'S source port.
        # Since we are behind Nginx, we need Nginx to send it.
        # We will assume `X-Real-IP` is present.
        # We will assume a hypothetical `X-Real-Port` or defaulted to 0 if missing.

        ip_addr = request.headers.get('X-Real-IP', request.META.get('REMOTE_ADDR'))
        try:
             port = int(request.headers.get('X-Real-Port', '0'))
        except ValueError:
             port = 0

        # 3. Update User
        ClientService.update_client_state(request.user, ip_addr, port)

        return HttpResponse(status=204) # 204 No Content for successful PATCH
