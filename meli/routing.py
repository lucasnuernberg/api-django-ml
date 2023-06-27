from django.urls import re_path
from .consumers import NotificacaoConsumer

websocket_urlpatterns = [
    re_path(r'ws/notifications/(?P<user_id>\w+)/$', NotificacaoConsumer.as_asgi()),
]
