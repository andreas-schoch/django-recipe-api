from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):
    """Test the publicly available tag api"""

    def setUp(self):
        self.client = APIClient()

    # def test_login_required(self):
    #     """Test that login is required to retrieve the tags"""
    #     res = self.client.get(TAGS_URL)
    #     self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_required(self):
        """Test that login is required for retrieving tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test authoriced user apu"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(email='test@test.com', password='password123')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags"""
        Tag.objects.create(name='tag1', user=self.user)
        Tag.objects.create(name='tag2', user=self.user)

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are meant for authenticated user"""
        self.other_user = get_user_model().objects.create_user(email='other@other.com', password='password123')
        my_tag = Tag.objects.create(name='mytag', user=self.user)
        Tag.objects.create(name='othertag', user=self.other_user)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)  # should only return a single tag of authorized user
        self.assertEqual(res.data[0]['name'], my_tag.name)
