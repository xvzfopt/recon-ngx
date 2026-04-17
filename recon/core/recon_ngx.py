# =====================================================================================
# Imports: External
# =====================================================================================
import os
import sys
import re
import requests
from requests.exceptions import HTTPError

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.core.options import Options
from recon.utils import utils
from recon.core.db import KeysDB
from recon.core.output import ConsoleOutput
from recon.core._module import ModuleManager
from recon.core.workspace import WorkspaceManager
from recon.core.interpreter import ModuleInterpreter
from recon.core.interpreter import FrameworkInterpreter

# =====================================================================================
# Recon-NGX Application Class
# =====================================================================================
class ReconNGXApp:
    '''
    Recon-NGX Core App
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    BASE_REPO_URL = 'https://raw.githubusercontent.com/xvzfopt/recon-ngx/master'

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, version, author, verbosity, stealth, analytics, marketplace, accessible) :
        super(ReconNGXApp, self).__init__()

        # Initialise Base Properties
        self._name = "recon-ngx"
        self._version = version
        self._author = author
        self._workspace = None
        self._base_prompt = "[%s]" % self._name

        # Initialise Global Options
        self._options = Options()
        self._options.initialise_global_options(self._version)

        # Initialise Console Output
        self._console = ConsoleOutput(self._options)

        # Interpreter instances
        self._f_interpreter = FrameworkInterpreter(self, self._console)
        self._active_context = self._f_interpreter
        self._m_interpreter = None

        # Set Paths
        self._app_path          = sys.path[0]
        self._home_path         = os.path.join(utils.get_user_home_path(), ".%s" % self._name)
        self._modules_path      = os.path.join(self._home_path, "modules")
        self._data_path         = os.path.join(self._home_path, "data")
        self._workspaces_path   = os.path.join(self._home_path, "workspaces")

        # Validate Parameters
        if verbosity not in [0, 1, 2]:
            self._console.error("Invalid verbosity level: '%s'. Must be 0, 1, or 2." % verbosity)
            sys.exit(1)

        # Initialise App Home
        self._init_home_dir()

        # Initialise Module Manager
        self._module_manager = ModuleManager(self._home_path, self._console, self)
        self._module_manager.fetch_marketplace_index()

        # Initialise Workspace Manager
        self._workspace_manager = WorkspaceManager(self._workspaces_path, self._console, "default")

        # Run Version Check
        self._check_version()


    def start(self, workspace_name="default"):
        '''
        Starts Recon-NGX
        '''
        self.set_workspace(workspace_name)
        self._f_interpreter.start()


    def open_module(self, fqn):
        '''
        Opens the specified module

        :param fqn: The module's Fully Qualified Name (FQN)
        :type fqn: str
        '''
        module = self._module_manager.get_module_instance(fqn)
        self._m_interpreter = ModuleInterpreter(self, self._console, module)
        self._active_context = self._m_interpreter

        while True:
            # On KeyboardInterrupt, either go back or exit app
            try:
                self._m_interpreter.start()
            except KeyboardInterrupt:
                print('')

            # Module Interpreter exited
            if self._m_interpreter.get_status() == ModuleInterpreter.STATUS_EXITED:
                return True

            break

    # =====================================================================================
    # Getters
    # =====================================================================================
    def get_latest_version_number(self):
        '''
        Gets the latest available Recon-NGX version number

        :return: The latest available Recon-NGX version number
        :rtype: str
        '''
        ver_pattern = r"version=(\d+\.\d+\.\d+).*"
        remote_ver  = 0
        url = self.BASE_REPO_URL + "/VERSION"

        # Fetch Latest Version
        try:
            r = requests.get(url)
            if not r.status_code == 200:
                raise HTTPError(r.status_code)
            remote_ver = re.search(ver_pattern, r.text).group(1)
        except Exception as ex:
            self._console.error(f"Version check failed ({type(ex).__name__}).")

        return remote_ver

    def get_version(self):
        '''
        Gets the Recon-NGX app version

        :returns: The Recon-NGX app version number
        :rtype: str
        '''
        return self._version

    def get_author(self):
        '''
        Gets the Recon-NGX app version

        :returns: The Recon-NGX app author name
        :rtype: str
        '''
        return self._author

    def get_app_name(self):
        '''
        Returns the Recon-NGX application name

        :returns: The Recon-NGX application name
        :rtype: str
        '''
        return self._name

    def get_module_manager(self):
        '''
        Gets the Module Manager instance

        :returns: The ModuleManager instance
        :rtype: ModuleManager
        '''
        return self._module_manager

    def get_workspace_manager(self):
        '''
        Gets the Workspace Manager instance

        :returns: The Workspace Manager instance
        :rtype: WorkspaceManager
        '''
        return self._workspace_manager

    def get_current_workspace(self):
        '''
        Returns the current Recon-NGX workspace instance

        :returns: The currently active Recon-NGX workspace instance
        :rtype: Workspace
        '''
        return self._workspace

    def get_console(self):
        '''
        Gets the app's ConsoleOutput instance

        :returns: The app's ConsoleOutput instance
        :rtype: ConsoleOutput
        '''
        return self._console

    def get_options(self):
        '''
        Gets the current Global Options

        :returns: Current Global Options dict
        :rtype: dict
        '''
        return self._options

    def is_marketplace_enabled(self):
        '''
        Checks if the Marketplace is currently enabled

        :returns: True if the Marketplace is enabled, otherwise False
        :rtype: bool
        '''
        # TODO TODO TODO
        return True

    # =====================================================================================
    # Setters
    # =====================================================================================
    def set_workspace(self, name):
        '''
        Sets the current workspace, creating it if necessary

        :param name: The name of the workspace
        :type name: string
        '''
        if not name:
            return

        # Create Workspace
        if not self._workspace_manager.workspace_exists(name):
            self._workspace = self._workspace_manager.create_workspace(name)
        else:
            self._workspace = self._workspace_manager.get_workspace(name)

        # Update Prompt
        self._f_interpreter.set_workspace_name(self._workspace.get_name())

        # Load Workspace configuration
        workspace_config = self._workspace.get_config_data()
        for key in self._options:
            if key in workspace_config:
                self._options[key] = workspace_config[key]

        # Reload Modules
        self._module_manager.load_modules()
        return True

    # =====================================================================================
    # Internal Functions
    # =====================================================================================
    def _init_home_dir(self):
        '''
        Sets up and initialises the Recon-NGX home directory
        '''

        # Create Directories
        if not os.path.exists(self._home_path):
            os.makedirs(self._home_path)

        # Set up Keys Database
        self._keys_db = KeysDB(os.path.join(self._home_path, "keys.db"), self._console)

    def _check_version(self):
        '''
        Checks the current version number against the latest available
        '''
        remote_ver = self.get_latest_version_number()
        if self._version != remote_ver:
            self._console.alert('Your version of Recon-NGX does not match the latest release.')
            self._console.alert('Please consider updating before further use.')
            self._console.output(f"Remote version:  {remote_ver}")
            self._console.output(f"Local version:   {self._version}")
