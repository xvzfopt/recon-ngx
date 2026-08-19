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
from recon.core.module import ModuleManager
from recon.core.workspace import WorkspaceManager
from recon.core.interpreter import ModuleInterpreter
from recon.core.interpreter import FrameworkInterpreter
from recon.core.keys import KeyManager
from recon.sdk.exceptions import *
from recon.core.exceptions import *

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
    def __init__(self, version, author, verbosity, check_version, marketplace_enabled, accessible, modules_path,
                 marketplace_branch) :
        '''
        Recon-NGX Core App Consructor

        :param version: The Recon-NGX app version
        :type version: str
        :param author: The Recon-NGX app author
        :type author: str
        :param verbosity: The Recon-NGX app verbosity level
        :type verbosity: int
        :param check_version: Whether the app should check to see if updates are available
        :type check_version: bool
        :param marketplace_enabled: Whether the marketplace is enabled
        :type marketplace_enabled: bool
        :param modules_path: A modules path override to load modules from a custom directory
        :type modules_path: str
        :param marketplace_branch: The branch to use for the module marketplace
        :type marketplace_branch: str
        '''
        super(ReconNGXApp, self).__init__()

        # Initialise Base Properties
        self._name = "recon-ngx"
        self._displayname = "Recon-NGX"
        self._version = version
        self._author = author
        self._workspace = None
        self._marketplace_enabled = marketplace_enabled
        self._base_prompt = "[%s]" % self._name
        self._script_path = None
        self._is_running_script = False

        # Initialise Global Options
        self._options = Options()
        self._options.initialise_global_options(self._version)

        # Initialise Console Output
        self._console = ConsoleOutput(self._options, accessible)

        # Interpreter instances
        self._f_interpreter = FrameworkInterpreter(self, self._console)
        self._active_context = self._f_interpreter
        self._m_interpreter = None

        # Set Paths
        self._app_path          = sys.path[0]
        self._home_path         = os.path.join(utils.get_user_home_path(), ".%s" % self._name)
        self._modules_path      = os.path.join(self._home_path, "modules")
        self._workspaces_path   = os.path.join(self._home_path, "workspaces")

        # =====================================================================================
        # Validate Arguments
        # =====================================================================================
        # Check Modules Path
        if modules_path:
            if not os.path.isdir(modules_path):
                self._console.error("Invalid modules path specified: '%s'. Check that this is a valid directory" % modules_path)
                sys.exit(1)
            self._modules_path = modules_path

        # Check Verbosity
        if verbosity not in [0, 1, 2]:
            self._console.error("Invalid verbosity level: '%s'. Must be 0, 1, or 2." % verbosity)
            sys.exit(1)
        self.set_verbosity(verbosity)

        # Check Marketplace Branch
        if marketplace_branch not in ["develop", "master"]:
            self._console.error(f"Invalid Marketplace branch specified: '{marketplace_branch}'")
            sys.exit(1)

        # Initialise App Home
        self._init_home_dir()

        # Initialise Module Manager
        self._module_manager = ModuleManager(self._home_path, self._modules_path, self._console, self, marketplace_branch)
        if self.is_marketplace_enabled():
            self._module_manager.fetch_marketplace_index()

        # Initialise Workspace Manager
        self._workspace_manager = WorkspaceManager(self._workspaces_path, self._console, "default")

        # Initialise Key Manager
        self._key_manager = KeyManager(self._home_path, self._console)

        # Run Version Check
        if check_version:
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

        # Load Workspace Module Config
        module_config = self._workspace.get_module_config_data(module.get_fqn())
        module_options = module.get_options()
        for option_name in module_config:
            module_options[option_name] = module_config[option_name]

        # Module Main
        while True:
            # On KeyboardInterrupt, either go back or exit app
            try:
                self._m_interpreter.start()
            except KeyboardInterrupt:
                print('')

            # Module Interpreter exited
            if self._m_interpreter.get_status() == ModuleInterpreter.STATUS_EXITED:
                return True
            # Module Interpreter reloaded
            if self._m_interpreter.get_status() == ModuleInterpreter.STATUS_RELOADED:
                self._console.output("Reloading module...")

                # Create new instance of loaded module
                module = self._m_interpreter.get_module()
                is_loaded, new_module = self._module_manager.reload_module(module)

                # Module reloaded successfully: don't exit back to framework
                if is_loaded:
                    self._m_interpreter.reload(new_module)
                    continue
            break

    def validate_options(self, module=None):
        '''
        Validates the Global Recon-NGX options. Throws a ValidationException if validation fails.

        :param module: If option validation is being performed for a module, this should be the Module for which
            validation is being performed. Optional
        :type module: BaseModule, optional
        :raises: ValidationException
        '''
        # Validate Module Options if set
        if module:
            for option_name in module.get_options():
                self.validate_module_option(option_name, module)

        # Validate Global options
        for option_name in self.get_options():
            self.validate_global_option(option_name, self.get_options())

    def validate_global_option(self, option_name, options):
        '''
        Validates a single global/framework option

        :param option_name: The name of the global option to validate
        :type option_name: str
        :param options: The Options object containing the option
        :type options: Options
        '''

        # If Option is required, make sure it's set
        if self.is_option_required(option_name, options):
            if not self.is_option_set(option_name, options):
                raise ValidationException("Value required for the '%s' option." % option_name)

    def validate_module_option(self, option_name, module):
        '''
        Validates a single module option

        :param option_name: The name of the global option to validate
        :type option_name: str
        :param module: The Module for which validation is being performed
        :type module: BaseModule
        '''
        options = module.get_options()

        # If Option is required, make sure it's set
        if self.is_option_required(option_name, options):
            if not self.is_option_set(option_name, options):
                raise ModuleValidationException("Value required for the '%s' option." % option_name)

        # Perform any option validation
        if options.validators.get(option_name):
            for validator in options.validators[option_name]:
                if not validator.validate(options[option_name], module):
                    raise ModuleValidationException(f"Validation failed for the '{option_name}' option => %s" % validator.get_error())

    def execute_script(self, path):
        '''
        Executes a script file. To be called when a script is automatically passed via the CLI

        :param path: The path of the script to be executed
        :type path: str
        '''
        # Expand Path
        path = os.path.expanduser(path)

        # Load script into stdin
        if os.path.exists(path):
            # works even when called before Recon.start due
            # to stdin waiting for the interactive prompt
            self._console.code_line("Script Execution Started --> %s" % path)
            sys.stdin = open(path)
            self._is_running_script = True
        else:
            self._console.error(f"Script file '{path}' not found.")

    def record_script_line(self, line):
        '''
        Records a line to the current script file

        :param line: The line to record
        :type line: str
        '''
        with open(self._script_path, "a") as script_file:
            script_file.write(f"{line}{os.linesep}")

    def stop_recording(self):
        '''
        Stops Recording lines to current script file
        '''
        self._script_path = None

    def start_recording(self, path):
        '''
        Starts recording lines to the target script file

        :param path: The target script file path
        :type path: str
        '''
        open(path, 'w').close()
        self._script_path = path

    def read_input(self, prompt, default=None):
        '''
        Reads input from the user via the console. This is really just an override for the Console
        read() function, but enables us to also record input

        :param prompt: The prompt to present to the user
        :type prompt: str
        :param default: The default value to return if no input is provided. Defaults to None
        :type default: any, Optional
        :returns: The input entered by the user
        :type: str
        '''
        content = self._console.read(prompt, default, self.is_running_script())

        # Check if recording
        if self.is_recording():
            with open(self.get_script_path(), "a") as script_file:
                script_file.write(f"{content}{os.linesep}")

        return content

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
        return self._displayname

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

    def get_key_manager(self):
        '''
        Gets the API Key Manager instance

        :returns: The API Key Manager instance
        :rtype: KeyManager
        '''
        return self._key_manager

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
        :rtype: Options
        '''
        return self._options

    def get_option_value(self, option_name):
        '''
        Gets the value of the specified option. Returns None if the option does not have a value
        Note: This function expects that you have already checked that the option exists

        :param option_name: The name of the option to retrieve the value of
        :type option_name: str
        :returns: The value of the specified option
        :rtype: TODO
        '''
        return self.get_options()[option_name]

    def is_option_set(self, option_name, options=None):
        '''
        Checks if the specified option is currently set

        :param option_name: The name of the option to check
        :type option_name: str
        :param options: Optional Options instance override. Defaults to Global Options if not set
        :type options: Options
        :returns: True if the option is currently set, otherwise False
        :rtype: bool
        '''
        # If no options override, use global options
        if not options:
            options = self.get_options()

        is_set = False
        if option_name in options:
            value = options[option_name]

            # If option is bool or int, then it's implicitly set
            if type(value) in [bool, int]:
                is_set = True
            # Otherwise, check for a valid (non-null) value
            else:
                if value:
                    is_set = True
        return is_set

    def is_option_required(self, option_name, options=None):
        '''
        Checks is the specified option is required

        :param option_name: The name of the option to check
        :type option_name: str
        :param options: Optional Options instance override. Defaults to Global Options if not set
        :type options: Options
        :returns: True if the option is required, otherwise False
        :rtype: bool
        '''
        # If no options override, use global options
        if not options:
            options = self.get_options()
        return options.required[option_name]


    def is_marketplace_enabled(self):
        '''
        Checks if the Marketplace is currently enabled

        :returns: True if the Marketplace is enabled, otherwise False
        :rtype: bool
        '''
        return self._marketplace_enabled

    def get_verbosity(self):
        '''
        Gets the current verbosity level

        :returns: The current verbosity level
        :rtype: int
        '''
        return self.get_option_value("verbosity")

    def get_home_path(self):
        '''
        Gets the Recon-NGX application home path

        :returns: The absolute path to the Recon-NGX app home directory
        :type: str
        '''
        return self._home_path

    def get_script_path(self):
        '''
        Gets the path file that the interpreter is currently recording a script to

        :returns: Recording script path
        :rtype: str
        '''
        return self._script_path

    def is_recording(self):
        '''
        Checks if a script is currently being recorded

        :returns: True if a script is currently being recorded, otherwise False
        :rtype: bool
        '''
        return self._script_path is not None

    def is_running_script(self):
        '''
        Checks if a script is currently being executed

        :returns: True if a script is currently being executed, otherwise False
        :rtype: bool
        '''
        return self._is_running_script

    # =====================================================================================
    # Setters
    # =====================================================================================
    def set_workspace(self, name, load_modules=True):
        '''
        Sets the current workspace, creating it if necessary

        :param name: The name of the workspace
        :type name: string
        :param load_modules: (test only) Whether to load modules. Used as an override to skip loading of all modules
                when running in test mode, where only a single module is going to be loaded
        :type load_modules: bool
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

        # Load Workspace Base Configuration
        base_config = self._workspace.get_base_config_data()
        for key in self._options:
            if key in base_config:
                self._options[key] = base_config[key]

        # Load Modules
        if load_modules:
            self._module_manager.load_modules()
        return True

    def set_verbosity(self, verbosity):
        '''
        Sets the current verbosity level

        :param verbosity: The new verbosity level
        :type verbosity: int
        '''
        self.get_options()["verbosity"] = verbosity

    def finish_script_execution(self):
        '''
        Finishes the execution of a script and performs any post-execution cleanup
        '''
        self._is_running_script = False
        self._console.write("")
        self._console.code_line("Script Execution Finished")

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
