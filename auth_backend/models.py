from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django_rest_passwordreset.tokens import get_token_generator
from django.db import models


USER_TYPE_CHOICES = (
    ('shop', 'Shop'),
    ('buyer', 'Buyer'),

)


class UserManager(BaseUserManager):
    """
    Миксин для управления пользователями
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Стандартная модель пользователей
    """
    objects = UserManager()
    email = models.EmailField(verbose_name='Email', max_length=40, unique=True)
    company = models.CharField(verbose_name='Company', max_length=40, blank=True, null=True)
    position = models.CharField(verbose_name='Position', max_length=40, blank=True, null=True)
    type = models.CharField(verbose_name='Users type', choices=USER_TYPE_CHOICES, max_length=5, default='buyer')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = "List of users"
        ordering = ('email',)


class Contact(models.Model):
    user = models.ForeignKey(User, verbose_name='User', related_name='contacts', blank=True,
                             on_delete=models.CASCADE)
    city = models.CharField(max_length=50, verbose_name='City')
    street = models.CharField(max_length=100, verbose_name='Street', blank=True)
    house = models.CharField(max_length=35, verbose_name='House', blank=True)
    apartment = models.CharField(max_length=15, verbose_name='Flat', blank=True)
    e_mail = models.EmailField(max_length=50, verbose_name='E-mail', blank=True)
    phone = models.CharField(max_length=35, verbose_name='Cell Phone')
    work_phone = models.CharField(max_length=40, verbose_name='Working Phone', blank=True)

    class Meta:
        verbose_name = 'Users Contact'
        verbose_name_plural = "List of users contacts"

    def __str__(self):
        return f'{self.city}, {self.phone}'


class ConfirmEmailToken(models.Model):
    class Meta:
        verbose_name = 'Confirmation Token Email'
        verbose_name_plural = 'Confirmation Tokens Email'

    @staticmethod
    def generate_key():
        """ generates a pseudo random code using os.urandom and binascii.hexlify """
        return get_token_generator().generate_token()

    user = models.ForeignKey(
        User,
        related_name='confirm_email_tokens',
        on_delete=models.CASCADE,
        verbose_name="The User which is associated to this password reset token"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="When was this token generated"
    )

    # Key field, though it is not the primary key of the model
    key = models.CharField(
        verbose_name="Key",
        max_length=64,
        db_index=True,
        unique=True
    )

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ConfirmEmailToken, self).save(*args, **kwargs)

    def __str__(self):
        return "Password reset token for user {user}".format(user=self.user)


