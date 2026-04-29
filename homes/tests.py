from django.test import TestCase


class SmokeTest(TestCase):
    def test_health(self):
        self.assertTrue(True)
