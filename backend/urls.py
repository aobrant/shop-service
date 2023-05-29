from django.db import router
from django.urls import path, include
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm

from backend.views import CategoryView, ShopView, ProductInfoView, BasketView, \
    OrderView, PartnerViewset, AccountViewSet
from rest_framework.routers import DefaultRouter

app_name = 'backend'

r = DefaultRouter()
r.register(r'partner', PartnerViewset, basename='partner')
r.register(r'user', AccountViewSet, basename='user')

urlpatterns = [
                  path('', include(r.urls)),
                  path('categories', CategoryView.as_view(), name='categories'),
                  path('shops', ShopView.as_view(), name='shops'),
                  path('products', ProductInfoView.as_view(), name='shops'),
                  path('basket', BasketView.as_view(), name='basket'),
                  path('order', OrderView.as_view(), name='order'),
                  path('user/password_reset', reset_password_request_token, name='password-reset'),
                  path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'),
              ]
