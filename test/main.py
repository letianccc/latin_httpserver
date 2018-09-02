import unittest


test_dir = 'ftp'
discover = unittest.defaultTestLoader.discover(test_dir)

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(discover)
