# =====================================================================================
# Imports: External
# =====================================================================================
import os
import textwrap

# =====================================================================================
# Imports: Internal
# =====================================================================================
from .base import BaseInterpreter
from recon.utils import utils

# =====================================================================================
# Module Interpreter Class
# =====================================================================================
class ModuleInterpreter(BaseInterpreter):
    '''
    Module Command Interpreter for use in Module context/mode
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, recon, console, module):
        '''
        Constructor
        '''
        '''
        Constructor

        :param recon: The ReconNGX App instance
        :type recon: ReconNGXApp
        :param console: The console output instance
        :type console: ConsoleOutput
        :param module: The Module instance
        :type module: BaseModule
        '''
        super(ModuleInterpreter, self).__init__(recon, console)
        self._module = module
        self._workspace = self._recon.get_current_workspace()
        self.prompt = "%s[%s][%s] > " % (self._base_prompt, self._workspace.get_name(), module.get_name())

    def start(self):
        '''
        Start the Module Interpreter

        :note: Overrides base start to avoid banner print
        '''
        self.cmdloop()

    # =====================================================================================
    # Command Do Functions: "info"
    # =====================================================================================
    def do_info(self, params):
        '''Shows details about the loaded module'''
        print('')

        # Print Basic Module information
        for item in ['name', 'author', 'version']:
            print(f"{item.title().rjust(10)}: {self._module.meta[item]}")

        # Print any required Keys
        if self._module.meta.get('required_keys'):
            print(f"{'keys'.title().rjust(10)}: {', '.join(self._module.meta.get('required_keys'))}")
        print('')

        # Print Module Description
        print('Description:')
        print(f"{self.SPACER}{textwrap.fill(self._module.meta['description'], 100, subsequent_indent=self.SPACER)}")
        print('')

        # Print Module Option information
        print('Options:', end='')
        self._list_options(self._module._options)

        # Print Module Source information (TODO TBC?)
        if hasattr(self, '_default_source'):
            print('Source Options:')
            print(f"{self.SPACER}{'default'.ljust(15)}{self._default_source}")
            print(f"{self.SPACER}{'<string>'.ljust(15)}string representing a single input")
            print(f"{self.SPACER}{'<path>'.ljust(15)}path to a file containing a list of inputs")
            print(f"{self.SPACER}{'query <sql>'.ljust(15)}database query returning one column of inputs")
            print('')

        # Print Module Comments
        if self._module.meta.get('comments'):
            print('Comments:')
            for comment in self._module.meta['comments']:
                prefix = '* '
                if comment.startswith('\t'):
                    prefix = self.SPACER+'- '
                    comment = comment[1:]
                print(f"{self.SPACER}{textwrap.fill(prefix+comment, 100, subsequent_indent=self.SPACER)}")
            print('')


    # =====================================================================================
    # Command Do Functions: "options"
    # =====================================================================================
    def _do_options_list(self, params):
        '''Shows the current context options'''
        self._list_options(self._module._options)

    def _do_options_set(self, params):
        '''Sets a current context option'''

        # Parse option key and value
        option, value = self._parse_params(params)
        if not (option and value):
            self._help_options_set()
            return

        # Get Workspace
        workspace = self._recon.get_current_workspace()

        # Check option is a valid, known Module Option
        options = self._module._options
        option_name = option.upper()
        if option_name in options:
            options[option_name] = value
            print(f"{option_name} => {value}")
            workspace.set_config_property(option_name, self._module._fqn, options=options)
        else:
            self._console.error('Invalid option name.')

    def _do_options_unset(self, params):
        '''Unsets a current context option'''

        # Parse option key and value
        option, value = self._parse_params(params)
        if not option:
            self._help_options_unset()
            return

        # Check option is a valid, known Module Option
        options = self._module._options
        option_name = option.upper()
        if option_name in options:
            self._do_options_set(' '.join([option_name, 'None']))
        else:
            self._console.error('Invalid option name.')

    # =====================================================================================
    # Command Do Functions: "goptions"
    # =====================================================================================
    def do_goptions(self, params):
        '''Manages the global context options'''

        # Check goptions subcommand specified
        if not params:
            self.help_goptions()
            return

        # Execute goptions Command
        arg, params = self._parse_params(params)
        if arg in self._get_subcommands('goptions'):
            return getattr(self, '_do_goptions_' + arg)(params)
        else:
            self.help_goptions()

    def _do_goptions_list(self, params):
        '''Shows the global context options'''
        self._list_options()


    def _do_goptions_set(self, params):
        '''Sets a global context option'''

        # Parse option key and value
        option, value = self._parse_params(params)
        if not (option and value):
            self._help_goptions_set()
            return

        # Get Workspace
        workspace = self._recon.get_current_workspace()

        # Check option is a valid, known Global Option
        goptions = self._recon.get_options()
        option_name = option.upper()
        if option_name in goptions:
            goptions[option_name] = value
            print(f"{option_name} => {value}")
            workspace.set_config_property(option_name, options=goptions)
        else:
            self._console.error('Invalid option name.')

    def _do_goptions_unset(self, params):
        '''Unsets a global context option'''

        # Parse option key and value
        option, value = self._parse_params(params)
        if not option:
            self._help_goptions_unset()
            return

        # Check option is a valid, known Global Option
        goptions = self._recon.get_options()
        option_name = option.upper()
        if option_name in goptions:
            self._do_goptions_set(' '.join([option_name, 'None']))
        else:
            self._console.error('Invalid option name.')

    def do_reload(self, params):
        '''Reloads the loaded module'''
        self._status = self.STATUS_RELOADED
        return True

    # =====================================================================================
    # Auto-completion Functions: goptions
    # =====================================================================================
    def complete_goptions(self, text, line, *ignored):
        '''
        Auto-completion for goptions commands

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :param line: The entire line that has been typed so far
        :type line: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        arg, params = self._parse_params(line.split(' ', 1)[1])
        subs = self._get_subcommands('goptions')

        # If directly matching sub-command found, auto-complete that
        if arg in subs:
            return getattr(self, '_complete_goptions_'+arg)(text, params)

        # Else return all available matching commands
        return [sub for sub in subs if sub.startswith(text)]

    def _complete_goptions_list(self, text, *ignored):
        '''
        Auto-completion for goptions command: list
        Placeholder: currently we have nothing more to provide for this command

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        return []

    def _complete_goptions_set(self, text, *ignored):
        '''
        Auto-completion for goptions command: set
        Searches all global options for an option that matches

        :param text: The option name to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        return [x for x in self._recon.get_options() if x.startswith(text.upper())]
    # Auto-complete goptions "unset" in same way as set
    _complete_goptions_unset = _complete_goptions_set

    # =====================================================================================
    # Auto-completion Functions: options
    # =====================================================================================
    def _complete_options_set(self, text, *ignored):
        '''
        Auto-completion for options command: set
        Searches all Module options for an option that matches

        :param text: The option name to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        return [x for x in self._module._options if x.startswith(text.upper())]
    # Auto-complete options "unset" in same way as set
    _complete_options_unset = _complete_options_set

    # =====================================================================================
    # Auto-completion functions: reload
    # =====================================================================================
    def complete_reload(self, text, *ignored):
        '''
        Auto-completion for reload command

        :param text: The option name to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        return []

    # =====================================================================================
    # Command Help Functions
    # =====================================================================================
    def help_goptions(self):
        print(getattr(self, 'do_goptions').__doc__)
        print(f"{os.linesep}Usage: goptions <{'|'.join(self._get_subcommands('goptions'))}> [...]{os.linesep}")

    def _help_goptions_set(self):
        print(getattr(self, '_do_goptions_set').__doc__)
        print(f"{os.linesep}Usage: goptions set <option> <value>{os.linesep}")

    def _help_goptions_unset(self):
        print(getattr(self, '_do_goptions_unset').__doc__)
        print(f"{os.linesep}Usage: goptions unset <option>{os.linesep}")

    # =====================================================================================
    # Getters
    # =====================================================================================
    def get_module(self):
        '''
        Returns the current module instance

        :returns: The Module instance associated with this interpreter
        :rtype: BaseModule
        '''
        return self._module

    # =====================================================================================
    # Internal Helpers
    # =====================================================================================