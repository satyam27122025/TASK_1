import asyncio

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer
from .nats_client import publish_user_created


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response(
        {"status": "ok", "service": "user-service"},
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    user = serializer.save()

    try:
        asyncio.run(publish_user_created(user))
    except Exception as e:
        print(f"Error publishing user created event: {e}")

    return Response(
        {
            "message": "User created successfully",
            "user": UserSerializer(user).data
        },
        status=status.HTTP_201_CREATED
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"error": "Both username and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(
        username=username,
        password=password
    )

    if user is None:
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh)
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile(request):
    return Response(
        UserSerializer(request.user).data
    )