from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser

class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        token = scope['query_string'].decode('utf-8').split('=')[1]
        user_id = int(scope['path'].split('/')[-2])
        try:
            UntypedToken(token)
            user = await database_sync_to_async(self.get_user_from_token)(token)
            if user.id == user_id:
                scope['user'] = user
            else:
                scope['user'] = AnonymousUser()
        except (InvalidToken, TokenError):
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)

    @staticmethod
    def get_user_from_token(token):
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated_token)
        return user
