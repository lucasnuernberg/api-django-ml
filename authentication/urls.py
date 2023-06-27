from django.urls import path
from .views import VerifyEmail, RegisterUserView, RequestPasswordReset, SetNewPasswordAPIView, PasswordTokenCheckAPI, SendEmailToUsView, SetNewPass, VerifyPassword
from .tokens import CustomTokenObtainPairView, CustomTokenRefreshViewPairView

app_name = 'authentication'

urlpatterns = [
    path(route='register/', view=RegisterUserView.as_view(), name='register_user'),
    path(route='login/', view=CustomTokenObtainPairView.as_view(), name='login'),
    path(route='token/refresh/', view=CustomTokenRefreshViewPairView.as_view(), name='refresh_token'),
    path(route='email-verify/', view=VerifyEmail.as_view(), name="email-verify"),
    path(route='password-verify/', view=VerifyPassword.as_view(), name="password-verify"),
    path(route='request-reset-password/', view=RequestPasswordReset.as_view(), name="request-reset-email"),
    path(route='password-reset/<uidb64>/<token>/', view=PasswordTokenCheckAPI.as_view(), name='password-reset-confirm'),
    path(route='password-reset/', view=SetNewPasswordAPIView.as_view(), name='password-reset'),
    path(route='pass-reset/', view=SetNewPass.as_view(), name='pass-reset'),
    path(route='contact-email/', view=SendEmailToUsView.as_view(), name='contact-email')
 ]
