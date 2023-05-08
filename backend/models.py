from django.db import models
from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from auth_backend.models import User, Contact

# storage = FileSystemStorage(location=settings.STORAGE)
storage = FileSystemStorage()

STATUS_CHOICES = (
    ('basket', 'Basket status'),
    ('new', 'New'),
    ('confirmed', 'Confirmed'),
    ('assembled', 'Assembled'),
    ('sent', 'Sent'),
    ('delivered', 'Delivered'),
    ('canceled', 'Canceled'),
)


# Create your models here.

class Shop(models.Model):
    name = models.CharField(max_length=50, verbose_name='Shop Name')
    url = models.URLField(verbose_name='Shops site', null=True, blank=True)
    file_name = models.FileField(verbose_name='', null=True, blank=True, storage=storage)
    user = models.OneToOneField(User, verbose_name='User', blank=True, null=True,
                                on_delete=models.CASCADE)
    state = models.BooleanField(verbose_name='Status of orders receiving  ', default=True)

    class Meta:
        verbose_name = 'Shop'
        verbose_name_plural = 'Shops'
        ordering = ('-name',)

    def __str__(self):
        return f'{self.name} - {self.user}'


class Category(models.Model):
    name = models.CharField(max_length=50, verbose_name='name of the category')
    shops = models.ManyToManyField(Shop, verbose_name='Shops', related_name='categories', blank=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'categories'
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name='Product name')
    category = models.ForeignKey(Category, verbose_name='Category', related_name='products', blank=True,
                                 on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = "Products"
        ordering = ('-name',)

    def __str__(self):
        return f'{self.category} - {self.name}'


class ProductInfo(models.Model):
    model = models.CharField(max_length=100, verbose_name='Model')
    external_id = models.PositiveIntegerField(verbose_name='External id')
    quantity = models.PositiveIntegerField(verbose_name='Quantity')
    price = models.PositiveIntegerField(verbose_name='Price')
    price_rrc = models.PositiveIntegerField(verbose_name='Recommended retail price')
    product = models.ForeignKey(Product, verbose_name='Product', related_name='product_infos', blank=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Shop', related_name='product_infos', blank=True,
                             on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Product information'
        verbose_name_plural = 'Product information list'
        constraints = [
            models.UniqueConstraint(fields=['product', 'shop'], name='unique_product_info'),
        ]

    def __str__(self):
        return f'{self.shop.name} - {self.product.name}'


class Parameter(models.Model):
    name = models.CharField(max_length=50, verbose_name='Parameter name')

    class Meta:
        verbose_name = 'Parameter name'
        verbose_name_plural = "List of parameter names"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, verbose_name='Product Information', blank=True,
                                     related_name='product_parameters', on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Parameter', related_name='product_parameters', blank=True,
                                  on_delete=models.CASCADE)
    value = models.CharField(max_length=100, verbose_name='Value')

    class Meta:
        verbose_name = 'Parameter'
        verbose_name_plural = 'List of parameter names'
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter'),
        ]

    def __str__(self):
        return f'{self.product_info.model} - {self.parameter.name}'


class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='User', related_name='orders', blank=True,
                             on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, verbose_name='Contact', related_name='Contact', blank=True, null=True,
                                on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, verbose_name='Status', choices=STATUS_CHOICES)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = "Order list"
        ordering = ('-dt',)

    def __str__(self):
        return f'{self.user} - {self.dt}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Order', related_name='ordered_items', blank=True,
                              on_delete=models.CASCADE)

    product_info = models.ForeignKey(ProductInfo, verbose_name='Product Information', related_name='ordered_items',
                                     blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantity')
    price = models.PositiveIntegerField(default=0, verbose_name='Price')
    total_amount = models.PositiveIntegerField(default=0, verbose_name='Total Amount')

    class Meta:
        verbose_name = 'Item ordered'
        verbose_name_plural = "List of ordered items"
        constraints = [
            models.UniqueConstraint(fields=['order_id', 'product_info'], name='unique_order_item'),
        ]

    def __str__(self):
        return f'№ {self.order} - {self.product_info.model}. Number: {self.quantity}. Sum {self.total_amount} '

    def save(self, *args, **kwargs):
        self.total_amount = self.price * self.quantity
        super(OrderItem, self).save(*args, **kwargs)
