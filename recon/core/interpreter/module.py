# =====================================================================================
# Imports: External
# =====================================================================================
import copy
import os
import textwrap
import sqlite3
import socket
import requests

# =====================================================================================
# Imports: Internal
# =====================================================================================
from .base import BaseInterpreter
from recon.utils import validators
from recon.core.exceptions import *

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

    def reload(self, new_module=None):
        '''
        Reloads the Module interpreter with a new module instance

        :param new_module: The new module instance
        :type new_module: BaseModule, optional
        '''

        self._module = new_module
        super(ModuleInterpreter, self).reload()

    # =====================================================================================
    # Command Do Functions: "info"
    # =====================================================================================
    def do_info(self, params):
        '''Shows details about the loaded module'''
        self._console.write('')

        # Print Basic Module information
        for item in ['name', 'author', 'version']:
            self._console.write(f"{item.title().rjust(10)}: {self._module.get_meta_property(item)}")

        # Print any required Keys
        if self._module.meta.required_keys:
            self._console.write(f"{'keys'.title().rjust(10)}: {', '.join(self._module.meta.required_keys)}")
        self._console.write('')

        # Print Path/Fully Qualified Name
        self._console.write("Fully-Qualified Name (FQN)/Path:")
        self._console.write(f"{self.SPACER}{self._module.get_fqn()}")
        self._console.write('')

        # Print Module Description
        self._console.write('Description:')
        self._console.write(f"{self.SPACER}{textwrap.fill(self._module.meta.description, 100, subsequent_indent=self.SPACER)}")
        self._console.write('')

        # Print Module Option information
        self._console.write('Options:', end='')
        self._list_options(self._module.get_options())

        # Print Module Source information (TODO TBC?)
        if hasattr(self, '_default_source'):
            self._console.write('Source Options:')
            self._console.write(f"{self.SPACER}{'default'.ljust(15)}{self._default_source}")
            self._console.write(f"{self.SPACER}{'<string>'.ljust(15)}string representing a single input")
            self._console.write(f"{self.SPACER}{'<path>'.ljust(15)}path to a file containing a list of inputs")
            self._console.write(f"{self.SPACER}{'query <sql>'.ljust(15)}database query returning one column of inputs")
            self._console.write('')

        # Print Module Comments
        if self._module.meta.comments:
            self._console.write('Comments:')
            for comment in self._module.meta.comments:
                prefix = '* '
                if comment.startswith('\t'):
                    prefix = self.SPACER+'- '
                    comment = comment[1:]
                self._console.write(f"{self.SPACER}{textwrap.fill(prefix+comment, 100, subsequent_indent=self.SPACER)}")
            self._console.write('')


    # =====================================================================================
    # Command Do Functions: "options"
    # =====================================================================================
    def _do_options_list(self, params):
        '''Shows the current context options'''
        self._list_options(self._module.get_options())

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
        options = self._module.get_options()
        option_name = option.upper()
        if option_name in options:
            options[option_name] = value
            self._console.write(f"{option_name} => {value}")
            workspace.set_config_property(option_name, self._module.get_fqn(), options=options)
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
        options = self._module.get_options()
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
            self._console.write(f"{option_name} => {value}")
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

    # =====================================================================================
    # Command Do Functions: "reload"
    # =====================================================================================
    def do_reload(self, params):
        '''Reloads the loaded module'''
        self._status = self.STATUS_RELOADED
        return True

    # =====================================================================================
    # Command Do Functions: "input"
    # =====================================================================================
    def do_input(self, params):
        '''Shows inputs based on the source option'''

        # Check if Module has a Default Source set
        if hasattr(self._module, '_default_source'):
            try:
                self._recon.validate_options()
                inputs = self._get_source_entries(self._module.get_option_value('source'), self._module._default_source)
                self._console.table([[x] for x in inputs], header=['Module Inputs'])
            except Exception as e:
                self._console.output(e.__str__())
        else:
            self._console.output('Source option not available for this module.')
            
    # =====================================================================================
    # Command Do Functions: "run"
    # =====================================================================================
    def do_run(self, params):
        '''Runs the loaded module'''
        inputs = []

        # Process Inputs
        if hasattr(self._module, '_default_source'):
            inputs = self._get_source_entries(self._module.get_option_value('source'), self._module._default_source)
            self._module._validate_inputs(inputs)

        # Run the Module!
        try:
            self._recon.validate_options(self._module.get_options())
            if self._module.preflight():
                self._module.run(inputs)
        # Handler: Keyboard Interrupts from user
        except KeyboardInterrupt:
            self._console.write("")
        # Handler: Connection Timeouts
        except (requests.exceptions.Timeout, socket.timeout):
            self._console.print_exception()
            self._console.error('A request took too long to complete. If the issue persists, increase the global TIMEOUT option.')
        # Handler: Framework/Validation Exception
        except (ReconNGXException, validators.ValidationException):
            self._console.print_exception()
            if self._recon.get_verbosity() > 1:
                raise
        # Handler: Unexpected exceptions/errors
        except Exception:
            self._console.print_exception()
            self._console.error('Something broken? See https://github.com/xvzfopt/recon-ngx/wiki/Troubleshooting#issue-reporting.')
            if self._recon.get_verbosity() > 1:
                raise

        # Post run
        # TODO : To be reviewed. _summary_counts doesn't actually seem to be used anywhere??
        # TODO: Actually.. it's used by the web server. Check this
        # finally:
        #     # print module summary
        #     if self._summary_counts:
        #         self._console.heading('Summary', level=0)
        #         for table in self._summary_counts:
        #             new = self._summary_counts[table]['new']
        #             cnt = self._summary_counts[table]['count']
        #             if new > 0:
        #                 method = getattr(self, 'alert')
        #             else:
        #                 method = getattr(self, 'output')
        #             method(f"{cnt} total ({new} new) {table} found.")
        
    # =====================================================================================
    # Command Do Functions: "modules"
    # =====================================================================================
    def _do_modules_load(self, params):
        '''Loads a module'''

        # Check target module specified
        if not params:
            self._help_modules_load()
            return

        # finds any modules that contain params
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

        # TODO - Review This
        # # compensation for stdin being used for scripting and loading
        # if framework.Framework._script:
        #     end_string = sys.stdin.read()
        # else:
        #     end_string = 'EOF'
        #     framework.Framework._load = 1
        # sys.stdin = io.StringIO(f"modules load {modules[0]}{os.linesep}{end_string}")

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
        return [x for x in self._module.get_options() if x.startswith(text.upper())]
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
        self._console.write(getattr(self, 'do_goptions').__doc__)
        self._console.write(f"{os.linesep}Usage: goptions <{'|'.join(self._get_subcommands('goptions'))}> [...]{os.linesep}")

    def _help_goptions_set(self):
        self._console.write(getattr(self, '_do_goptions_set').__doc__)
        self._console.write(f"{os.linesep}Usage: goptions set <option> <value>{os.linesep}")

    def _help_goptions_unset(self):
        self._console.write(getattr(self, '_do_goptions_unset').__doc__)
        self._console.write(f"{os.linesep}Usage: goptions unset <option>{os.linesep}")

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
    def _get_source_entries(self, params, query=None):
        '''
        Resolves and gets the source entries (input data) for the Module
        '''
        prefix = params.split()[0].lower()
        entries = []

        # =====================================================================================
        # Process Source: Database Query
        # =====================================================================================
        if prefix in ['query', 'default']:
            workspace = self._recon.get_current_workspace()
            db = workspace.get_db()

            query = ' '.join(params.split()[1:]) if prefix == 'query' else query
            try:
                results = db.query(query)
            except sqlite3.OperationalError as oe:
                raise ReconNGXException("Invalid source query: %s --> %s" % (type(oe).__name__, oe))

            # Process Results
            if results and len(results[0]) > 1:
                entries += [x[:len(x)] for x in results]
            else:
                entries += [x[0] for x in results]

        # =====================================================================================
        # Process Source: File
        # =====================================================================================
        elif os.path.isfile(params):
            entries += open(params).read().split()

        # =====================================================================================
        # Process Source: Source value itself
        # =====================================================================================
        else:
            entries.append(params)

        # Check we have some sources to use
        if not entries:
            raise ReconNGXException("Source contains no input. There are no entries to run the module against.")

        return entries