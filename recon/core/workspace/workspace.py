# =====================================================================================
# Imports: External
# =====================================================================================
import os
import json

# =====================================================================================
# Imports: Internal
# =====================================================================================

# =====================================================================================
# Workspace Class
# =====================================================================================
class Workspace:
    '''
    recon-ngx Workspace
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================


    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, name, path, db):
        '''
        Constructor

        :param name: workspace name
        :type name: str
        :param path: Path to the workspace
        :type path: str
        :param db: The database instance for this workspace
        :type db: WorkspaceDB
        '''
        self._name = name
        self._path = path
        self._db = db
        self._config_data = {}

        # Process Config
        self._config_path = os.path.join(self._path, 'config.dat')
        if os.path.isfile(self._config_path):
            self._config_data = self._load_config(self._config_path)

    def _load_config(self, path):
        '''
        Loads the specified Workspace configuration file

        :param path: Path to the Workspace configuration file
        :type path: str
        '''
        config_data = {}

        # Read config data from file
        with open(path, "r") as config_file:
            try:
                config_data = json.loads(config_file.read())
            except ValueError:
                pass

        return config_data

    def set_config_property(self, option_name, module='base', options=None):
        '''
        Sets a specific configuration property and writes it to disk
        '''
        # Initialise config file
        open(self._config_path, 'a').close()

        # Read existing contents
        config_data = {}
        with open(self._config_path) as config_file:
            try:
                config_data = json.loads(config_file.read())
            except ValueError:
                pass

        # Create a container for the current module
        if module not in config_data:
            config_data[module] = {}

        # Set the new option value in the config
        config_data[module][option_name] = options[option_name]

        # Remove the option if it has been unset
        if config_data[module][option_name] is None:
            del config_data[module][option_name]

        # Remove the module container if it is empty
        if not config_data[module]:
            del config_data[module]

        # write the new config data to the config file
        with open(self._config_path, 'w') as config_file:
            json.dump(config_data, config_file, indent=4)

    def get_mod_time(self):
        '''
        Gets the Modification Time of this workspace

        :return: The Modification Time of this workspace
        :rtype: str
        '''
        return self.get_db().get_mod_time()

    def get_name(self):
        '''
        Gets the workspace name

        :return: the name of this workspace
        :rtype: str
        '''
        return self._name

    def get_path(self):
        '''
        Gets the path to the workspace directory

        :return: the path to the workspace directory
        :rtype: str
        '''
        return self._path

    def get_db(self):
        '''
        Gets the database instance for this workspace

        :return: The database instance for this workspace
        :rtype: WorkspaceDB
        '''
        return self._db

    def get_db_path(self):
        '''
        Gets the path to the Workspace's Database

        :return: the path to the Workspace's Database
        :rtype: str
        '''
        return self._db.get_path()

    def get_config_data(self):
        '''
        Gets the config data for this workspace

        :return: The Workspace config data
        :rtype: dict
        '''
        return self._config_data