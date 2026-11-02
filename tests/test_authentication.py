import unittest

from runtime_check import check_authentication


class AuthenticationTests(unittest.TestCase):
    def test_pyatv_can_authenticate_against_an_offline_srp_peer(self):
        check_authentication()


if __name__ == "__main__":
    unittest.main()
