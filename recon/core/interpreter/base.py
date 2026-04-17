# =====================================================================================
# Imports: External
# =====================================================================================
import os
import re
from cmd import Cmd

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.utils import utils


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

    STATUS_EXITED   = 0
    STATUS_RUNNING  = 1
    STATUS_RELOADED = 2

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
        self._status = None

        self._base_prompt = "[%s]" % self._recon.get_app_name()


    def start(self):
        '''
        Starts the interpreter session
        '''
        self.print_banner()
        self._status = self.STATUS_RUNNING
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
    # Command Functions: Back/Exit
    # =====================================================================================
    def do_exit(self, params):
        '''
        Action Handler: exit
        '''
        self._status = self.STATUS_EXITED
        return True

    def do_back(self, params):
        '''
        Action Handler: Back
        '''
        self._status = self.STATUS_EXITED
        return True

    # =====================================================================================
    # Command Do Functions: "options"
    # =====================================================================================
    def do_options(self, params):
        '''Manages the current context options'''

        # Check options subcommand was provided
        if not params:
            self.help_options()
            return
        arg, params = self._parse_params(params)

        # Check subcommand is valid
        if arg in self._get_subcommands('options'):
            return getattr(self, '_do_options_'+arg)(params)
        else:
            self.help_options()

    def _do_options_list(self, params):
        '''Shows the current context options'''
        self._list_options()

    def _do_options_set(self, params):
        '''Sets a current context option'''

        # Parse option key and value
        option, value = self._parse_params(params)
        if not (option and value):
            self._help_options_set()
            return

        # Get Workspace
        workspace = self._recon.get_current_workspace()

        # Check option is a valid, known Global Option
        options = self._recon.get_options()
        option_name = option.upper()
        if option_name in options:
            options[option_name] = value
            print(f"{option_name} => {value}")
            workspace.set_config_property(option_name, options=options)
        else:
            self._console.error('Invalid option name.')

    def _do_options_unset(self, params):
        '''Unsets a current context option'''

        # Parse option key and value
        option, value = self._parse_params(params)
        if not option:
            self._help_options_unset()
            return

        options = self._recon.get_options()
        option_name = option.upper()
        if option_name in options:
            self._do_options_set(' '.join([option_name, 'None']))
        else:
            self._console.error('Invalid option name.')

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
    # Auto-completion Functions: modules
    # =====================================================================================
    def complete_modules(self, text, line, *ignored):
        '''
        Auto-completion for modules commands

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :param line: The entire line that has been typed so far
        :type line: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''

        arg, params = self._parse_params(line.split(' ', 1)[1])
        subs = self._get_subcommands('modules')

        # If directly matching sub-command found, auto-complete that
        if arg in subs:
            return getattr(self, '_complete_modules_'+arg)(text, params)

        # Else return all available matching commands
        return [sub for sub in subs if sub.startswith(text)]

    def _complete_modules_search(self, text, *ignored):
        '''
        Auto-completion for modules command: search
        Placeholder: currently we have nothing more to provide for this command

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        return []
    # Auto-complete modules "reload" command in same way as search
    _complete_modules_reload = _complete_modules_search

    def _complete_modules_load(self, text, *ignored):
        '''
        Auto-completion for modules command: load
        Searches all installed modules for those that match

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        mm = self._recon.get_module_manager()
        return [x for x in mm.get_loaded_modules() if x.startswith(text)]

    # =====================================================================================
    # Auto-completion Functions: options
    # =====================================================================================
    def complete_options(self, text, line, *ignored):
        '''
        Auto-completion for options commands

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :param line: The entire line that has been typed so far
        :type line: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        arg, params = self._parse_params(line.split(' ', 1)[1])
        subs = self._get_subcommands('options')

        # If directly matching sub-command found, auto-complete that
        if arg in subs:
            return getattr(self, '_complete_options_'+arg)(text, params)

        # Else return all available matching commands
        return [sub for sub in subs if sub.startswith(text)]

    def _complete_options_list(self, text, *ignored):
        '''
        Auto-completion for options command: list
        Placeholder: currently we have nothing more to provide for this command

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        return []

    def _complete_options_set(self, text, *ignored):
        '''
        Auto-completion for options command: set
        Searches all global options for an option that matches

        :param text: The option name to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        return [x for x in self._recon.get_options() if x.startswith(text.upper())]
    # Auto-complete options "unset" in same way as set
    _complete_options_unset = _complete_options_set


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

    def help_options(self):
        print(getattr(self, 'do_options').__doc__)
        print(f"{os.linesep}Usage: options <{'|'.join(self._get_subcommands('options'))}> [...]{os.linesep}")

    def _help_options_set(self):
        print(getattr(self, '_do_options_set').__doc__)
        print(f"{os.linesep}Usage: options set <option> <value>{os.linesep}")

    def _help_options_unset(self):
        print(getattr(self, '_do_options_unset').__doc__)
        print(f"{os.linesep}Usage: options unset <option>{os.linesep}")


    # =====================================================================================
    # Getters
    # =====================================================================================
    def get_status(self):
        '''
        Gets the interpreter's status

        :returns: The interpreter's status enum int
        :rtype: int
        '''
        return self._status

    # =====================================================================================
    # Setters
    # =====================================================================================
    def set_workspace_name(self, name):
        '''
        Sets the current workspace name
        '''
        self.prompt = "%s[%s] > " % (self._base_prompt, name)

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


    def _list_options(self, options=None):
        '''
        Display the options that are available.
        If a dictionary is passed in then this will be used, otherwise the interpreter will fall back to the global
        options

        :param options: The options to display
        :type options: dict
        '''

        # Use run-time options if provided, otherwise use Global Options
        if options is None:
            options = self._recon.get_options()

        # Copied across form recon-ng
        if options:
            pattern = f"{self.SPACER}%s  %s  %s  %s"
            key_len = len(max(options, key=len))
            if key_len < 4: key_len = 4
            val_len = len(max([utils.to_unicode_str(options[x]) for x in options], key=len))
            if val_len < 13: val_len = 13
            print('')
            print(pattern % ('Name'.ljust(key_len), 'Current Value'.ljust(val_len), 'Required', 'Description'))
            print(pattern % (self.ruler*key_len, (self.ruler*13).ljust(val_len), self.ruler*8, self.ruler*11))
            for key in sorted(options):
                value = options[key] if options[key] != None else ''
                reqd = 'no' if options.required[key] is False else 'yes'
                desc = options.description[key]
                print(pattern % (key.ljust(key_len), utils.to_unicode_str(value).ljust(val_len), utils.to_unicode_str(reqd).ljust(8), desc))
            print('')
        else:
            print('')
            print(f"{self.SPACER}No options available for this module.")
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
