from .Meli import Meli
import pytz
from dateutil import parser

def mudar_tags(text, access_token, question_id):

    if '[Nome do cliente]' in text:
        meli = Meli(access_token)
        pergunta = meli.send_request(url=f'/questions/{question_id}?api_version=4', method='GET')
        dados_comprador = meli.send_request(url=f'/users/{pergunta["from"]["id"]}', method='GET')
        nome_comprador = dados_comprador['nickname'] if dict(dados_comprador).get('nickname') != None else ''
        nome_comprador = ''.join(i for i in nome_comprador.split(".")[0].title() if not i.isdigit())
        text = text.replace("[Nome do cliente]", nome_comprador)
    
    if '[Nome do produto]' in text:
        meli = Meli(access_token)
        pergunta = meli.send_request(url=f'/questions/{question_id}?api_version=4', method='GET')
        item = meli.send_request(url=f'/items/{pergunta["item_id"]}', method='GET')
        titulo_item = item['title']
        text = text.replace("[Nome do produto]", titulo_item)
        
    return text

def convert_to_user_timezone(dt, user_timezone):
    utc_dt = dt.astimezone(pytz.UTC)
    user_tz = pytz.timezone(user_timezone)
    return utc_dt.astimezone(user_tz)

def process_mercado_livre_response(response, user_timezone):
    for question in response['questions']:
        date_created = parser.parse(question['date_created'])
        question['date_created'] = convert_to_user_timezone(date_created, user_timezone)

    return response

def is_timezone_valid(timezone_str):
    return timezone_str in pytz.all_timezones

def get_user_details(user_id, meli):

    return meli.send_request_without_auth(url=f'users/{user_id}', method='GET')