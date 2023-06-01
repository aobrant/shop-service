from django.test import TestCase
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import User

from backend.views import PartnerViewset


class MyTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_update_price_list_unauthenticated(self):

        url = '/api/partner/update_price_list/'
        data = {'url': 'http://example.com'}

        request = self.factory.post(url, data)
        response = PartnerViewset.as_view({'post': 'update_price_list'})(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['Error'], 'Log in required')

