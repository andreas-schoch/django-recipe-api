from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Tag, Recipe
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


class PublicTagsApiTests(TestCase):
    """Test the publicly available tag api"""

    def setUp(self):
        self.client = APIClient()

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

    def test_create_tag_successful(self):
        """Test creating a new tag"""
        payload = {'name': 'newtag'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(user=self.user, name=payload['name']).exists()
        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """Test creating a tag with invalid name"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        """Test filtering out tags that are not assigned to any recipes"""
        tag1 = Tag.objects.create(user=self.user, name='tag1')
        tag2 = Tag.objects.create(user=self.user, name='tag2')
        recipe = Recipe.objects.create(user=self.user, title='recipe', time_minutes=5, price=5)
        recipe.tags.add(tag1)

        # assigned_only is a filter, meaning only tags assigned to recipes will be returned (0 or 1)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        """Test filtering tags assigned returns unique items"""
        tag = Tag.objects.create(user=self.user, name='tag1')
        Tag.objects.create(user=self.user, name='tag2')  # second tag necessary for the assertion

        recipe1 = Recipe.objects.create(user=self.user, title='recipe1', time_minutes=5, price=5)
        recipe1.tags.add(tag)

        recipe2 = Recipe.objects.create(user=self.user, title='recipe2', time_minutes=5, price=5)
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)  # this is why we need second tag
