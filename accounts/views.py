from rest_framework import generics, permissions
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .serializers import UserSerializer

class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(exclude=True)
class ProtectedHelloView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response({'message': f'Hello, {request.user.username}'})
