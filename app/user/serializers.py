from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import ugettext_lazy as _  # good practice to run outputted text through translation
from rest_framework import serializers


class UserSerielizer(serializers.ModelSerializer):
    """Serializer for user object"""

    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'name')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    def create(self, validated_data):
        """create new user with encrypted pw and return it"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update a user, set password correctly and return it"""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for user authentication object"""
    email = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False  # its possible to have whitespace in pw, by default django trims it
    )

    def validate(self, attrs):
        """validate and authenticate the user"""
        email = attrs.get('email')  # attrs is basically every field that makes up the serializer
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )

        if not user:
            msg = _('Unable to authenticate user with provided credentials')
            raise serializers.ValidationError(msg, code='authentication')

        # inject user object and return attrs
        attrs['user'] = user
        return attrs  # whenever overwriting validate func you must return attrs
