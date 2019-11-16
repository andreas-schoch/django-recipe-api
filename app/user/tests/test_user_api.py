from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the public users API (public = available without auth)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        payload = {
            'email': 'test@test.com',
            'password': 'test123',
            'name': 'John Doe'
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)  # make sure password is not returned to the user

    def test_user_exist(self):
        """Test if creating already existing user fails"""
        payload = {
            'email': 'test@test.com',
            'password': 'test123',
            'name': 'John Doe'
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_passowrd_too_short(self):
        """Test to make sure password cannot be shorter than 5 characters"""
        payload = {
            'email': 'test@test.com',
            'password': 'pw',
            'name': 'John Doe'
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # make sure user was not created
        # keep in mind that every test starts with fresh db, no need to worry about email existing from previous tests
        user_exists = get_user_model().objects.filter(email=payload['email']).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for user"""
        payload = {
            'email': 'test@test.com',
            'password': 'password123',
            'name': 'John Doe'
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        # check that a key named "token" exists
        # no need to test if token works since it's part of django it should have it's own unit tests
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test that no token is created hen invalid credentials are given"""
        create_user(email='test@test.com', password='wrong_password')
        payload = {'email': 'test@test.com', 'password': 'password123'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that no token is created if user doesn't exist"""
        payload = {'email': 'test@test.com', 'password': 'password123'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """test that email and password are required and not empty strings"""
        res = self.client.post(TOKEN_URL, {'email': 'test@test.com', 'password': ''})
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        res2 = self.client.post(TOKEN_URL, {'email': '', 'password': 'whatever'})
        self.assertNotIn('token', res2.data)
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
