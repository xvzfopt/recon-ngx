# =====================================================================================
# Imports: External
# =====================================================================================

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.core.keys import KeyManager
from recon.core.output import ConsoleOutput
from test.abs_testcase import AbsTestCase

# =====================================================================================
# Key Manager Test Case Class
# =====================================================================================
class TestKeyManager(AbsTestCase):
    '''
    BaseModule Test Case
    '''

    # =====================================================================================
    # General Methods
    # =====================================================================================
    def setUp(self):
        '''
        Key Manager Test Case Set up
        '''
        super(TestKeyManager, self).setUp()
        self._console = ConsoleOutput(self._options)
        self._options["verbosity"] = 2
        self._km = KeyManager(self.HOME_PATH, self._console)

    # =====================================================================================
    # Test Methods
    # =====================================================================================
    def test_add_get_key(self):
        '''
        Tests that we can get and add API keys
        '''
        self.assertEmpty(self._km.get_keys())

        # Test with simple key
        key = ("my_test_key", "password123")
        self._km.add_key(key[0], key[1])

        # Check key was added
        self.assertEqual(self._km.get_keys_count(), 1)
        self.assertEqual(self._km.get_keys()[0], key)

        # Add another key and check
        key = ("my_test_key2", "password123")
        self._km.add_key(key[0], key[1])
        self.assertEqual(self._km.get_keys_count(), 2)
        self.assertEqual(self._km.get_keys()[1], key)

        # Clear keys and check empty
        self._km.clear_keys()
        self.assertEmpty(self._km.get_keys())

    def test_get_key_value(self):
        '''
        Tests that we can get the value of a specific API key
        '''

        # Check initial empty set
        self.assertEmpty(self._km.get_keys())

        # Add some keys and check
        key1 = ("my_test_key1", "password123")
        key2 = ("my_test_key2", "password123")
        self._km.add_key(key1[0], key1[1])
        self._km.add_key(key2[0], key2[1])
        self.assertEqual(self._km.get_keys_count(), 2)
        self.assertIn("my_test_key2", self._km.get_key_names())

        # Test getting key value
        key1_value = self._km.get_key_value("my_test_key1")
        self.assertEqual("password123", key1_value)
        key2_value = self._km.get_key_value("my_test_key2")
        self.assertEqual("password123", key2_value)

    def test_has_key(self):
        '''
        Tests that we can check if a key exists
        '''

        # Initial check
        self.assertFalse(self._km.has_key("my_test_key1"))

        # Add Key and re-check
        key1 = ("my_test_key1", "password123")
        self._km.add_key(key1[0], key1[1])
        self.assertTrue(self._km.has_key("my_test_key1"))

    def test_remove_keys(self):
        '''
        Tests that we can remove specific API keys
        '''

        # Check initial empty set
        self.assertEmpty(self._km.get_keys())

        # Add keys and check
        key1 = ("my_test_key1", "password123")
        key2 = ("my_test_key2", "password123")
        self._km.add_key(key1[0], key1[1])
        self._km.add_key(key2[0], key2[1])
        self.assertEqual(self._km.get_keys_count(), 2)
        self.assertIn("my_test_key2", self._km.get_key_names())

        # Remove specific key and test
        self._km.remove_key("my_test_key2")
        self.assertNotIn("my_test_key2", self._km.get_key_names())

    def test_clear_keys(self):
        '''
        Tests that we can clear all API keys
        '''

        # Check initial empty set
        self.assertEmpty(self._km.get_keys())

        # Add keys and check
        key1 = ("my_test_key1", "password123")
        key2 = ("my_test_key2", "password123")
        self._km.add_key(key1[0], key1[1])
        self._km.add_key(key2[0], key2[1])
        self.assertEqual(self._km.get_keys_count(), 2)

        # Clear keys and check
        self._km.clear_keys()
        self.assertEmpty(self._km.get_keys())
        self.assertEqual(self._km.get_keys_count(), 0)


    def test_get_keys_count(self):
        '''
        Tests that we can get a count of API Keys
        '''

        # Check initial count
        self.assertEqual(0, self._km.get_keys_count())

        # Add key and check new count
        key = ("my_test_key1", "password123")
        self._km.add_key(key[0], key[1])
        self.assertEqual(1, self._km.get_keys_count())

        # Add another key and check count
        # Add key and check new count
        key = ("my_test_key2", "password123")
        self._km.add_key(key[0], key[1])
        self.assertEqual(2, self._km.get_keys_count())

        # Clear keys and check count is 0
        self._km.clear_keys()
        self.assertEqual(0, self._km.get_keys_count())

    def test_get_key_names(self):
        '''
        Tests that we can get API Key Names
        '''

        # Check initial set
        self.assertEmpty(self._km.get_key_names())

        # Add key and check names list
        key = ("my_test_key1", "password123")
        self._km.add_key(key[0], key[1])
        self.assertLength(1, self._km.get_key_names())
        self.assertIn("my_test_key1", self._km.get_key_names())

        # Add second key
        key = ("my_test_key2", "password123")
        self._km.add_key(key[0], key[1])
        self.assertLength(2, self._km.get_key_names())
        self.assertIn("my_test_key2", self._km.get_key_names())

        # Clears keys and re-check
        self._km.clear_keys()
        self.assertEmpty(self._km.get_key_names())

