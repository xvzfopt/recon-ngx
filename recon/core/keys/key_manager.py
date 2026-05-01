# =====================================================================================
# Imports: External
# =====================================================================================
import os
import inspect

# =====================================================================================
# Imports Internal
# =====================================================================================
from recon.core.db import KeysDB

# =====================================================================================
# Key Manager Class
# =====================================================================================
class KeyManager:
    '''
    Manages API Keys
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    KEYS_DB_FILENAME = "keys.db"

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, home_path, console):
        '''
        Constructor
        '''
        self._console = console
        self._home_path = home_path
        self._db_path = os.path.join(self._home_path, self.KEYS_DB_FILENAME)

        # Initialise Keys Database
        self._db = KeysDB(self._db_path, self._console)

    def add_key(self, name, value):
        '''
        Adds an API Key with the specified name and value

        :param name: The name of the API Key
        :type name: str
        :param value: The API Key
        :type value: str
        '''
        if name in self.get_keys():
            self._console.debug("Key with name '%s' already exists. Updating value" % name)
            return self._query('UPDATE keys SET value=? WHERE name=?', (value, name))
        return self._query('INSERT INTO keys VALUES (?, ?)', (name, value))

    def remove_key(self, name):
        '''
        Removes the API key with the specified name

        :param name: The name of the API Key to remove
        :type name: str
        '''
        return self._query('DELETE FROM keys WHERE name=?', (name,))

    def clear_keys(self):
        '''
        Clears all API Keys
        '''
        return self._query('DELETE FROM keys')

    def get_keys(self):
        '''
        Gets the list of available API Keys

        :return: list of API Keys
        :rtype: list
        '''
        return self._query("SELECT * FROM keys")

    def get_key_value(self, name):
        '''
        Gets the value of the specified API key, returning None if not found

        :param name: The name of the target API Key
        :type name: str
        '''
        value = None
        results = self._query('SELECT value FROM keys WHERE name=? AND value NOT NULL', (name,))
        if results:
            value = results[0][0]
        return value

    def get_keys_count(self):
        '''
        Gets the current count of API Keys

        :return: count of API Keys
        :rtype: int
        '''
        return len(self.get_keys())

    def get_key_names(self):
        '''
        Gets the list of current API Key names

        :return: list of API Key names
        :rtype: list
        '''
        return [key[0] for key in self._query('SELECT name FROM keys')]

    # =====================================================================================
    # Internal Helpers
    # =====================================================================================
    def _query(self, query, values=()):
        '''
        Keys Database query function. Gets, adds, removes and updates Keys DB records

        :param query: The query to execute
        :type query: str
        :param values: List of query placeholder values
        :type values: list
        '''
        result = self._db.query(query, values)
        # filter out tokens when not called from the get_key method
        if type(result) is list and 'get_key' not in [x[3] for x in inspect.stack()]:
            result = [x for x in result if not x[0].endswith('_token')]
        return result
