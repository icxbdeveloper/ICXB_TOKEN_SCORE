from ..icxb import ICONBET
from tbears.libs.scoretest.score_test_case import ScoreTestCase


class TestICONBET(ScoreTestCase):

    def setUp(self):
        super().setUp()
        self.score = self.get_score_instance(ICONBET, self.test_account1)

    def test_hello(self):
        self.assertEqual(self.score.hello(), "Hello")
