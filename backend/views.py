from distutils.util import strtobool

import yaml
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponse
import os
from django.db.models import Q, Sum, F
from urllib.request import urlopen
from django.shortcuts import render
from requests import get
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from ujson import loads as load_json
import json
from yaml import load as load_yaml, Loader
from django.core.exceptions import ValidationError

from auth_backend.models import ConfirmEmailToken, Contact
from auth_backend.serializers import UserSerializer, ContactSerializer
from backend.models import Shop, Category, ProductInfo, Product, ProductParameter, Parameter, Order, OrderItem
from backend.serializers import CategorySerializer, ShopSerializer, ProductInfoSerializer, OrderSerializer, \
    OrderItemSerializer
from backend.signals import new_user_registered, new_order
from backend.tasks import oder_ser, import_partner

from rest_framework.viewsets import ViewSet, GenericViewSet
from rest_framework.decorators import action


# Create your views here.
def index(request):
    """
    Home page
    """
    return render(request, 'index.html')


class PartnerViewset(ViewSet):
    """
    Viewset for updating the price list from the supplier
    """

    @action(detail=False, methods=['post'])
    def update_price_list(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Only for shops'}, status=403)

        url = request.data.get('url')

        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content
                data = load_yaml(stream, Loader=Loader)

                import_partner(data)

                # return JsonResponse({'Status': True})
                return HttpResponse(json.dumps({'Status': True}), content_type='application/json')

        # return JsonResponse({'Status': False, 'Errors': 'Not all required arguments  provided'})
        return HttpResponse(json.dumps({'Status': False, 'Errors': 'Not all required arguments not provided'}),
                            content_type='application/json')

    """
        Class for updating the price from the supplier through a local file in the folder fixtures
    """

    @action(detail=False, methods=['post'])
    def partner_update_local(self, request, *args, **kwargs):
        file_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'shop1.yaml')
        with open(file_path, 'r') as stream:
            data = yaml.safe_load(stream)
        import_partner(data)
        return HttpResponse(json.dumps({'Status': True}), content_type='application/json')

    """
    working with supplier status
    """

    # get current status
    @action(detail=False, methods=['get'])
    def get_partner_state(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Stores only'}, status=403)

        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    # change current status
    @action(detail=False, methods=['post'])
    def change_status(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Stores only'}, status=403)
        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
                return JsonResponse({'Status': True})
            except ValueError as error:
                return JsonResponse({'Status': False, 'Errors': str(error)})

        return JsonResponse({'Status': False, 'Errors': 'Not all required arguments not provided'})

    """
    receiving orders by suppliers
    """

    @action(detail=False, methods=['get'])
    def list_of_orders(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Stores only'}, status=403)

        serializer_data = oder_ser(request)
        return Response(serializer_data)


class AccountViewSet(GenericViewSet):
    """
    Class for working with user accounts
    """

    # Registration method POST
    @action(detail=False, methods=['post'])
    def register(self, request, *args, **kwargs):

        # checking required arguments
        if {'first_name', 'last_name', 'email', 'password', 'company', 'position'}.issubset(request.data):
            errors = {}

            # check the password for complexity

            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                # check data for unique username

                data_request = {
                    'id': request.data['id'],
                    'email': request.data['email'],
                    'company': request.data['company'],
                    'position': request.data['position']
                }
                user_serializer = UserSerializer(data=data_request)
                if user_serializer.is_valid():
                    # save the user
                    user = user_serializer.save()
                    # user.set_password(request.data['password'])
                    user.set_password(data_request['password'])
                    user.save()
                    new_user_registered.send(sender=self.__class__, user_id=user.id)
                    return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Not all required arguments not provided'})

    """
    validating an email address
    """

    # Registration method POST
    @action(detail=False, methods=['post'])
    def confirm(self, request, *args, **kwargs):

        # checking required arguments
        if {'email', 'token'}.issubset(request.data):

            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Неправильно указан токен или email'})

        return JsonResponse({'Status': False, 'Errors': 'Not all required arguments not provided'})

    """
    working with user data
    """

    # to get data
    @action(detail=False, methods=['get'])
    def details(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    # Editing method POST
    @action(detail=False, methods=['post'])
    def update_account(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        # checking required arguments

        if 'password' in request.data:
            errors = {}
            # check the password for complexity
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                request.user.set_password(request.data['password'])

        # check other data
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

    """
    working with customer contacts
    """

    # get contacts
    @action(detail=False, methods=['get'])
    def get_contact(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        contact = Contact.objects.filter(
            user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    # add new contact
    @action(detail=False, methods=['post'])
    def add_contact(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'city', 'street', 'phone'}.issubset(request.data):
            request.data._mutable = True
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Not all required arguments not provided'})

    # delete contact
    @action(detail=False, methods=['delete'])
    def delete_contact(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Objects removed': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Not all required arguments not provided'})

    """
    Class for user authorization
    """

    # Method authorization POST
    @action(detail=False, methods=['post'])
    def login(self, request, *args, **kwargs):

        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)

                    return JsonResponse({'Status': True, 'Token': token.key})

            return JsonResponse({'Status': False, 'Errors': 'Failed to authorize'})

        return JsonResponse({'Status': False, 'Errors': 'Not all required arguments not provided'})


class CategoryView(ListAPIView):
    """
    Category view class
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    Class for viewing the list of stores
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class ProductInfoView(APIView):
    """
    Class for searching goods
    """

    def get(self, request, *args, **kwargs):

        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        # filtering and discarding duplicates
        queryset = ProductInfo.objects.filter(
            query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()

        serializer = ProductInfoSerializer(queryset, many=True)

        return Response(serializer.data)


class BasketView(APIView):
    """
    Class for working with the user's shopping basket
    """

    # get basket
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        basket = Order.objects.filter(
            user_id=request.user.id, state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    # edit basket
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                return JsonResponse({'Status': False, 'Errors': 'Invalid request format'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                objects_created = 0
                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            return JsonResponse({'Status': False, 'Errors': str(error)})
                        else:
                            objects_created += 1

                    else:

                        return JsonResponse({'Status': False, 'Errors': serializer.errors})

                return JsonResponse({'Status': True, 'Objects created': objects_created})
        return JsonResponse({'Status': False, 'Errors': 'Not all required arguments not provided'})

    # remove items from basket
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Objects removed': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Not all required arguments not provided'})

    # add items to basket
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                return JsonResponse({'Status': False, 'Errors': 'Invalid request format'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                objects_updated = 0
                for order_item in items_dict:
                    if type(order_item['id']) == int and type(order_item['quantity']) == int:
                        objects_updated += OrderItem.objects.filter(order_id=basket.id, id=order_item['id']).update(
                            quantity=order_item['quantity'])

                return JsonResponse({'Status': True, 'Objects updated': objects_updated})
        return JsonResponse({'Status': False, 'Errors': 'Not all required arguments not provided'})


class OrderView(APIView):
    """
    Class for receiving and placing orders by users
    """

    # get my orders
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        serializer_data = oder_ser(request)
        return Response(serializer_data)

    # place order from cart
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'id', 'contact'}.issubset(request.data):
            if request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data['id']).update(
                        contact_id=request.data['contact'],
                        state='new')
                except IntegrityError as error:
                    print(error)
                    return JsonResponse({'Status': False, 'Errors': 'Arguments specified incorrectly'})
                else:
                    if is_updated:
                        new_order.send(sender=self.__class__, user_id=request.user.id)
                        return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Not all required arguments not provided'})
