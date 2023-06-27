
import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
from django.conf import settings
from pathlib import Path
import jwt
import requests
import time

def send_push_notification_to_user(user_id, data):
    from .models import Device

    devices = Device.objects.filter(user_id=user_id)

    for device in devices:
        
        if device.platform == "web":
            registration_token = device.device_token

            message = messaging.Message(
                data=data,
                token=registration_token,
            )

            try:
                response = messaging.send(message)
                print('Enviado a notificação para o aparelho:', device.id, response)
            except firebase_admin.exceptions.InvalidArgumentError:
                print(f'Token inválido para o dispositivo: {device.id}')
            except firebase_admin._messaging_utils.UnregisteredError:
                print(f'Token não registrado para o dispositivo: {device.id}')
                device.delete()

        elif device.platform in ['android', 'ios']:
            EXPO_PUSH_ENDPOINT = "https://exp.host/--/api/v2/push/send"
            message = {
                'to': device.device_token,
                "title": "Lemon Hub",
                "body": "Você recebeu uma pergunta",
                "data": data,
                "icon": "https://storage.googleapis.com/bananahub/lemon/logo-lemon.jpg"
            }

            headers = {
                'Content-Type': 'application/json'
            }
            
            try:
                response = requests.post(EXPO_PUSH_ENDPOINT, headers=headers, json=message)
            except Exception as e:
                print(f'Erro ao enviar notificação para o dispositivo: {device.id}', str(e))
                device.delete()

def initialize_firebase():
    relative_path = "config/lemon-hub-firebase-adminsdk-90we1-3123ae8964.json"

    abs_path = Path(settings.BASE_DIR) / relative_path
    cred = credentials.Certificate(str(abs_path))
    firebase_admin.initialize_app(cred)

initialize_firebase()