from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from .models import CustomUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import smart_str, smart_bytes, DjangoUnicodeDecodeError
from django.urls import reverse
from .utils import Util
from .serielizers import RegisterUserSerializer, EmailVerificationSerializer, ResetPasswordRequestSerializer, SetNewPasswordSerializer, SendEmailToUsSerializer, SetnewPassSerializer, VerifyPasswordSerializer
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from meli.serializers import CustomUserSerializer
from dotenv import load_dotenv
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth.hashers import check_password
from os import getenv, path
import jwt


class RegisterUserView(generics.GenericAPIView):
    
    serializer_class = RegisterUserSerializer
    
    def post(self, request):
        load_dotenv(path.join(path.dirname(__file__), '..', 'config', '.env'))
        user = request.data
        serializer = self.serializer_class(data=user)
        if serializer.is_valid(raise_exception=True):
            if request.data['password'] != request.data['password2']:

                return Response(data={"password": "As senhas não são iguais"}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
        
        user_data = serializer.data        
        user = CustomUser.objects.get(email=user_data['email'])        
        token = RefreshToken.for_user(user=user).access_token  
        current_site = get_current_site(request).domain
        
        relativeLink = reverse('authentication:email-verify')
        
        absurl = f'{getenv("HTTP_PRODUCTION")}://{current_site}{relativeLink}?token={token}'

        email_body = f'''
        <div>
        <div style="
        background-size: cover;
        background: #F1F3F2;
        padding: 24px;
        ">
        <div style="
            width: 500px;
            margin: auto;
            background: white;
            border-radius: 32px;
            padding: 24px 0;
        ">
            <img src="https://storage.googleapis.com/bananahub/lemon/logo-lemon.jpg" alt="Logo Lemon" style="
                margin: 0 auto;
                display: block;
                width: 262px;
                height: 67px;
            " />
            <div style="
                width: 328px;
                margin: 0 auto;
            ">
            <h3 style="
                color:#367CFF;
                margin: 40px 0 16px;
                text-align: center;
            ">
                Confirmação de e-mail
            </h3>
            <p style="
                text-align: center;
            ">
                Olá {user.first_name}! Para confirmar seu cadastro no Lemon clique no botão abaixo:
            </p>
            </div>
            <div
                style="
                margin: 24px auto;
                width: 328px;
            ">
            <a href="{absurl}" target="__blank" style="
                max-width: 328px;
                width: 100%;
                text-align: center;
                cursor: pointer;
                background: #367CFF;
                border: none;
                color:white;
                max-width: 328px;
                display: block;
                width: 100%;
                height: 40px;
                border-radius: 4px;
                text-decoration: none;
                line-height: 40px;
            ">
                Confirmar
            </a>
            <br>
            </div>
        </div>
        </div>
        '''
        email_data = {'email_body': email_body, 'to_email': user.email,
                'email_subject': 'Verifique o seu Email'}
        
        Util.send_email(data=email_data)
        
        return Response(user_data, status=status.HTTP_201_CREATED)

class UpdateUserView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomUserSerializer
    queryset = CustomUser.objects.all()

    def get_object(self):
        return self.request.user

    def update(self, request):
        load_dotenv(path.join(path.dirname(__file__), '..', 'config', '.env'))
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        email_changed = 'email' in request.data and user.email != request.data['email']
        
        if email_changed:
            email = request.data['email']
            token = RefreshToken.for_user(user=user).access_token
            current_site = get_current_site(request).domain
            relative_link = reverse('meli:verify-email', kwargs={'email': email})
            absurl = f'{getenv("HTTP_PRODUCTION")}://{current_site}{relative_link}?token={token}'
            email_body = f'''
            <div>
            <div style="
            background-size: cover;
            background: #F1F3F2;
            padding: 24px;
            ">
            <div style="
                width: 500px;
                margin: auto;
                background: white;
                border-radius: 32px;
                padding: 24px 0;
            ">
                <img src="https://storage.googleapis.com/bananahub/lemon/logo-lemon.jpg" alt="Logo Lemon" style="
                    margin: 0 auto;
                    display: block;
                    width: 262px;
                    height: 67px;
                " />
                <div style="
                    width: 328px;
                    margin: 0 auto;
                ">
                <h3 style="
                    color:#367CFF;
                    margin: 40px 0 16px;
                    text-align: center;
                ">
                    Confirmação de e-mail
                </h3>
                <p style="
                    text-align: center;
                ">
                    Olá {user.first_name} clique no botão abaixo para verificar o seu novo email:
                </p>
                </div>
                <div
                    style="
                    margin: 24px auto;
                    width: 328px;
                ">
                <a href="{absurl}" target="__blank" style="
                    max-width: 328px;
                    width: 100%;
                    text-align: center;
                    cursor: pointer;
                    background: #367CFF;
                    border: none;
                    color:white;
                    max-width: 328px;
                    display: block;
                    width: 100%;
                    height: 40px;
                    border-radius: 4px;
                    text-decoration: none;
                    line-height: 40px;
                ">
                    Confirmar
                </a>
                <br>
                </div>
            </div>
            </div>
            '''

            email_data = {
                'email_body': email_body,
                'to_email': email,
                'email_subject': 'Verifique o seu novo email',
            }
            Util.send_email(data=email_data)
        
        serializer.save()

        if email_changed:
            return Response({'message': f'O email de verificação foi enviado para {email}.'}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.data, status=status.HTTP_200_OK)

class VerifyPassword(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VerifyPasswordSerializer

    @swagger_auto_schema(operation_description="Esta rota verifica a senha do usuário", request_body=VerifyPasswordSerializer)
    def post(self, request):
        self.serializer_class(data=request.data).is_valid(raise_exception=True)
        user = request.user

        is_password_correct = check_password(request.data['password'], user.password)

        if is_password_correct:            
            return Response({"success": "A senha esta correta"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "A senha esta incorreta"}, status=status.HTTP_400_BAD_REQUEST)

class VerifyUpdateEmailView(views.APIView):
    #Arrumar esse furo
    def get(self, request, email):
        token = request.GET.get('token')
        try:
            payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms='HS256')
            user = CustomUser.objects.get(id=payload['user_id'])
            user.email = email
            user.save()            

            return Response({"success": "Email verificado"})         

        except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError, CustomUser.DoesNotExist):
            return Response({'error': 'O token é inválido ou expirou.'}, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer

    def get(self, request):
        load_dotenv(path.join(path.dirname(__file__), '..', 'config', '.env'))
        token = request.GET.get('token')
        try:
            payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms='HS256')

            user = CustomUser.objects.get(id=payload['user_id'])
            if not user.is_active:
                user.is_active = True
                user.save()
            
            return HttpResponseRedirect(getenv('FRONTEND_URL', 'http://localhost:5173'))

            #return Response({'email': 'Successfully activated'}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError as identifier:
            return Response({'error': 'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError as identifier:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)  

class CustomRedirect(HttpResponsePermanentRedirect):

    allowed_schemes = ['http', 'https']

class RequestPasswordReset(generics.GenericAPIView):
    
    serializer_class = ResetPasswordRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data).is_valid(raise_exception=True)

        load_dotenv(path.join(path.dirname(__file__), '..', 'config', '.env'))

        user = get_object_or_404(CustomUser, email=request.data['email'])

        uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
        token = PasswordResetTokenGenerator().make_token(user)
        current_site = get_current_site(request=request).domain
        relativeLink = reverse('authentication:password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
        
        absurl = f'{getenv("HTTP_PRODUCTION")}://{current_site}{relativeLink}'
        email_body = f'''
        <div>
        <div style="
        background-size: cover;
        background: #F1F3F2;
        padding: 24px;
        ">
        <div style="
            width: 500px;
            margin: auto;
            background: white;
            border-radius: 32px;
            padding: 24px 0;
        ">
            <img src="https://storage.googleapis.com/bananahub/lemon/logo-lemon.jpg" alt="Logo Lemon" style="
                margin: 0 auto;
                display: block;
                width: 262px;
                height: 67px;
            " />
            <div style="
                width: 328px;
                margin: 0 auto;
            ">
            <h3 style="
                color:#367CFF;
                margin: 40px 0 16px;
                text-align: center;
            ">
                Redefinição de senha
            </h3>
            <p style="
                text-align: center;
            ">
                Olá {user.first_name} para mudar sua senha clique no botão abaixo:
            </p>
            </div>
            <div
                style="
                margin: 24px auto;
                width: 328px;
            ">
            <a href="{absurl}?redirect_url={request.data["redirect_url"]}" target="__blank" style="
                max-width: 328px;
                width: 100%;
                text-align: center;
                cursor: pointer;
                background: #367CFF;
                border: none;
                color:white;
                max-width: 328px;
                display: block;
                width: 100%;
                height: 40px;
                border-radius: 4px;
                text-decoration: none;
                line-height: 40px;
            ">
                Mudar Senha
            </a>
            <br>
            </div>
        </div>
        </div>
        '''
            
        data =  {'email_body': email_body,
                'to_email': user.email,
                'email_subject': 'Troque sua senha'
                }
        
        Util.send_email(data)
            
        return Response({'success': 'Enviamos um link para o seu email.'}, status=status.HTTP_200_OK)

class SetNewPass(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SetnewPassSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data).is_valid(raise_exception=True)
        user = request.user

        is_password_correct = check_password(request.data['old_pass'], user.password)

        if is_password_correct:
            user.set_password(request.data['new_pass'])
            user.save()
            
            return Response({"success": "Senha alterada"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "A senha antiga esta incorreta"}, status=status.HTTP_400_BAD_REQUEST)

class PasswordTokenCheckAPI(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def get(self, request, uidb64, token):
        load_dotenv(path.join(path.dirname(__file__), '..', 'config', '.env'))
        redirect_url = request.GET.get('redirect_url')

        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                if len(redirect_url) > 3:
                    return CustomRedirect(f'{redirect_url}?token_valid=False')
                else:
                    return CustomRedirect(f"{getenv('FRONTEND_URL', '')}?token_valid=False")

            if redirect_url and len(redirect_url) > 3:
                return CustomRedirect(f'{redirect_url}?token_valid=True&message=Credentials Valid&uidb64={uidb64}&token={token}')
            else:
                return CustomRedirect(f"{getenv('FRONTEND_URL', '')}?token_valid=False")

        except DjangoUnicodeDecodeError as identifier:
            try:
                if not PasswordResetTokenGenerator().check_token(user):
                    return CustomRedirect(f'{redirect_url}?token_valid=False')
                    
            except UnboundLocalError as e:
                return Response({'error': 'Token is not valid, please request a new one'}, status=status.HTTP_400_BAD_REQUEST)

class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'success': True, 'message': 'Password reset success'}, status=status.HTTP_200_OK)

class SendEmailToUsView(generics.GenericAPIView):
    
    serializer_class = SendEmailToUsSerializer
    
    def post(self, request):
        
        email_list = ['lucasnogoncalves@hotmail.com', 'donavanmarques@gmail.com']
        
        payload = request.data
        serializer = self.serializer_class(data=payload)
        serializer.is_valid(raise_exception=True)
        
        email_body = f'Nome: {payload["name"]}\nEmail: {payload["email"]}\nEmpresa: {payload.get("company_name", "")}\nMessage: {payload["message"]}\n'
        
        for email in email_list:
            
            data = {
                    'email_body': email_body,
                    'to_email': email,
                    'email_subject': 'Contato Lemon'
                }
                
            Util.send_email(data)
            
        return Response({'success': 'Email foi enviado'}, status=status.HTTP_200_OK)
  