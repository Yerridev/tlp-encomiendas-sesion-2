from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate

from api.throttles import LoginRateThrottle


# ── JWT con datos del empleado en el payload ───────────────────────────

class EncomiendaTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email']    = user.email
        try:
            emp = user.empleado
            token['empleado_id']  = emp.id
            token['empleado_cod'] = emp.codigo
            token['cargo']        = emp.cargo
        except Exception:
            pass
        return token


class EncomiendaTokenView(TokenObtainPairView):
    serializer_class = EncomiendaTokenSerializer
    throttle_classes = [LoginRateThrottle]


# ── Login con HttpOnly Cookies ─────────────────────────────────────────

class LoginCookieView(APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user     = authenticate(username=username, password=password)

        if not user:
            return Response({'error': 'Credenciales inválidas.'}, status=401)

        refresh  = RefreshToken.for_user(user)
        response = Response({'message': 'Login exitoso.'})
        response.set_cookie(
            key='access_token', value=str(refresh.access_token),
            httponly=True, secure=True, samesite='Lax', max_age=3600,
        )
        response.set_cookie(
            key='refresh_token', value=str(refresh),
            httponly=True, secure=True, samesite='Lax', max_age=604800,
        )
        return response


class LogoutCookieView(APIView):
    def post(self, request):
        response = Response({'message': 'Logout exitoso.'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
