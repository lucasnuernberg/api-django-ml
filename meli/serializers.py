from rest_framework import serializers
from django.contrib.auth.models import Group
from authentication.models import CustomUser
from .models import ContaML, TokenMl, RespostaPadrao, Device, Notification
from custom_errors.exceptions import CustomValidationErrorsDict

class CustomErrorsMixin:
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
                    elif 'em branco' in error:
                        custom_errors.add(field, f'O campo {field} não pode ser em branco')
                    elif 'ser nulo' in error:
                        custom_errors.add(field, f'O campo {field} não pode ser nulo')
                    
                    else:
                        custom_errors.add(field, str(error))

            raise serializers.ValidationError(custom_errors)

class CustomUserSerializer(CustomErrorsMixin, serializers.ModelSerializer):

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'group', 'profile_picture']
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance

class ContaMLSerializer(CustomErrorsMixin, serializers.ModelSerializer):

    class Meta:
        model = ContaML
        fields = ['id', 'nickname',
                  'user', 'seller_id',
                  'data_criacao', 'link_img',
                  'permalink', 'nivel']

class TokenMlSerializer(CustomErrorsMixin, serializers.ModelSerializer):
    class Meta:
        model = TokenMl
        fields = '__all__'

class RespostaPadraoSerializer(CustomErrorsMixin, serializers.ModelSerializer):
    class Meta:
        model = RespostaPadrao
        fields = '__all__'
        read_only_fields = ('user',)

class GroupSerializer(CustomErrorsMixin, serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

class AuthMlSerializer(CustomErrorsMixin, serializers.Serializer): 
    code = serializers.CharField(required=True)

class PerguntasSerializer(CustomErrorsMixin, serializers.Serializer):

    STATUS_CHOICES = (
        ('ANSWERED', 'answered'),
        ('UNANSWERED', 'unanswered'),
    )
    
    status = serializers.ChoiceField(choices=STATUS_CHOICES, required=False)
    offset = serializers.IntegerField(required=False)
    item = serializers.CharField(required=False)
    timezone = serializers.CharField(required=False)

class PerguntasAnterioresSerializer(CustomErrorsMixin, serializers.Serializer):

    question_id = serializers.IntegerField(required=True)
    timezone = serializers.CharField(required=False)

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as e:
            custom_errors = CustomValidationErrorsDict()

            for field, errors in e.detail.items():
                for error in errors:
                    if field == 'status' and 'em branco' in error:
                        custom_errors.add(field, 'O campo status não pode ser em branco')
                    elif field == 'status' and 'ser nulo' in error:
                        custom_errors.add(field, 'O campo status não pode ser nulo')
                    else:
                        custom_errors.add(field, str(error))

            raise serializers.ValidationError(custom_errors)

class ResponderPerguntasSerializer(CustomErrorsMixin, serializers.Serializer):

    question_id = serializers.IntegerField(required=True)
    text = serializers.CharField(max_length=2000)

    class Meta:
        fields = '__all__'

class DeviceSerializer(CustomErrorsMixin, serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'device_token', 'platform', 'created_at']

class NotificationSerializer(CustomErrorsMixin, serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'