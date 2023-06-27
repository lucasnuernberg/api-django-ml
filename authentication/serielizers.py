from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from .models import CustomUser
from custom_errors.exceptions import CustomValidationErrorsDict
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

class RegisterUserSerializer(serializers.ModelSerializer):
    
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(
            required=True,
            validators=[UniqueValidator(queryset=CustomUser.objects.all())]
            )

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    country = serializers.CharField(required=True)
    address_number = serializers.IntegerField(required=True)
    cep = serializers.CharField(required=True)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'password', 'password2', 'email', 'country', 'address_number', 'cep')

    def create(self, validated_data):
        email = validated_data['email']
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        password = validated_data['password']

        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'is_active': False,
            },
            address_number=validated_data['address_number'],
            cep=validated_data['cep'],
            country=validated_data['country']
        )

        if not created:
            raise serializers.ValidationError({"email": "Este email já está em uso"})

        user.set_password(password)
        user.save()

        return user

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as e:
            custom_errors = CustomValidationErrorsDict()

            for field, errors in e.detail.items():
                for error in errors:
                    if field == 'first_name' and 'em branco' in error:
                        custom_errors.add(field, 'O campo nome não pode ser em branco')
                    elif field == 'first_name' and 'ser nulo' in error:
                        custom_errors.add(field, 'O campo nome não pode ser nulo')
                    elif field == 'last_name' and 'em branco' in error:
                        custom_errors.add(field, 'O campo sobrenome não pode ser em branco')
                    elif field == 'last_name' and 'ser nulo' in error:
                        custom_errors.add(field, 'O campo sobrenome não pode ser nulo')
                    elif field == 'email' and 'em branco' in error:
                        custom_errors.add(field, 'O campo email não pode ser em branco')
                    elif field == 'email' and 'ser nulo' in error:
                        custom_errors.add(field, 'O campo email não pode ser nulo')
                    elif field == 'password' and 'em branco' in error:
                        custom_errors.add(field, 'O campo senha não pode ser em branco')
                    elif field == 'password' and 'ser nulo' in error:
                        custom_errors.add(field, 'O campo senha não pode ser nulo')
                    elif field == 'address_number' and 'em branco' in error:
                        custom_errors.add(field, 'O campo número não pode ser em branco')
                    elif field == 'address_number' and 'ser nulo' in error:
                        custom_errors.add(field, 'O campo número não pode ser nulo')
                    elif field == 'cep' and 'em branco' in error:
                        custom_errors.add(field, 'O campo cep não pode ser em branco')
                    elif field == 'cep' and 'ser nulo' in error:
                        custom_errors.add(field, 'O campo cep não pode ser nulo')
                    elif field == 'country' and 'em branco' in error:
                        custom_errors.add(field, 'O campo país não pode ser em branco')
                    elif field == 'country' and 'ser nulo' in error:
                        custom_errors.add(field, 'O campo país não pode ser nulo')

                    else:
                        custom_errors.add(field, str(error))

            raise serializers.ValidationError(custom_errors)

class CustomTokenRefreshSerializer(TokenRefreshSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh_token = RefreshToken(attrs['refresh'])
        payload = refresh_token.payload
        
        user = CustomUser.objects.get(id=payload['user_id'])

        data['first_name'] = user.first_name
        data['profile_picture'] = user.profile_picture

        return data

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as e:
            custom_errors = CustomValidationErrorsDict()

            for field, errors in e.detail.items():
                for error in errors:
                    custom_errors.add(field, str(error))

            raise serializers.ValidationError(custom_errors)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        attrs[self.username_field] = attrs.get(self.username_field).lower().strip()
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        
        user = self.user
        data['first_name'] = user.first_name
        data['profile_picture'] = user.profile_picture

        return data

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as e:
            custom_errors = CustomValidationErrorsDict()

            for field, errors in e.detail.items():
                for error in errors:
                    if field == 'email' and 'branco' in error:
                        custom_errors.add(field, 'O campo email não pode ser em branco')
                    elif field == 'email' and 'obrigatório' in error:
                        custom_errors.add(field, 'O campo email é obrigatório')
                    elif field == 'password' and 'obrigatório' in error:
                        custom_errors.add(field, 'O campo senha é obrigatório')
                    elif field == 'password' and 'obrigatório' in error:
                        custom_errors.add(field, 'O campo senha é obrigatório')

                    else:
                        custom_errors.add(field, str(error))

            raise serializers.ValidationError(custom_errors)

class EmailVerificationSerializer(serializers.ModelSerializer):
    
    token = serializers.CharField(max_length=555)
    class Meta:
        model = CustomUser
        fields = ['email']

class VerifyPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=500, required=True)
    class Meta:
        fields = []

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as e:
            custom_errors = CustomValidationErrorsDict()

            for field, errors in e.detail.items():
                for error in errors:
                    if field == 'password' and 'em branco' in error:
                        custom_errors.add(field, 'O campo senha não pode ser em branco')
                    elif field == 'password' and 'ser nulo' in error:
                        custom_errors.add(field, 'O campo senha não pode ser nulo')
                    else:
                        custom_errors.add(field, str(error))

            raise serializers.ValidationError(custom_errors)

class SetnewPassSerializer(serializers.Serializer):
    old_pass = serializers.CharField(max_length=500, required=True)
    new_pass = serializers.CharField(max_length=500, required=True, validators=[validate_password])

    class Meta:
        fields = []

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as e:
            custom_errors = CustomValidationErrorsDict()

            for field, errors in e.detail.items():
                for error in errors:
                    if field == 'old_pass' and 'em branco' in error:
                        custom_errors.add(field, 'O campo old_pass não pode ser em branco')
                    elif field == 'old_pass' and 'ser nulo' in error:
                        custom_errors.add(field, 'O campo old_pass não pode ser nulo')
                    elif field == 'new_pass' and 'em branco' in error:
                        custom_errors.add(field, 'O campo new_pass não pode ser em branco')
                    elif field == 'new_pass' and 'ser nulo' in error:
                        custom_errors.add(field, 'O campo new_pass não pode ser nulo')
                    else:
                        custom_errors.add(field, str(error))

            raise serializers.ValidationError(custom_errors)

class ResetPasswordRequestSerializer(serializers.Serializer):
    redirect_url = serializers.CharField(max_length=500, required=True)
    email = serializers.CharField(max_length=500, required=True)

    class Meta:
        fields = ['redirect_url', 'email']

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as e:
            custom_errors = CustomValidationErrorsDict()

            for field, errors in e.detail.items():
                for error in errors:
                    if field == 'redirect_url' and 'em branco' in error:
                        custom_errors.add(field, 'O campo redirect_url não pode ser em branco')
                    elif field == 'redirect_url' and 'ser nulo' in error:
                        custom_errors.add(field, 'O campo redirect_url não pode ser nulo')
                    elif field == 'email' and 'em branco' in error:
                        custom_errors.add(field, 'O campo email não pode ser em branco')
                    elif field == 'email' and 'ser nulo' in error:
                        custom_errors.add(field, 'O campo email não pode ser nulo')
                    else:
                        custom_errors.add(field, str(error))

            raise serializers.ValidationError(custom_errors)

class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(
        min_length=1, write_only=True)
    uidb64 = serializers.CharField(
        min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            id = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('O link é inválido', 401)

            user.set_password(password)
            user.save()

            return (user)
        
        except Exception as e:
            raise AuthenticationFailed('O link é inválido', 401)

class SendEmailToUsSerializer(serializers.Serializer):
    
    name = serializers.CharField(required=True)
    company_name = serializers.CharField(required=False)
    email = serializers.EmailField(required=True)
    message = serializers.CharField(required=True)

    class Meta:
        fields = ['name', 'email', 'company_name', 'message']
