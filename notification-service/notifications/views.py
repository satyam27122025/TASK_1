import os
import socket
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    nats_url = os.getenv("NATS_URL", "nats://127.0.0.1:4222")
    nats_status = "disconnected"
    try:
        cleaned = nats_url.replace("nats://", "")
        if "@" in cleaned:
            cleaned = cleaned.split("@")[1]
        host = cleaned.split(":")[0]
        port = int(cleaned.split(":")[1]) if ":" in cleaned else 4222

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect((host, port))
        s.close()
        nats_status = "connected"
    except Exception:
        nats_status = "unreachable"

    return Response({
        "status": "ok",
        "service": "notification-service",
        "nats": nats_status
    }, status=status.HTTP_200_OK)
