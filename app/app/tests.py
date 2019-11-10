from django.test import TestCase
from app.calc import add


class CalcTests(TestCase):
    def test_add_numbers(self):  # needs to start with test, otherwise ignored when tests are run
        """ Test that two numbers are added together"""
        self.assertEqual(add(5, 5), 10)