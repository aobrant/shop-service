from django.db import router
from django.urls import path, include
from rest_framework import routers

from backend.views import PartnerUpdate, LocalPartnerUpdate

app_name = 'backend'

urlpatterns = [
    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/update/local', LocalPartnerUpdate.as_view(), name='Local_partner-update'),
]
