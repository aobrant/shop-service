from celery import shared_task
from django.db.models import Sum, F
from rest_framework import request

from backend.models import Order, Shop, Category, ProductInfo, Product, Parameter, ProductParameter
from backend.serializers import OrderSerializer


@shared_task
def oder_ser(request):
    order = Order.objects.filter(
        user_id=request.user.id).exclude(state='basket').prefetch_related(
        'ordered_items__product_info__product__category',
        'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
        total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

    serializer = OrderSerializer(order, many=True)
    serializer_data = serializer.data
    return serializer_data


@shared_task
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
