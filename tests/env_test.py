import sys
import unittest


class MyTestCase(unittest.TestCase):
    def test_something(self):
        print(sys.executable)
        import pixivpy3
        import tweepy


if __name__ == '__main__':
    unittest.main()
