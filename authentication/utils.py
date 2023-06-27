from django.core.mail import EmailMultiAlternatives

class Util:
    @staticmethod
    def send_email(data):
        email = EmailMultiAlternatives(
            subject=data['email_subject'],
            body='Esta é a versão em texto simples do seu email.',
            to=[data['to_email']],
        )
        email.attach_alternative(data['email_body'], "text/html")
        email.send()
