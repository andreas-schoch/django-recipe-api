from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe
from recipe.serializers import RecipeSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def sample_recipe(user, **params):
    """Create and return sample recipe"""
    defaults = {
        'title': 'sample recipe',
        'time_minutes': 10,
        'price': 5.00
    }

    # handy python method for updating a dictionary
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated API access"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving ingredients"""
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test private ingredients API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(email='test@test.com', password='password123')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving list of ingredients"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test that only Recipes meant for the authenticated user are returned"""
        self.other_user = get_user_model().objects.create_user(email='other@other.com', password='password123')
        sample_recipe(user=self.user)
        sample_recipe(user=self.other_user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)  # should only return a single recipe of authorized user
        self.assertEqual(res.data, serializer.data)

    # def test_create_ingredient_successful(self):
    #     """Test creating a new Ingredient"""
    #     payload = {'name': 'newingredient'}
    #     self.client.post(INGREDIENTS_URL, payload)
    #
    #     exists = Ingredient.objects.filter(user=self.user, name=payload['name']).exists()
    #     self.assertTrue(exists)
    #
    # def test_create_ingredient_invalid(self):
    #     """Test creating a Ingredient with invalid name"""
    #     payload = {'name': ''}
    #     res = self.client.post(INGREDIENTS_URL, payload)
    #
    #     self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
