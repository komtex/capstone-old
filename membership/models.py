from django.contrib.auth.models import AbstractUser
from django.db import models
from django import forms
from django.forms import ModelForm
import datetime

SUBSCRIPTION_TYPE_CHOICES = (
    ('kar', 'Karate'),
    ('sd', 'SelfDefense'),
    ('pt', 'Personal Training'),
)

FEE_STATUS = (
    ('paid', 'Paid'),
    ('pending', 'Pending'),
)

STATUS = (
    (0, 'Start'),
    (1, 'Stop'),
)

class User(AbstractUser):
    pass
    birth_date = models.DateField(null=True, blank=True)
    registration_date = models.DateField(('Registration Date'), default=datetime.date.today)
    registration_upto = models.DateField(null=True, blank=True)
    subscription_type  = models.CharField(
                            ('Subscription Type'),
                            max_length=3,
                            choices=SUBSCRIPTION_TYPE_CHOICES,
                            default=SUBSCRIPTION_TYPE_CHOICES[0][0]
                            )
    amount = models.CharField(max_length=30, null=True, blank=True)
    fee_status = models.CharField(('Fee Status'), max_length=30, choices=FEE_STATUS, default=FEE_STATUS[0][0])
    notification = models.IntegerField(default=2, blank=True)
    stop = models.IntegerField(('Status'), choices=STATUS, default=STATUS[0][0], blank=True)
    def __str__(self):
        return self.first_name + '' + self.last_name
