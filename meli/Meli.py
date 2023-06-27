import requests
from dotenv import load_dotenv
from rest_framework.exceptions import ValidationError
from os import getenv, path
from datetime import timedelta
from django.utils import timezone
from redis import ConnectionError, Redis
from os import getenv

def connect_redis():
    
    load_dotenv(path.join(path.dirname(__file__), '..', 'config', '.env'))
    REDIS_URL = getenv('REDIS_URL')
    if not REDIS_URL:
        raise ValueError("Missing REDIS_URL environment variable")
    redis_client = Redis.from_url(REDIS_URL)
    return redis_client


class Meli:
    def __init__(self, access_token=''):
        self.access_token = access_token
        self.base_url = 'https://api.mercadolibre.com'

    def send_request(self, url, method, data={}, params={}):
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        
        if method == 'GET':
            response = requests.get(f'{self.base_url}/{url}', headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(f'{self.base_url}/{url}', headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(f'{self.base_url}/{url}', headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(f'{self.base_url}/{url}', headers=headers)
        else:
            raise ValueError("Método HTTP inválido")


        if response.status_code not in (200, 201):
            if response.json().get('message', '') == 'invalid_token':
                raise ValidationError(detail="Invalid token")              
            else:
                raise ValidationError(detail=response.json())
        return response.json()

    def send_request_without_auth(self, url, method, data={}, params={}):

        if method == 'GET':
            response = requests.get(f'{self.base_url}/{url}', params=params)
        elif method == 'POST':
            response = requests.post(f'{self.base_url}/{url}', json=data)
        elif method == 'PUT':
            response = requests.put(f'{self.base_url}/{url}', json=data)
        elif method == 'DELETE':
            response = requests.delete(f'{self.base_url}/{url}')
        else:
            raise ValueError("Método HTTP inválido")


        if response.status_code not in (200, 201):
            if response.json().get('message', '') == 'invalid_token':
                raise ValidationError(detail="Invalid token")              
            else:
                raise ValidationError(detail=response.json())
        return response.json()

    def get_refresh_token(self, type='refresh_token', json={}):

        load_dotenv(path.join(path.dirname(__file__), '..', 'config', '.env'))

        if type == 'refresh_token':
            body_json ={
                "grant_type": "refresh_token",
                "client_id": getenv('APP_ML_ID'),
                "client_secret": getenv('SECRECT_ML'),
                "refresh_token":  json.get('refresh_token')
            }
            
        elif type == "authorization_code":
            body_json =  {
                "grant_type": "authorization_code",
                "client_id": getenv('APP_ML_ID'),
                "client_secret": getenv('SECRECT_ML'),
                "code": json.get('code'),
                "redirect_uri": getenv('REDIRECT_URI_ML'),
            }

        response = requests.post(f'{self.base_url}/oauth/token', body_json)

        if response.status_code not in (200, 201):
            raise ValidationError(detail=response.json())
              
        return {
            'data': response.json(),
            'expires_at': timezone.now() + timezone.timedelta(seconds=response.json()['expires_in'])
        }

    def check_and_update_token(self, conta):
        now = timezone.now()
        redis_client = connect_redis()
        token_key = f"token:{conta.id}"

        redis_available = True
        try:
            redis_client.ping()
        except ConnectionError:
            redis_available = False

        if redis_available:
            if not redis_client.exists(token_key):
                try:
                    retorno_access = self.get_refresh_token(type='refresh_token', json={
                        "refresh_token": conta.token.refresh_token
                    })

                    access_token = retorno_access['data']["access_token"]
                    token = conta.token
                    token.access_token = access_token
                    token.access_token_expires_at = retorno_access['expires_at']
                    token.save()

                    # Salvar o token no Redis com o tempo de expiração
                    redis_client.set(token_key, access_token, ex=int(retorno_access['data']['expires_in']))

                    # Atualize o access_token da instância atual de Meli
                    self.access_token = access_token

                except ValidationError as e:
                    raise ValidationError(detail=e.detail)
            else:
                self.access_token = redis_client.get(token_key).decode('utf-8')
        else:
            if conta.token.access_token_expires_at is None or now >= conta.token.access_token_expires_at - timedelta(minutes=5):

                try:
                    retorno_access = self.get_refresh_token(type='refresh_token', json={
                        "refresh_token": conta.token.refresh_token
                    })

                    access_token = retorno_access['data']["access_token"]
                    token = conta.token
                    token.access_token = access_token
                    token.access_token_expires_at = retorno_access['expires_at']
                    token.save()

                    # Atualize o access_token da instância atual de Meli
                    self.access_token = access_token

                except ValidationError as e:
                    raise ValidationError(detail=e.detail)
            else:
                self.access_token = conta.token.access_token
