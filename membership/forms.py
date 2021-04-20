from django import forms
from django.forms import ModelForm
from membership.models import User
from django.db import models
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

class UpdateUserForm(forms.Form):
    subscription_type = forms.ChoiceField(choices=SUBSCRIPTION_TYPE_CHOICES)
    registration_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'datepicker form-control', 'type': 'date'}),)
    registration_upto = forms.DateField(widget=forms.DateInput(attrs={'class': 'datepicker form-control', 'type': 'date'}),)
    fee_status = forms.ChoiceField(label='Fee Status', choices=FEE_STATUS)
    amount = forms.CharField()
    stop = forms.ChoiceField(label='Status', choices=STATUS)

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if not amount.isdigit():
            raise forms.ValidationError('Amount should be a number')
        return amount

class UpdateUserInForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    birth_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'datepicker  form-control', 'type': 'date'}),)
    email = forms.EmailField(required=True)

class AddUserForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(AddUserForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].error_messages = {'required': 'Please enter first name'}
        self.fields['last_name'].error_messages = {'required': 'Please enter last name'}
        self.fields['username']
    class Meta:
        model = User
        # fields = ['username', 'first_name', 'last_name', 'email', 'birth_date', 'subscription_type', 'date_joined']
        fields = ['username', 'first_name', 'last_name', 'email', 'birth_date', 'stop', 'registration_date', 'registration_upto', 'subscription_type', 'amount', 'fee_status']
        widgets = {
        'birth_date': forms.DateInput(attrs={'class': 'datepicker form-control', 'type': 'date'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if not amount.isdigit():
            raise forms.ValidationError('Amount should be a number')
        return amount

    def clean(self):
        cleaned_data = super().clean()
        birth_date = cleaned_data.get('birth_date')
        first_name = cleaned_data.get('first_name').capitalize()
        last_name = cleaned_data.get('last_name').capitalize()
        queryset = User.objects.filter(
                        first_name=first_name,
                        last_name=last_name,
                        birth_date=birth_date
                    ).count()
        if queryset > 0:
            raise forms.ValidationError('This member already exists!')
