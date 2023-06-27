from django.db import models
from django.conf import settings
from authentication.models import CustomUser

class ContaML(models.Model):
    
    nickname = models.CharField(max_length=50)
    seller_id = models.IntegerField()
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='contas'
    )
    data_criacao = models.DateTimeField(blank=True, null=True)
    link_img = models.URLField(blank=True, null=True)
    permalink = models.URLField(blank=True, null=True)
    nivel = models.CharField(blank=True, null=True, max_length=50)

    def __str__(self):
        return self.nickname

class TokenMl(models.Model):
    
    access_token = models.CharField(blank=True, max_length=100)
    refresh_token = models.CharField(max_length=100)
    conta_ml = models.OneToOneField(ContaML, on_delete=models.CASCADE, unique=True, related_name='token')
    access_token_expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.conta_ml.nickname

class RespostaPadrao(models.Model):
    
    nome = models.CharField(blank=True, max_length=100)
    texto = models.CharField(max_length=1000)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    def __str__(self):
        return self.nome

class Device(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    device_token = models.CharField(max_length=255)
    platform = models.CharField(max_length=10, choices=(('ios', 'iOS'),
                                                        ('android', 'Android'),
                                                        ('web', 'Web')))
    created_at = models.DateTimeField(auto_now_add=True)    

    class Meta:
        unique_together = ('user', 'device_token')

    def __str__(self):
        return f"{self.id} - {self.user.first_name} - {self.platform}"

class Notification(models.Model):
    
    TOPIC_CHOICES = [
        ('items', 'Items'),
        ('questions', 'Questions'),
        ('payments', 'Payments'),
        ('messages', 'Messages'),
        ('orders_v2', 'Orders V2'),
        ('shipments', 'Shipments'),
        ('orders feedback', 'Orders Feedback'),
        ('quotations', 'Quotations'),
        ('invoices', 'Invoices'),
        ('claims', 'Claims'),
        ('item competition', 'Item Competition'),
        ('leads credits', 'Leads Credits'),
        ('stock fulfillment', 'Stock Fulfillment'),
        ('best price eligible', 'Best Price Eligible'),
        ('public candidates', 'Public Candidates'),
        ('items prices', 'Items Prices'),
        ('public offers', 'Public Offers'),
        ('flex handshakes', 'Flex Handshakes'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    conta_ml = models.ForeignKey(ContaML, on_delete=models.SET_NULL, null=True)

    title = models.CharField(max_length=255)
    message = models.TextField()
    topic = models.CharField(max_length=50, choices=TOPIC_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    related_item_id = models.CharField(max_length=255, blank=True, null=True)
    extra_data = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.id} {self.user.first_name} - {self.title} - {self.is_read}"
