from django.test import TestCase
from .models import User
import datetime
# Create your tests here.
class UserTestCase(TestCase):
    def setUp(self):
        User.objects.create(
                                first_name='Iren',
                                last_name='Marlen',
                                email='user@gmail.com',
                                registration_date=datetime.datetime.now(),
                                subscription_type='kar',
                                amount='100',
                                fee_status='paid',
                            )
    def test_user(self):
        check = User.objects.get(first_name='Iren')
        print(check)
