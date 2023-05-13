from rest_framework import serializers

from auth_backend.models import User, Contact


# from backend.serializers import ContactSerializer


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'city', 'street', 'house', 'work_phone', 'building', 'apartment', 'user', 'phone', 'e_mail')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }


class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'company', 'position')
        read_only_fields = ('id',)
