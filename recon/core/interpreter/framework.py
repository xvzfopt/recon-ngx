# =====================================================================================
# Imports: External
# =====================================================================================
import os

# =====================================================================================
# Imports: Internal
# =====================================================================================
from .base import BaseInterpreter

# =====================================================================================
# Framework Interpreter Class
# =====================================================================================
class FrameworkInterpreter(BaseInterpreter):
    '''
    Main Recon-NGX Command Interpreter for core Framework
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, recon, console):
        '''
        Constructor
        '''
        '''
        Constructor

        :param recon: The ReconNGX App instance
        :type recon: ReconNGXApp
        :param console: The console output instance
        :type console: ConsoleOutput
        '''
        super(FrameworkInterpreter, self).__init__(recon, console)

    # =====================================================================================
    # Command Do Functions: "marketplace"
    # =====================================================================================
    def do_marketplace(self, params):
        '''Interfaces with the module marketplace'''

        # Check Marketplace is enabled
        if not self._recon.is_marketplace_enabled():
            self._console.alert('Marketplace disabled.')
            return

        # Check Marketplace subcommand specified
        if not params:
            self.help_marketplace()
            return

        # Execute Marketplace Command
        arg, params = self._parse_params(params)
        if arg in self._get_subcommands('marketplace'):
            return getattr(self, '_do_marketplace_' + arg)(params)
        else:
            self.help_marketplace()

    def _do_marketplace_refresh(self, params):
        '''Refreshes the marketplace index'''
        mm = self._recon.get_module_manager()
        mm.fetch_marketplace_index()
        self._console.output('Marketplace index refreshed.')

    def _do_marketplace_search(self, params):
        '''Searches marketplace modules'''
        mm = self._recon.get_module_manager()

        # Search Modules
        if params:
            self._console.output(f"Searching module index for '{params}'...")
            modules = mm.search_module_index(params)
        else:
            modules = [m for m in mm.get_module_index()]

        # Display Matching Modules
        if modules:
            rows = []
            for module in sorted(modules, key=lambda m: m['path']):
                row = []
                for key in ('path', 'version', 'status', 'last_updated'):
                    row.append(module[key])
                row.append('*' if module['dependencies'] else '')
                row.append('*' if module['required_keys'] else '')
                rows.append(row)
            header = ('Path', 'Version', 'Status', 'Updated', 'D', 'K')

            self._console.table(rows, header=header)
            print(f"{self.SPACER}D = Has dependencies. See info for details.")
            print(f"{self.SPACER}K = Requires keys. See info for details.{os.linesep}")
        else:
            self._console.error('No modules found.')
            self._help_marketplace_search()

    def _do_marketplace_info(self, params):
        '''Shows detailed information about available modules'''

        # Check module name was provided
        if not params:
            self._help_marketplace_info()
            return

        # Display info for matching modules
        mm = self._recon.get_module_manager()
        modules = [m for m in mm.get_module_index() if params in m['path'] or params == 'all']
        if modules:
            for module in modules:
                rows = []
                for key in ('path', 'name', 'author', 'version', 'last_updated', 'description', 'required_keys', 'dependencies', 'files', 'status'):
                    row = (key, module[key])
                    rows.append(row)
                self._console.table(rows)
        else:
            self._console.error('Invalid module path.')

    def _do_marketplace_install(self, params):
        '''Installs modules from the marketplace'''

        # Check Module name was provided
        if not params:
            self._help_marketplace_install()
            return

        # Install matching modules
        mm = self._recon.get_module_manager()
        modules = [m for m in mm.get_module_index() if params in m['path'] or params == 'all']
        if modules:
            for module in modules:
                mm.install_module(module['path'])
            self._do_modules_reload('')
        else:
            self._console.error('Invalid module path.')

    def _do_marketplace_remove(self, params):
        '''Removes marketplace modules from the framework'''

        # Check module name provided
        if not params:
            self._help_marketplace_remove()
            return

        # Process Modules
        target_modules = params.split(" ")
        modules_to_remove = []
        mm = self._recon.get_module_manager()
        for module in mm.get_module_index():
            if mm.is_installed(module["path"]) and (module["path"] in target_modules or "all" in target_modules):
                modules_to_remove.append(module["path"])

        # Remove Modules
        if modules_to_remove:
            for module in modules_to_remove:
                mm.uninstall_module(module)
            self._do_modules_reload('')
        else:
            self._console.error('Invalid module path --> %s' % params)

    # =====================================================================================
    # Command Do Function: "workspaces"
    # =====================================================================================
    def do_workspaces(self, params):
        '''Manages workspaces'''

        # Check Workspace subcommand provided
        if not params:
            self.help_workspaces()
            return

        # Execute workspaces subcommand
        arg, params = self._parse_params(params)
        if arg in self._get_subcommands('workspaces'):
            return getattr(self, '_do_workspaces_'+arg)(params)
        else:
            self.help_workspaces()

    def _do_workspaces_list(self, params):
        '''Lists existing workspaces'''
        rows = []

        # Display Workspaces
        wm = self._recon.get_workspace_manager()
        for workspace in wm.get_workspaces():
            rows.append((workspace.get_name(), workspace.get_mod_time()))
        rows.sort(key=lambda x: x[0])
        self._console.table(rows, header=['Workspaces', 'Modified'])

    def _do_workspaces_create(self, params):
        '''Creates a new workspace'''

        # Check workspace name specified
        if not params:
            self._help_workspaces_create()
            return

        # Create workspace
        if not self._recon.set_workspace(params):
            self._console.output(f"Unable to create '{params}' workspace.")

    def _do_workspaces_load(self, params):
        '''Loads an existing workspace'''

        # Check Workspace name provided
        if not params:
            self._help_workspaces_load()
            return

        # Set Workspace
        wm = self._recon.get_workspace_manager()
        if params in [x.get_name() for x in wm.get_workspaces()]:
            if not self._recon.set_workspace(params):
                self._console.output(f"Unable to initialize '{params}' workspace.")
        else:
            self._console.output('Invalid workspace name.')

    def _do_workspaces_remove(self, params):
        '''Removes an existing workspace'''

        # Check Workspace name provided
        if not params:
            self._help_workspaces_remove()
            return

        wm = self._recon.get_workspace_manager()
        if not wm.remove_workspace(params):
            self._console.output(f"Unable to remove '{params}' workspace.")
        else:
            self._console.output("Workspace removed.")
            if params == self._recon.get_current_workspace().get_name():
                self._recon.set_workspace('default')

    # =====================================================================================
    # Command Do Function: "snapshots"
    # =====================================================================================
    def do_snapshots(self, params):
        '''Manages workspace snapshots'''
        # Check snapshots subcommand provided
        if not params:
            self.help_snapshots()
            return

        # Execute snapshots subcommand
        arg, params = self._parse_params(params)
        if arg in self._get_subcommands('snapshots'):
            return getattr(self, '_do_snapshots_'+arg)(params)
        else:
            self.help_snapshots()

    def _do_snapshots_list(self, params):
        '''Lists existing database snapshots'''

        # Get Snapshots for DB
        workspace = self._recon.get_current_workspace()
        db = workspace.get_db()
        snapshots = db.get_snapshots()

        # Display Snapshots
        if snapshots:
            self._console.table([[x] for x in snapshots], header=['Snapshots'])
        else:
            self._console.output('This workspace has no snapshots.')

    def _do_snapshots_take(self, params):
        '''Takes a snapshot of the current database'''

        # Get DB
        workspace = self._recon.get_current_workspace()
        db = workspace.get_db()

        # Take snapshot
        db.take_snapshot()

    def _do_snapshots_load(self, params):
        '''Loads an existing database snapshot'''

        # Check snapshot name specified
        if not params:
            self._help_snapshots_load()
            return

        # Get DB
        workspace = self._recon.get_current_workspace()
        db = workspace.get_db()

        if params in db.get_snapshots():
            db.load_snapshot(params)
        else:
            self._console.error(f"No snapshot named '{params}'.")

    def _do_snapshots_remove(self, params):
        '''Removes an existing snapshot'''

        # Check snapshot name specified
        if not params:
            self._help_snapshots_remove()
            return

        # Get DB
        workspace = self._recon.get_current_workspace()
        db = workspace.get_db()

        if params in db.get_snapshots():
            db.remove_snapshot(params)
        else:
            self._console.error(f"No snapshot named '{params}'.")

    # =====================================================================================
    # Auto-completion Functions: marketplace
    # =====================================================================================
    def complete_marketplace(self, text, line, *ignored):
        '''
        Auto-completion for marketplace commands

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :param line: The entire line that has been typed so far
        :type line: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        arg, params = self._parse_params(line.split(' ', 1)[1])
        subs = self._get_subcommands('marketplace')

        # If directly matching sub-command found, auto-complete that
        if arg in subs:
            return getattr(self, '_complete_marketplace_'+arg)(text, params)

        # Else return all available matching commands
        return [sub for sub in subs if sub.startswith(text)]

    def _complete_marketplace_refresh(self, text, *ignored):
        '''
        Auto-completion for marketplace command: refresh
        Placeholder: currently we have nothing more to provide for this command

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        return []
    # Auto-complete marketplace "search" in same way as refresh
    _complete_marketplace_search = _complete_marketplace_refresh

    def _complete_marketplace_info(self, text, *ignored):
        '''
        Auto-completion for marketplace command: info
        Searches all modules that match

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        mm = self._recon.get_module_manager()
        return [x['path'] for x in mm.get_module_index() if x['path'].startswith(text)]
    # Auto-complete marketplace "install" in same way as info
    _complete_marketplace_install = _complete_marketplace_info

    def _complete_marketplace_remove(self, text, *ignored):
        '''
        Auto-completion for marketplace command: remove
        Searches all modules that match, and are currently installed

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        mm = self._recon.get_module_manager()
        return [x['path'] for x in mm.get_module_index() if x['status'] == mm.MODULE_STATUS_INSTALLED and x['path'].startswith(text)]

    # =====================================================================================
    # Auto-completion Functions: workspaces
    # =====================================================================================
    def complete_workspaces(self, text, line, *ignored):
        '''
        Auto-completion for workspaces commands

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :param line: The entire line that has been typed so far
        :type line: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        arg, params = self._parse_params(line.split(' ', 1)[1])
        subs = self._get_subcommands('workspaces')

        # If directly matching sub-command found, auto-complete that
        if arg in subs:
            return getattr(self, '_complete_workspaces_'+arg)(text, params)

        # Else return all available matching commands
        return [sub for sub in subs if sub.startswith(text)]

    def _complete_workspaces_list(self, text, *ignored):
        '''
        Auto-completion for workspaces command: list
        Placeholder: currently we have nothing more to provide for this command

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        return []
    # Auto-complete workspaces "create" in same way as list
    _complete_workspaces_create = _complete_workspaces_list

    def _complete_workspaces_load(self, text, *ignored):
        '''
        Auto-completion for workspaces command: load
        Searches all workspaces that match

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        wm = self._recon.get_workspace_manager()
        return [x.get_name() for x in wm.get_workspaces() if x.get_name().startswith(text)]
    # Auto-complete workspaces "remove" command in same way as load
    _complete_workspaces_remove = _complete_workspaces_load

    # =====================================================================================
    # Auto-completion Functions: snapshots
    # =====================================================================================
    def complete_snapshots(self, text, line, *ignored):
        '''
        Auto-completion for snapshots commands

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :param line: The entire line that has been typed so far
        :type line: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        arg, params = self._parse_params(line.split(' ', 1)[1])
        subs = self._get_subcommands('snapshots')

        # If directly matching sub-command found, auto-complete that
        if arg in subs:
            return getattr(self, '_complete_snapshots_'+arg)(text, params)

        # Else return all available matching commands
        return [sub for sub in subs if sub.startswith(text)]

    def _complete_snapshots_list(self, text, *ignored):
        '''
        Auto-completion for snapshots command: list
        Placeholder: currently we have nothing more to provide for this command

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        return []
    # Auto-complete snapshots "take" command in the same way as list
    _complete_snapshots_take = _complete_snapshots_list

    def _complete_snapshots_load(self, text, *ignored):
        '''
        Auto-completion for snapshots command: load
        Searches all snapshots for the current workspace DB that match

        :param text: The subcommand text to auto-complete, which has been typed so far
        :type text: str
        :returns: List of matching subcommands, if found
        :rtype: list
        '''
        # Get DB
        workspace = self._recon.get_current_workspace()
        db = workspace.get_db()

        return [x for x in db.get_snapshots() if x.startswith(text)]
    # Auto-complete snapshots "remove" in the same way as load
    _complete_snapshots_remove = _complete_snapshots_load

    # =====================================================================================
    # Command Help Functions
    # =====================================================================================
    def help_marketplace(self):
        print(getattr(self, 'do_marketplace').__doc__)
        print(f"{os.linesep}Usage: marketplace <{'|'.join(self._get_subcommands('marketplace'))}> [...]{os.linesep}")

    def _help_marketplace_search(self):
        print(getattr(self, '_do_marketplace_search').__doc__)
        print(f"{os.linesep}Usage: marketplace search [<regex>]{os.linesep}")

    def _help_marketplace_info(self):
        print(getattr(self, '_do_marketplace_info').__doc__)
        print(f"{os.linesep}Usage: marketplace info <<path>|<prefix>|all>{os.linesep}")

    def _help_marketplace_install(self):
        print(getattr(self, '_do_marketplace_install').__doc__)
        print(f"{os.linesep}Usage: marketplace install <<path>|<prefix>|all>{os.linesep}")

    def _help_marketplace_remove(self):
        print(getattr(self, '_do_marketplace_remove').__doc__)
        print(f"{os.linesep}Usage: marketplace remove <<path>|<prefix>|all>{os.linesep}")

    def help_workspaces(self):
        print(getattr(self, 'do_workspaces').__doc__)
        print(f"{os.linesep}Usage: workspaces <{'|'.join(self._get_subcommands('workspaces'))}> [...]{os.linesep}")

    def _help_workspaces_create(self):
        print(getattr(self, '_do_workspaces_create').__doc__)
        print(f"{os.linesep}Usage: workspace create <name>{os.linesep}")

    def _help_workspaces_load(self):
        print(getattr(self, '_do_workspaces_load').__doc__)
        print(f"{os.linesep}Usage: workspace load <name>{os.linesep}")

    def _help_workspaces_remove(self):
        print(getattr(self, '_do_workspaces_remove').__doc__)
        print(f"{os.linesep}Usage: workspace remove <name>{os.linesep}")

    def help_snapshots(self):
        print(getattr(self, 'do_snapshots').__doc__)
        print(f"{os.linesep}Usage: snapshots <{'|'.join(self._get_subcommands('snapshots'))}> [...]{os.linesep}")

    def _help_snapshots_load(self):
        print(getattr(self, '_do_snapshots_load').__doc__)
        print(f"{os.linesep}Usage: snapshots load <name>{os.linesep}")

    def _help_snapshots_remove(self):
        print(getattr(self, '_do_snapshots_remove').__doc__)
        print(f"{os.linesep}Usage: snapshots remove <name>{os.linesep}")






