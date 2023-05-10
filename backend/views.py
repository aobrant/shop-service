import yaml
from django.core.validators import URLValidator
from django.http import JsonResponse, HttpResponse
import os
from urllib.request import urlopen
from django.shortcuts import render
from requests import get
from rest_framework.views import APIView
import json
from yaml import load as load_yaml, Loader
from django.core.exceptions import ValidationError

from backend.models import Shop, Category, ProductInfo, Product, ProductParameter, Parameter


# Create your views here.

def import_partner(data):
    shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
    for category in data['categories']:
        category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
        category_object.shops.add(shop.id)
        category_object.save()
    ProductInfo.objects.filter(shop_id=shop.id).delete()
    for item in data['goods']:
        product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

        product_info = ProductInfo.objects.create(product_id=product.id,
                                                  external_id=item['id'],
                                                  model=item['model'],
                                                  price=item['price'],
                                                  price_rrc=item['price_rrc'],
                                                  quantity=item['quantity'],
                                                  shop_id=shop.id)
        for name, value in item['parameters'].items():
            parameter_object, _ = Parameter.objects.get_or_create(name=name)
            ProductParameter.objects.create(product_info_id=product_info.id,
                                            parameter_id=parameter_object.id,
                                            value=value)
        return


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

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

        # return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})
        return HttpResponse(json.dumps({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'}),
                            content_type='application/json')


class LocalPartnerUpdate(APIView):
    """
        Класс для обновления прайса от поставщика через локальный файл в папке fixtures
        """
    def post(self, request, *args, **kwargs):
        file_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'shop1.yaml')
        with open(file_path, 'r') as stream:
            data = yaml.safe_load(stream)
        import_partner(data)
        return HttpResponse(json.dumps({'Status': True}), content_type='application/json')
