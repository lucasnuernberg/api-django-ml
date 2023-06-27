from django.urls import path
from .views import ContaMlListView, AuthMLAPIView, GroupListView, GroupDetailView, UserToGroupView, ListPerguntasContaView, ResponderPerguntasView, RespostaPadraoListCreateAPIView, RespostaPadraoRetrieveUpdateDestroyView, ContaMlRetrieveUpdateDestroyView, UploadFileView, NotificacoesView, ListaPerguntasAnteriores, ListPerguntasContaView2, DeviceListCreateAPIView, DeviceRetrieveUpdateDestroyView, NotificationsListView, NotificationRetrieveUpdateDestroyView, DeletePerguntaView, MarkNotificationsAsReadView, ContaMlListQuestionsView

from authentication.views import UpdateUserView, VerifyUpdateEmailView
app_name = 'meli'

urlpatterns = [
    path(route='contas/', view=ContaMlListView.as_view(), name='lista_conta_ml'),
    path(route='contas-perguntas/', view=ContaMlListQuestionsView.as_view(), name='lista_conta_ml_perguntas'),
    path(route='perfil/', view=UploadFileView.as_view(), name='enviar_foto'),
    path(route='conta/<int:pk>/', view=ContaMlRetrieveUpdateDestroyView.as_view(), name='Conta_ml'),
    path(route='respostas-padrao/', view=RespostaPadraoListCreateAPIView.as_view(), name='criar_listar_resposta_padrao'),
    path(route='resposta-padrao/<int:pk>/', view=RespostaPadraoRetrieveUpdateDestroyView.as_view(), name='deletar_atualizar_resposta_padrao'),
    path(route='usuario/', view=UpdateUserView.as_view(), name='usuario'),
    path('verify-email/<str:email>/', VerifyUpdateEmailView.as_view(), name='verify-email'),
    path(route='auth/', view=AuthMLAPIView.as_view(), name='auth_ml_app'),
    path(route='grupos/', view=GroupListView.as_view(), name='lista_grupos'),
    path(route='grupos/<int:grupo_id>/', view=GroupDetailView.as_view(), name='detalhes_grupo'),
    path(route='usuario/grupo/<int:grupo_id>/', view=UserToGroupView.as_view(), name='user_to_group'),
    path(route='perguntas/<int:conta_id>/', view=ListPerguntasContaView.as_view(), name='lista_perguntas_conta'),
    path(route='pergunta/<int:conta_id>/<int:question_id>/', view=DeletePerguntaView.as_view(), name='apagar_pergunta'),
    path(route='perguntas2/<int:conta_id>/', view=ListPerguntasContaView2.as_view(), name='lista_perguntas_conta'),
    path(route='perguntas-anteriores/<int:conta_id>/', view=ListaPerguntasAnteriores.as_view(), name='lista_perguntas_anteriores'),
    path(route='pergunta/responder/<int:conta_id>/', view=ResponderPerguntasView.as_view(), name='responder_pergunta'),
    path(route='notifica/', view=NotificacoesView.as_view(), name='receber_notificacoes'),
    path(route='notifications/', view=NotificationsListView.as_view(), name='list_notifications'),
    path(route='read_notifications/', view=MarkNotificationsAsReadView.as_view(), name='read_notifications'),
    path(route='notification/<int:pk>/', view=NotificationRetrieveUpdateDestroyView.as_view(), name='update_delete_notification'),
    path(route='devices/', view=DeviceListCreateAPIView.as_view(), name='device_view'),
    path(route='device/<str:device_token>/', view=DeviceRetrieveUpdateDestroyView.as_view(), name='device_view'),
 ]
