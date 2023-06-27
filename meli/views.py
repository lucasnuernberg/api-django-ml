from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView, DestroyAPIView
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.conf import settings
from django.contrib.auth.models import Group
import requests
from dotenv import load_dotenv
from os import getenv, path
from PIL import Image
from threading import Thread
from storages.backends.gcloud import GoogleCloudStorage
from google.cloud import storage
from uuid import uuid4
from .models import ContaML, RespostaPadrao, Device
from .serializers import ContaMLSerializer, AuthMlSerializer, TokenMlSerializer, GroupSerializer, PerguntasSerializer, ResponderPerguntasSerializer, RespostaPadraoSerializer, PerguntasAnterioresSerializer, DeviceSerializer, NotificationSerializer
from .Meli import Meli
from .utils import mudar_tags, process_mercado_livre_response, is_timezone_valid, get_user_details
from drf_yasg.utils import swagger_auto_schema
from .firebase import send_push_notification_to_user
from lemon.celery import app
from .models import Notification


@app.task
def process_notification(seller_id, resource, topic):

    conta = ContaML.objects.filter(seller_id=seller_id).first()
    if conta:
        meli = Meli()
        meli.check_and_update_token(conta)
        
        if topic == 'questions':

            try:
                info_question = meli.send_request(url=resource, method='GET')
                if info_question['status'] == 'UNANSWERED':
                    extra_info = {
                        "seller_id": str(info_question['seller_id']),
                        "text": str(info_question['text']),
                        "date_created": str(info_question['date_created']),
                        "question_id": str(info_question['id'])
                    }

                    attributes = "title,thumbnail"
                    item_data = meli.send_request(url=f"/items/{info_question['item_id']}?attributes={attributes}", method='GET')
                    
                    extra_info.update({k: str(v) for k, v in item_data.items()})

                    notification = Notification.objects.create(
                        user=conta.user,
                        conta_ml=conta,
                        title="Você recebeu uma pergunta",
                        message=f"Responda a pergunta feita no item {info_question['item_id']}",
                        topic=topic,
                        related_item_id=info_question['item_id'],
                        extra_data=extra_info
                    )

                    send_push_notification_to_user(user_id=conta.user.id,
                                                data={
                                                        "title": item_data["title"],
                                                        "thumbnail": item_data["thumbnail"],
                                                        "text": info_question['text'],
                                                        "question_id": str(info_question["id"])
                                                    })
        
            except Exception:
                print("======================")
                print("Erro ao enviar notificação")
                print("======================")

class NotificacoesView(APIView):

    def post(self, request):
        
        body_notification = request.data
        print("============================")
        print(body_notification)
        print("============================")
        process_notification.delay(
            seller_id=body_notification['user_id'],
            resource=body_notification['resource'],
            topic=body_notification['topic']
        )

        return Response({"success": "Notificação recebida"}, status.HTTP_200_OK)

class NotificationsListView(ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        return Notification.objects.filter(user=user).order_by('-timestamp')[:20]

class NotificationRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Notification.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_object(self):
        notification_id = self.kwargs.get('pk')
        notification = get_object_or_404(Notification, id=notification_id)

        # Verifique se o usuário atual é o destinatário da notificação
        if notification.user != self.request.user:
            raise ValidationError(detail={"error": "Você não tem permissão para manipular essa notificação"})

        return notification

class MarkNotificationsAsReadView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    @swagger_auto_schema(operation_description="Atualizar notications em lote")
    def put(self, request):
        notification_ids = request.data.get('notification_ids', [])

        if not isinstance(notification_ids, list) or not all(isinstance(i, int) for i in notification_ids):
            return Response({"detail": "Formato inválido. 'notification_ids' deve ser uma lista de inteiros."}, status=status.HTTP_400_BAD_REQUEST)

        notifications = Notification.objects.filter(id__in=notification_ids, user=request.user)
        notifications.update(is_read=True)

        return Response(status=status.HTTP_200_OK)

class DeviceListCreateAPIView(ListCreateAPIView):
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        device_token = serializer.validated_data.get('device_token')
        if Device.objects.filter(user=user, device_token=device_token).exists():
            raise ValidationError(detail={"error": "Um dispositivo com esse token já está registrado para o usuário atual."})
        serializer.save(user=user)

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user)

class DeviceRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = Device.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = DeviceSerializer

    def perform_update(self, serializer):
        user = self.request.user
        device_token = serializer.validated_data.get('device_token')
        current_device = self.get_object()
        if Device.objects.filter(user=user, device_token=device_token).exclude(device_token=current_device.device_token).exists():
            raise ValidationError(detail={"error": "Um dispositivo com esse token já está registrado para o usuário atual."})
        serializer.save()


    def get_object(self):
        device_token = self.kwargs.get('device_token')
        device = get_object_or_404(Device, device_token=device_token)

        if device.user != self.request.user:
            raise ValidationError(detail={"error": "Usuário não tem esse dispositivo"})

        return device

class UploadFileView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'Nenhum arquivo foi enviado'}, status.HTTP_400_BAD_REQUEST)

        if not file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return Response({'error': 'O arquivo enviado não é uma imagem'}, status.HTTP_400_BAD_REQUEST)

        try:
            Image.open(file)
        except:
            return Response({'error': 'O arquivo enviado não é uma imagem válida'}, status.HTTP_400_BAD_REQUEST)

        creds = settings.GS_CREDENTIALS
        user = request.user
        # Verificar se o usuário já tem uma foto de perfil e apagá-la do Google Cloud Storage
        if user.profile_picture:
            client = storage.Client(credentials=creds)
            bucket = client.get_bucket(settings.GS_BUCKET_NAME)
            file_path = user.profile_picture.split(f'https://storage.googleapis.com/{settings.GS_BUCKET_NAME}/')[-1]

            try:
                blob = storage.Blob(file_path, bucket)
                blob.delete()

            except Exception as e:
                print(f"Erro ao deletar a imagem: {str(e)}")
        
        gcs = GoogleCloudStorage(credentials=creds)

        filename = f'media/{uuid4()}.{file.name.split(".")[-1]}'
        gcs.save(filename, file)

        file_url = f'https://storage.googleapis.com/{settings.GS_BUCKET_NAME}/{filename}'

        user = request.user
        user.profile_picture = file_url
        user.save()

        return Response({'url': file_url})

class PadraoPaginacao(PageNumberPagination):
    page_size = 10

class RespostaPadraoListCreateAPIView(ListCreateAPIView):
    serializer_class = RespostaPadraoSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = PadraoPaginacao

    def get_queryset(self):
        return RespostaPadrao.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class RespostaPadraoRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = RespostaPadrao.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = RespostaPadraoSerializer

    def get_object(self):
        resposta_padrao = super().get_object()

        if resposta_padrao.user != self.request.user:
            raise ValidationError(detail={"error": "Usuário não tem essa resposta"})

        return resposta_padrao

class AuthMLAPIView(APIView):

    permission_classes = [IsAuthenticated]
    serializer_class = AuthMlSerializer

    @swagger_auto_schema(operation_description="Cadastra as contas do mercado livre no sistema", request_body=AuthMlSerializer)
    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        load_dotenv(path.join(path.dirname(__file__), '..', 'config', '.env'))

        dados = {
            "grant_type": "authorization_code",
            "client_id": getenv('APP_ML_ID'),
            "client_secret": getenv('SECRECT_ML'),
            "code": request.data["code"],
            "redirect_uri": getenv('REDIRECT_URI_ML'),
            #"code_verifier": "$CODE_VERIFIER"  Implementar para segurança  
        }
        

        response_api = requests.post(url="https://api.mercadolibre.com/oauth/token", data=dados)

        response_json = response_api.json()

        if response_api.status_code not in [200, 201]:
            return Response(data={"error": "Code inválido"}, status=status.HTTP_400_BAD_REQUEST)

        elif response_json.get('access_token', None) != None:
            user_data = Meli(access_token=response_json.get('access_token')).send_request(method='GET',
                                                                                   url='users/me')
            
            user = request.user
            seller_id = dict(user_data).get('id')

            if user.contas.filter(seller_id=seller_id).exists():
                return Response({"error": "Esse usuário ja tem essa conta conectada"}, status.HTTP_400_BAD_REQUEST)
            
            if user.contas.count() >= 5:
                return Response({"error": "Esse usuário não pode mais cadastrar contas"}, status.HTTP_400_BAD_REQUEST)


            serielizer_conta = ContaMLSerializer(data={
                "nickname": dict(user_data).get('nickname', 'Conta Ml'),
                "user": user.id,
                "seller_id": seller_id,
                "data_criacao": dict(user_data).get('registration_date'),
                "link_img": dict(user_data).get('thumbnail').get('picture_url') if dict(user_data).get('thumbnail') else None,
                "permalink": dict(user_data).get('permalink'),
                "nivel": dict(user_data).get('seller_reputation').get('power_seller_status'),
            })
            
            serielizer_conta.is_valid(raise_exception=True)
            conta_criada = serielizer_conta.save()
            
            serializer_token = TokenMlSerializer(data={
                "access_token": response_json.get('access_token'),
                "refresh_token": response_json.get('refresh_token'),
                "conta_ml": conta_criada.id,
            })
            
            serializer_token.is_valid(raise_exception=True)            
            serializer_token.save()

            return Response(data={"response": "Cadastro feito com sucesso"})

class ContaMlListView(ListAPIView):
    serializer_class = ContaMLSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PadraoPaginacao

    def get_queryset(self):
        user = self.request.user
        queryset = ContaML.objects.filter(user=user).order_by('id')
        return queryset

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ContaMlListQuestionsView(ListAPIView):
    serializer_class = ContaMLSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PadraoPaginacao

    def get_queryset(self):
        user = self.request.user
        queryset = ContaML.objects.filter(user=user).order_by('id')
        return queryset

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        meli = Meli()

        # Lista para conter as contas e as perguntas não respondidas
        accounts_and_unanswered_questions = []

        for conta in queryset:
            meli.check_and_update_token(conta)
            unanswered_questions = meli.send_request(
                url=f'/my/received_questions/search',
                method='GET',
                params={"status": "UNANSWERED"}
            )["total"]

            # Serializar a conta e adicionar o número de perguntas não respondidas
            serializer = self.get_serializer(conta)
            data = serializer.data
            data['unanswered_questions'] = unanswered_questions
            accounts_and_unanswered_questions.append(data)

        # Paginação
        page = self.paginate_queryset(accounts_and_unanswered_questions)

        if page is not None:
            return self.get_paginated_response(page)

        return Response(accounts_and_unanswered_questions)

class ContaMlRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    queryset = ContaML.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ContaMLSerializer

    def get_object(self):
        conta_ml = super().get_object()
        if conta_ml.user != self.request.user:
            raise ValidationError(detail={"error": "Usuário não tem essa Conta"})

        return conta_ml

    def delete(self, request, *args, **kwargs):
        load_dotenv(path.join(path.dirname(__file__), '..', 'config', '.env'))
        conta_ml = self.get_object()
        meli = Meli()
        meli.check_and_update_token(conta_ml)
        #Retira o app
        retorno = meli.send_request(url=f'/users/{conta_ml.seller_id}/applications/{getenv("APP_ML_ID")}',
                                    method='DELETE')

        return super().delete(request, *args, **kwargs)

class GroupListView(ListAPIView):
    queryset = Group.objects.filter()
    serializer_class = GroupSerializer
    pagination_class = PadraoPaginacao
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class GroupDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, grupo_id):
        group = get_object_or_404(Group, pk=grupo_id)
        serializer = GroupSerializer(group)
        return Response(serializer.data)

#Mais segurança nesse metodo - Aprimorar
class UserToGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, grupo_id):
        user = request.user

        try:
            group = Group.objects.get(id=grupo_id)
        except Group.DoesNotExist:
            return Response(data={"error": "Grupo não encontrado."}, status=status.HTTP_400_BAD_REQUEST)

        user.group = group
        user.save()
        
        return Response(data={"success": f"{user.email} foi adcionado ao grupo {group.name}."})
    
    def delete(self, request, grupo_id):
        
        user = request.user
        
        if user.group == None:
            return Response(data={"error": "Usuário não pertence a esse grupo."}, status=status.HTTP_400_BAD_REQUEST)

        if user.group.id == grupo_id:
            group = user.group

            user.group = None
            user.save()
            return Response(data={"success": f"{user.email} foi tirado do grupo {group.name}."})
        else:
            return Response(data={"error": "Usuário não pertence a esse grupo."}, status=status.HTTP_400_BAD_REQUEST)

class ListPerguntasContaView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PerguntasSerializer
    
    def get_paginated_response(self, data, total, limit):
        current_page = int(self.request.query_params.get('page', 1))
        page_size = int(self.request.query_params.get('page_size', 10))

        start = (current_page - 1) * page_size
        end = start + page_size

        paginated_data = data[start:end]

        response_data = {
            'count': total,
            'next': None if end >= total else current_page + 1,
            'previous': None if current_page == 1 else current_page - 1,
            'results': paginated_data
        }

        return Response(response_data)

    @swagger_auto_schema(operation_description="Listar perguntas do mercado livre", request_body=PerguntasSerializer)
    def post(self, request, conta_id):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        conta = request.user.contas.filter(id=conta_id).first()

        if conta:
            meli = Meli()
            meli.check_and_update_token(conta)

            user_timezone = request.data.get("timezone", "UTC")  # Obter o fuso horário do usuário ou usar "UTC" como padrão
            
            if not is_timezone_valid(user_timezone):
                return Response({"error": f"Fuso horário inválido: {user_timezone}"}, status=status.HTTP_400_BAD_REQUEST)

            request.data.pop('user_timezone', None)

            data_ml = request.data
            data_ml['limit'] = 10

            perguntas = process_mercado_livre_response(response=meli.send_request(url=f'/my/received_questions/search',
                                                                         method='GET',
                                                                         params=data_ml), user_timezone=user_timezone)
            
            if len(perguntas['questions']) > 0:
                atributos = 'id,title,price,thumbnail,permalink'
                ids = ','.join(str(pergunta['item_id']) for pergunta in perguntas["questions"])
                lista_dados = meli.send_request(url=f'/items', method='GET', params={
                    "ids": ids,
                    "attributes": atributos,
                    "api_version": "4"
                })

                for pergunta in perguntas["questions"]:         
                    for dados_item in lista_dados:
                        if dados_item["body"]["id"] == pergunta['item_id']:
                            pergunta["link_anuncio"] = dados_item["body"]['permalink']
                            pergunta["titulo_anuncio"] = dados_item["body"]['title']
                            pergunta["link_img"] = dados_item["body"]['thumbnail']
                            pergunta["preco"] = dados_item["body"]['price']                        
                            break

            return self.get_paginated_response(perguntas['questions'], perguntas['total'], perguntas['limit'])
        else:
            return Response({"error": f"Não existe uma conta com o id {conta_id} atribuida a esse usuário"}, status=status.HTTP_404_NOT_FOUND)

class ListPerguntasContaView2(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PerguntasSerializer

    def get_conversas_anteriores(self, pergunta, meli, user_timezone):
        """
        Buscar todas as conversas anteriores para um question_id em uma única chamada de API.
        """
        dados_pergunta = meli.send_request(method='GET', url=f'questions/{pergunta["id"]}')
        if dados_pergunta["from"]["answered_questions"] > 1:
            conversa = process_mercado_livre_response(response=meli.send_request(url='/questions/search', method='GET', params={"api_version": 4,
                                                                                        "from": dados_pergunta["from"]["id"],
                                                                                        "item": dados_pergunta["item_id"]}), user_timezone=user_timezone)
            pergunta["conversas_anteriores"] = conversa['questions']

    def fetch_conversas_anteriores_threaded(self, perguntas, meli, user_timezone):
        threads = []
        for pergunta in perguntas:
            thread = Thread(target=self.get_conversas_anteriores, args=(pergunta, meli, user_timezone))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def get_user_details_threaded(self, pergunta, meli):
        dados_comprador = get_user_details(user_id=pergunta['from']['id'], meli=meli)
        pergunta['nickname'] = dados_comprador['nickname']
        pergunta['address'] = dados_comprador['address']

    def fetch_user_details_threaded(self, perguntas, meli):
        threads = []
        for pergunta in perguntas:
            thread = Thread(target=self.get_user_details_threaded, args=(pergunta, meli))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    @swagger_auto_schema(operation_description="Listar perguntas do mercado livre 2.0", request_body=PerguntasSerializer)
    def post(self, request, conta_id):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        conta = request.user.contas.filter(id=conta_id).first()

        if conta:
            meli = Meli()
            meli.check_and_update_token(conta)

            user_timezone = request.data.get("timezone", "UTC")  # Obter o fuso horário do usuário ou usar "UTC" como padrão
            
            if not is_timezone_valid(user_timezone):
                return Response({"error": f"Fuso horário inválido: {user_timezone}"}, status=status.HTTP_400_BAD_REQUEST)

            request.data.pop('user_timezone', None)

            data_ml = request.data

            current_page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('limit', 10))

            data_ml['offset'] = (current_page - 1) * page_size
            data_ml['limit'] = int(request.query_params.get('limit', 10))

            perguntas = process_mercado_livre_response(response=meli.send_request(url=f'/my/received_questions/search',
                                                                         method='GET',
                                                                         params=data_ml), user_timezone=user_timezone)
            if len(perguntas['questions']) > 0:
                atributos = 'id,title,price,thumbnail,permalink'
                ids = ','.join(str(pergunta['item_id']) for pergunta in perguntas["questions"])
                lista_dados = meli.send_request_without_auth(url=f'/items', method='GET', params={
                    "ids": ids,
                    "attributes": atributos,
                    "api_version": "4"
                })

                for pergunta in perguntas["questions"]:     
                    for dados_item in lista_dados:
                        if dados_item["body"]["id"] == pergunta['item_id']:
                            pergunta["link_anuncio"] = dados_item["body"]['permalink']
                            pergunta["titulo_anuncio"] = dados_item["body"]['title']
                            pergunta["link_img"] = dados_item["body"]['thumbnail']
                            pergunta["preco"] = dados_item["body"]['price']                        
                            break


                self.fetch_user_details_threaded(perguntas["questions"], meli)
                self.fetch_conversas_anteriores_threaded(perguntas["questions"], meli, user_timezone)

            return Response(data=perguntas, status=status.HTTP_200_OK)
        else:
            return Response({"error": f"Não existe uma conta com o id {conta_id} atribuida a esse usuário"}, status=status.HTTP_404_NOT_FOUND)

class DeletePerguntaView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_description="Deletar uma pergunta específica")   
    def delete(self, request, conta_id, question_id):
        conta = request.user.contas.filter(id=conta_id).first()

        if not conta:
            return Response({'detail': 'Conta não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
        

        meli = Meli()
        meli.check_and_update_token(conta)
        meli.send_request(method='DELETE', url=f'questions/{question_id}')
        return Response({'detail': 'Pergunta deletada com sucesso.'}, status=status.HTTP_200_OK)

class ListaPerguntasAnteriores(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PerguntasAnterioresSerializer

    @swagger_auto_schema(operation_description="Listar todas as perguntas anteriores de um comprador em um item", request_body=PerguntasAnterioresSerializer)   
    def post(self, request, conta_id):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        conta = request.user.contas.filter(id=conta_id).first()
        question_id = request.data["question_id"]

        if conta:
            meli = Meli()
            meli.check_and_update_token(conta)

            dados_pergunta = meli.send_request(method='GET', url=f'questions/{question_id}')

            user_timezone = request.data.get("timezone", "UTC")  # Obter o fuso horário do usuário ou usar "UTC" como padrão
            request.data.pop('user_timezone', None)

            if dados_pergunta["from"]["answered_questions"] > 1:

                conversa = process_mercado_livre_response(response=meli.send_request(url='/questions/search', method='GET', params={"api_version": 4,
                                                                                            "from": dados_pergunta["from"]["id"],
                                                                                            "item": dados_pergunta["item_id"]}), user_timezone=user_timezone)
                
                return Response(data=conversa, status=status.HTTP_200_OK)
            else:
                return Response(data={"error": "Não existem perguntas anteriores"}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"error": f"Não existe uma conta com o id {conta_id} atribuida a esse usuário"}, status=status.HTTP_404_NOT_FOUND)

class ResponderPerguntasView(APIView):

    permission_classes = [IsAuthenticated]
    serializer_class = ResponderPerguntasSerializer
    
    @swagger_auto_schema(operation_description="Responder perguntas do mercado livre", request_body=ResponderPerguntasSerializer)
    def post(self, request, conta_id):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        conta = request.user.contas.filter(id=conta_id).first()
        if conta:

            meli = Meli()
            meli.check_and_update_token(conta) 

            request.data['text'] = mudar_tags(text=request.data['text'],
                                              access_token=meli.access_token,
                                              question_id=request.data['question_id'])
         
            response = meli.send_request(url=f'/answers', method='POST', data=request.data)

            return Response(response)
        else:
            return Response({"error": f"Não existe uma conta com o id {conta_id} atribuida a esse usuário"}, status=status.HTTP_400_BAD_REQUEST)
