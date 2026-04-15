# =====================================================================================
# Imports: External
# =====================================================================================
import os
import re
from cmd import Cmd

# =====================================================================================
# Imports: Internal
# =====================================================================================
# from recon.core.recon_ngx import ReconNGXApp

# =====================================================================================
# Base Command Interpreter Class
# =====================================================================================
class BaseInterpreter(Cmd):
    '''
    Base Recon-NGX Command Interpreter. Abstract class - Not to be instantiated directly.
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    RULER = '-'
    SPACER = '  '

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, recon, console):
        '''
        Constructor

        :param recon: The ReconNGX App instance
        :type recon: ReconNGXApp
        :param console: The console output instance
        :type console: ConsoleOutput
        '''
        super(BaseInterpreter, self).__init__()
        self._recon = recon
        self._console = console

        self._base_prompt = "[%s]" % self._recon.get_app_name()


    def start(self):
        '''
        Starts the interpreter session
        '''
        self.print_banner()
        self.cmdloop()

    def print_banner(self):
        '''
        Prints the Recon-NGX Banner
        '''
        module_manager = self._recon.get_module_manager()
        self._console.print_banner(
            self._recon.get_version(),
            self._recon.get_author(),
            module_manager.get_module_categories()
        )

    # =====================================================================================
    # Cmd Override Functions
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

        '''
        We have an interpreter/executor package containing several executors, or exeuctor contexts
            1. BaseExecutor (all inherit from). Contains executions common across executors
            2. FrameworkExecutor. The default context used outside of a module
            3. ModuleExecutor. The executor context used when a module is the focus
        '''

        # Delegate Action to target function
        try:
            return func(arg)
        except Exception:
            self._console.print_exception()

    # =====================================================================================
    # Command Functions
    # =====================================================================================
    def do_exit(self, params):
        '''
        Action Handler: exit
        '''
        self._exit = 1
        return True

    # =====================================================================================
    # Command Do Functions: "modules"
    # =====================================================================================
    def do_modules(self, params):
        '''Interfaces with installed modules'''
        # Check modules subcommand was provided
        if not params:
            self.help_modules()
            return

        arg, params = self._parse_params(params)

        # Check modules subcommand is valid
        if arg in self._get_subcommands("modules"):
            return getattr(self, '_do_modules_'+arg)(params)
        else:
            self.help_modules()

    def _do_modules_search(self, params):
        '''Searches installed modules'''
        mm = self._recon.get_module_manager()
        modules = [x for x in mm.get_loaded_modules()]

        # Check module name was provided
        if params:
            self._console.output(f"Searching installed modules for '{params}'...")
            modules = [x for x in mm.get_loaded_modules() if re.search(params, x)]

        # Display matching modules
        if modules:
            self._list_modules(modules)
        else:
            self._console.error('No modules found.')
            self._help_modules_search()

    def _do_modules_load(self, params):
        '''Loads a module'''
        # # validate global options before loading the module
        # TODO
        # try:
        #     self._validate_options()
        # except framework.FrameworkException as e:
        #     self.console.error(e)
        #     return
        # if not params:
        #     self._help_modules_load()
        #     return

        # Check module name was provided
        if not params:
            self._help_modules_load()
            return

        # Find matching modules
        mm = self._recon.get_module_manager()
        modules = mm.find_matching_installed_modules(params)

        # Error: No matching modules found, OR multiple
        if len(modules) != 1:
            if not modules:
                self._console.error('Invalid module name.')
            else:
                self._console.output(f"Multiple modules match '{params}'.")
                self._list_modules(modules)
            return

        # Load Module
        self._recon.open_module(modules[0])

    def _do_modules_reload(self, params):
        '''Reloads installed modules'''
        self._console.output('Reloading modules...')
        mm = self._recon.get_module_manager()
        mm.load_modules()

    # =====================================================================================
    # Command Help Functions
    # =====================================================================================
    def help_modules(self):
        print(getattr(self, 'do_modules').__doc__)
        print(f"{os.linesep}Usage: modules <{'|'.join(self._get_subcommands('modules'))}> [...]{os.linesep}")

    def _help_modules_search(self):
        print(getattr(self, '_do_modules_search').__doc__)
        print(f"{os.linesep}Usage: modules search [<regex>]{os.linesep}")

    def _help_modules_load(self):
        print(getattr(self, '_do_modules_load').__doc__)
        print(f"{os.linesep}Usage: modules load <path>{os.linesep}")

    # =====================================================================================
    # Setters
    # =====================================================================================
    def set_workspace_name(self, name):
        '''
        Sets the current workspace name
        '''
        self.prompt = "%s[%s] " % (self._base_prompt, name)

    # =====================================================================================
    # Helpers
    # =====================================================================================
    def _list_modules(self, modules):
        '''
        Prints the specified list of modules

        :param modules: The list of modules to display
        :type modules: list
        '''
        if modules:
            key_len = len(max(modules, key=len)) + len(self.SPACER)
            last_category = ''
            for module in sorted(modules):
                category = module.split('/')[0]
                if category != last_category:
                    # print header
                    last_category = category
                    self._console.heading(last_category)
                # print module
                print(f"{self.SPACER * 2}{module}")
        else:
            print('')
            self._console.alert('No modules enabled/installed.')
        print('')

    def _parse_params(self, params):
        '''
        Parses command/action parameter string into an argument and its sub-parameters

        :param params: The parameter string
        :type params: str
        :returns: Tuple containing 1) argument and 2) parameter list
        :rtype: tuple(str, list)
        '''
        params = params.split()
        arg = ''
        if params:
            arg = params.pop(0)
        params = ' '.join(params)
        return arg, params


    def _get_subcommands(self, command):
        '''
        Gets available subcommands for a specific command

        :param command: The command to get available subcommands for
        :type command: str
        :returns: A list of available subcommands
        :rtype: list
        '''
        subcommands = []
        for method in dir(self):
            if "_do_%s_" % command in method:
                subcommands.append(method.split("_")[-1])
        return subcommands
