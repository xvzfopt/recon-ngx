# =====================================================================================
# Imports: External
# =====================================================================================
import os
import sys
import re
import requests
from cmd import Cmd
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

# =====================================================================================
# Recon-NGX Framework
# =====================================================================================
class ReconNGXFramework(Cmd):
    '''
    Recon-NGX Core Framework
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    BASE_REPO_URL = 'https://raw.githubusercontent.com/xvzfopt/recon-ngx/master'

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, version, author, verbosity, stealth, analytics, marketplace, accessible) :
        super(ReconNGXFramework, self).__init__()

        # Initialise Base Properties
        self._name = "recon-ngx"
        self._version = version
        self._author = author
        self._workspace = None
        self._base_prompt = "[%s]" % self._name

        # Initialise Global Options
        self._g_options = Options()
        self._g_options.initialise_global_options(self._version)

        # Initialise Console Output
        self._console = ConsoleOutput(self._g_options)

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
        self._console.print_banner(self._version, self._author, self._module_manager.get_module_categories())

        # !!! MAIN LOOP !!!
        self.cmdloop()

    # =====================================================================================
    # Command Handler Functions
    # =====================================================================================
    def default(self, line):
        self._console.error("Invalid command: %s" % line)

    def precmd(self, line):
        '''
        !!! CMD PROCESSOR !!!
        Preprocess function. Performs preprocessing and modification of user input

        :param line: The line that was entered by the end-user
        :type line: str
        '''
        return line


    def onecmd(self, line):
        '''
        !!! CMD PROCESSOR !!!
        Main Command/Input processing function. Handles input and delegates further processing

        :param line: The line that was entered by the end-user
        :type line: str
        '''
        # Parse line
        cmd, arg, line = self.parseline(line)

        # Input: Empty Line
        if not line or not cmd:
            return self.emptyline()

        # Find target function
        try:
            func = getattr(self, "do_%s" % cmd)
        except AttributeError:
            return self.default(line)

        # Delegate Action to target function
        try:
            return func(arg)
        except Exception:
            self._console.print_exception()


    # =====================================================================================
    # Action/Do Functions
    # =====================================================================================
    def do_exit(self, params):
        self._exit = 1
        return True

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
        self.prompt = "%s[%s] " % (self._base_prompt, name)

        # Load Workspace configuration
        workspace_config = self._workspace.get_config_data()
        for key in self._g_options:
            if key in workspace_config:
                self._g_options[key] = workspace_config[key]

        # Reload Modules
        self._module_manager.load_modules()

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


