from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Ingredient, Recipe
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsApiTests(TestCase):
    """Test the publicly available ingredients api"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving ingredients"""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """Test private ingredients API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(email='test@test.com', password='password123')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """Test retrieving list of ingredients"""
        Ingredient.objects.create(name='tomato', user=self.user)
        Ingredient.objects.create(name='lettuce', user=self.user)

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test that only ingredients meant for the authenticated user are returned"""
        self.other_user = get_user_model().objects.create_user(email='other@other.com', password='password123')
        my_ingredient = Ingredient.objects.create(name='lettuce', user=self.user)
        Ingredient.objects.create(name='whatever', user=self.other_user)

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)  # should only return a single ingredient of authorized user
        self.assertEqual(res.data[0]['name'], my_ingredient.name)

    def test_create_ingredient_successful(self):
        """Test creating a new Ingredient"""
        payload = {'name': 'newingredient'}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(user=self.user, name=payload['name']).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        """Test creating a Ingredient with invalid name"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        """Test filtering out ingredients that are not assigned to any recipes"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='ing1')
        ingredient2 = Ingredient.objects.create(user=self.user, name='ing2')
        recipe = Recipe.objects.create(user=self.user, title='recipe', time_minutes=5, price=5)
        recipe.ingredients.add(ingredient1)

        # assigned_only is a filter, meaning only ingredients assigned to recipe with the specified id returned
        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredients_assigned_unique(self):
        """Test filtering ingredients assigned returns unique items"""
        ingredient = Ingredient.objects.create(user=self.user, name='ing1')
        Ingredient.objects.create(user=self.user, name='ing2')  # second ingredient necessary for the assertion

        recipe1 = Recipe.objects.create(user=self.user, title='recipe1', time_minutes=5, price=5)
        recipe1.ingredients.add(ingredient)

        recipe2 = Recipe.objects.create(user=self.user, title='recipe2', time_minutes=5, price=5)
        recipe2.ingredients.add(ingredient)

        # assigned_only is a filter, meaning only ingredients assigned to recipes will be returned (0 or 1)
        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)  # this is why we need second ingredient, otherwise always 1
