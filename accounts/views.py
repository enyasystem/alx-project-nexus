from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from .serializers import UserSerializer, PasswordResetRequestSerializer, SetNewPasswordSerializer
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        # create inactive user and send verification email
        user = serializer.save()
        user.is_active = False
        user.save()

        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verify_link = f"{self.request.build_absolute_uri('/')}api/auth/verify-email/?uid={uid}&token={token}"
        context = {'user': user, 'verify_link': verify_link}
        subject = 'Verify your email'
        from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None
        text_body = render_to_string('accounts/verify_email.txt', context)
        html_body = render_to_string('accounts/verify_email.html', context)
        msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=[user.email])
        msg.attach_alternative(html_body, 'text/html')
        try:
            msg.send(fail_silently=False)
        except Exception:
            pass


class VerifyEmailView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        uid = request.GET.get('uid')
        token = request.GET.get('token')
        if not uid or not token:
            return Response({'detail': 'Missing uid or token.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            uid_decoded = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_decoded)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': 'Invalid uid/token.'}, status=status.HTTP_400_BAD_REQUEST)
        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = True
        user.save()
        return Response({'detail': 'Email verified. You can now log in.'}, status=status.HTTP_200_OK)


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # don't reveal whether email exists
            return Response({'detail': 'If an account with that email exists, you will receive reset instructions.'}, status=status.HTTP_200_OK)
        token = PasswordResetTokenGenerator().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{request.build_absolute_uri('/')}api/auth/password-reset-confirm/?uid={uid}&token={token}"

        # Render email templates (plain text + HTML)
        context = {
            'user': user,
            'reset_link': reset_link,
        }
        subject = 'Password reset'
        from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None
        text_body = render_to_string('accounts/password_reset_email.txt', context)
        html_body = render_to_string('accounts/password_reset_email.html', context)

        # Send multi-part email
        msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=[email])
        msg.attach_alternative(html_body, 'text/html')
        try:
            msg.send(fail_silently=False)
        except Exception:
            # fallback: don't raise; keep response generic
            pass
        return Response({'detail': 'If an account with that email exists, you will receive reset instructions.'}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        try:
            uid_decoded = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid_decoded)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': 'Invalid uid/token.'}, status=status.HTTP_400_BAD_REQUEST)
        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password has been reset.'}, status=status.HTTP_200_OK)


class LockoutTokenObtainPairView(TokenObtainPairView):
    """Wrap TokenObtainPairView to track failed attempts and lockout via cache."""
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        identifier = request.data.get('username') or request.data.get('email') or request.data.get('username')
        cache_key = f'auth:failed:{identifier}'
        threshold = getattr(settings, 'ACCOUNT_LOCKOUT_THRESHOLD', 5)
        timeout = int(getattr(settings, 'ACCOUNT_LOCKOUT_TIMEOUT', 300))
        failures = cache.get(cache_key, 0) or 0
        if failures >= threshold:
            return Response({'detail': 'Account locked due to too many failed login attempts. Try again later.'}, status=403)
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            # increment failure count
            cache.set(cache_key, failures + 1, timeout)
            raise
        # success — clear failures
        cache.delete(cache_key)
        return Response(serializer.validated_data, status=200)


@extend_schema(exclude=True)
class ProtectedHelloView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response({'message': f'Hello, {request.user.username}'})
\n