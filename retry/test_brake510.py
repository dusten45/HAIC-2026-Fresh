import unittest
from retry.brake510_common import caps
from retry.brake509_adapter import native_caps


class BridgeBudgetTests(unittest.TestCase):
    def test_every_branch_reserved(self):
        c=caps();self.assertEqual(c['synthetic_worlds'],4);self.assertEqual(c['synthetic_ticks'],48)
        self.assertEqual(c['native_total_ticks'],358);self.assertEqual(c['all_positive_ticks'],406)
        self.assertEqual(c['all_worlds'],6);self.assertEqual(c['synthetic_zero_primes'],4)
        self.assertEqual(c['native_actions'],native_caps()['actions']);self.assertEqual(c['native_resets'],2)
        self.assertEqual(26027-c['native_actions'],25963)


if __name__=='__main__':unittest.main()
