from django.db import router
from django.urls import path, include
from rest_framework import routers

from backend.views import PartnerUpdate

app_name = 'backend'

urlpatterns = [
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
]
