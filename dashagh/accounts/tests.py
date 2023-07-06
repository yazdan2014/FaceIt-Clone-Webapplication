from django.test import TestCase
from model_mommy import mommy
from matches_and_ranks.models import Match

class TestMatch(TestCase):
    def setUp(self):
        self.match = mommy.make(Match)


# remember many to many has filter and get and add and remove to change the relations and also count
