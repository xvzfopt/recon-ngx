__author__    = 'Tim Tomes (@lanmaster53)'

# =====================================================================================
# Imports: External
# =====================================================================================
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
import errno
from importlib.machinery import SourceFileLoader
import json
import os
import random
import re
import shutil
import sys
import yaml
import builtins
import sys

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.core.workspace import WorkspaceManager
from recon.core._module import ModuleManager
from recon.core import framework
from ..utils import utils
from recon.core.workspace.workspace import Workspace

# using stdout to spool causes tab complete issues
# therefore, override print function
# use a lock for thread safe console and spool output
from threading import Lock
_print_lock = Lock()
# spooling system
def spool_print(*args, **kwargs):
    with _print_lock:
        if framework.Framework._spool:
            framework.Framework._spool.write(f"{args[0]}{os.linesep}")
            framework.Framework._spool.flush()
        # disable terminal output for server jobs
        if framework.Framework._mode == Mode.JOB:
            return
        # new print function must still use the old print function via the backup
        builtins._print(*args, **kwargs)
# make a builtin backup of the original print function
builtins._print = print
# override the builtin print function with the new print function
builtins.print = spool_print

#=================================================
# BASE CLASS
#=================================================

class Recon(framework.Framework):

    repo_url = 'https://raw.githubusercontent.com/lanmaster53/recon-ng-modules/master/'

    def __init__(self, version, author, verbosity, check=True, analytics=True, marketplace=True, accessible=False):
        framework.Framework.__init__(self, 'base', version, author)
        self._name = 'recon-ng'
        self._prompt_template = '{}[{}] > '
        self._base_prompt = self._prompt_template.format('', self._name)
        # set toggle flags
        self._check = check
        self._analytics = analytics
        self._marketplace = marketplace
        self.console.set_accessibility(accessible)
        # set path variables
        self.app_path = framework.Framework.app_path = sys.path[0]
        self.core_path = framework.Framework.core_path = os.path.join(self.app_path, 'core')
        self.home_path = framework.Framework.home_path = os.path.join(os.path.expanduser('~'), '.recon-ng')
        self.mod_path = framework.Framework.mod_path = os.path.join(self.home_path, 'modules')
        self.data_path = framework.Framework.data_path = os.path.join(self.home_path, 'data')
        self.spaces_path = framework.Framework.spaces_path = os.path.join(self.home_path, 'workspaces')

        # =====================================================================================
        # Validate Any Additional Parameters
        # =====================================================================================
        if verbosity not in [0, 1, 2]:
            self.console.error("Invalid verbosity level '%s'. Must be 0, 1, or 2." % verbosity)
            sys.exit(1)

        # Initialise Global Options
        self._init_global_options()
        self.options["verbosity"] = verbosity

        # Initialise Workspace Manager
        self._wm = WorkspaceManager(self.spaces_path, self.console)

        # Initialise Module Manager
        self._mm = ModuleManager(self.home_path, self.console)

    def start(self, mode, workspace='default'):
        # initialize framework components
        self._mode = framework.Framework._mode = mode
        self._init_home()
        self._init_workspace(workspace)
        self._check_version()
        if self._mode == Mode.CONSOLE:
            self.console.print_banner(self._version, self._author, self._mm.get_module_categories())
            self.cmdloop()

    #==================================================
    # SUPPORT METHODS
    #==================================================
    def _init_global_options(self):
        self.options = self._global_options
        self.options.initialise_global_options(self._version)

    def _init_home(self):
        # initialize home folder
        if not os.path.exists(self.home_path):
            os.makedirs(self.home_path)
        # initialize keys database
        self._query_keys('CREATE TABLE IF NOT EXISTS keys (name TEXT PRIMARY KEY, value TEXT)')
        # initialize module index
        self._mm.fetch_marketplace_index()

    def _check_version(self):
        if self._check:
            pattern = r"'(\d+\.\d+\.\d+[^']*)'"
            remote = 0
            try:
                remote = re.search(pattern, self.request('GET', 'https://raw.githubusercontent.com/lanmaster53/recon-ng/master/VERSION').text).group(1)
            except Exception as e:
                self.console.error(f"Version check failed ({type(e).__name__}).")
                #self.console.print_exception()
            if remote != self._version:
                self.console.alert('Your version of Recon-ng does not match the latest release.')
                self.console.alert('Please consider updating before further use.')
                self.console.output(f"Remote version:  {remote}")
                self.console.output(f"Local version:   {self._version}")
        else:
            self.console.alert('Version check disabled.')

    def _send_analytics(self, cd):
        if self._analytics:
            try:
                cid_path = os.path.join(self.home_path, '.cid')
                if not os.path.exists(cid_path):
                    # create the cid and file
                    import uuid
                    with open(cid_path, 'w') as fp:
                        fp.write(utils.to_unicode_str(uuid.uuid4()))
                with open(cid_path) as fp:
                    cid = fp.read().strip()
                params = {
                        'v': 1,
                        'tid': 'UA-52269615-2',
                        'cid': cid,
                        't': 'screenview',
                        'an': 'Recon-ng',
                        'av': self._version,
                        'cd': cd
                        }
                self.request('GET', 'https://www.google-analytics.com/collect', params=params)
            except Exception as e:
                self.console.debug(f"Analytics failed ({type(e).__name__}).")
                #self.console.print_exception()
                return
        else:
            self.console.debug('Analytics disabled.')

    def _menu_egg(self, params):
        eggs = [
            'Really? A menu option? Try again.',
            'You clearly need \'help\'.',
            'That makes no sense to me.',
            '*grunt* *grunt* Nope. I got nothin\'.',
            'Wait for it...',
            'This is not the Social Engineering Toolkit.',
            'Don\'t you think if that worked the numbers would at least be in order?',
            'Reserving that option for the next-NEXT generation of the framework.',
            'You\'ve clearly got the wrong framework. Attempting to start SET...',
            '1980 called. They want their menu driven UI back.',
        ]
        print(random.choice(eggs))
        return

    #==================================================
    # WORKSPACE METHODS
    #==================================================
    def _init_workspace(self, name):
        if not name:
            return

        # Create Workspace
        if not self._wm.workspace_exists(name):
            self._workspace_obj = self._wm.create_workspace(name)
            self.workspace = framework.Framework.workspace = self._workspace_obj.get_path()
        # Load Existing Workspace
        else:
            self._workspace_obj = self._wm.get_workspace(name)
            self.workspace = framework.Framework.workspace = self._workspace_obj.get_path()

        # set workspace prompt
        self.prompt = self._prompt_template.format(self._base_prompt[:-3], self._workspace_obj.get_name())
        # load workspace configuration
        self._load_config()
        # reload modules after config to populate options
        self._mm.load_modules()
        return True

    def _get_workspaces(self):
        return [x.get_name() for x in self._wm.get_workspaces()]

    def _get_snapshots(self):
        snapshots = []
        for f in os.listdir(self.workspace):
            if re.search(r'^snapshot_\d{14}.db$', f):
                snapshots.append(f)
        return snapshots

    #==================================================
    # COMMAND METHODS
    #==================================================
    def do_index(self, params):
        '''Creates a module index (dev only)'''
        mod_path, file_name = self._parse_params(params)
        if not mod_path:
            self.help_index()
            return
        self.console.output('Building index markup...')
        yaml_objs = []
        modules = [m for m in self._mm._loaded_modules.items() if mod_path in m[0] or mod_path == 'all']
        for path, module in sorted(modules, key=lambda k: k[0]):
            yaml_obj = {}
            # not in meta
            yaml_obj['path'] = path
            yaml_obj['last_updated'] = datetime.strftime(datetime.now(), '%Y-%m-%d')
            # meta required
            yaml_obj['author'] = module.meta.get('author')
            yaml_obj['name'] = module.meta.get('name')
            yaml_obj['description'] = module.meta.get('description')
            yaml_obj['version'] = module.meta.get('version', '1.0')
            # meta optional
            #yaml_obj['comments'] = module.meta.get('comments', [])
            yaml_obj['dependencies'] = module.meta.get('dependencies', [])
            yaml_obj['files'] = module.meta.get('files', [])
            #yaml_obj['options'] = module.meta.get('options', [])
            #yaml_obj['query'] = module.meta.get('query', '')
            yaml_obj['required_keys'] = module.meta.get('required_keys', [])
            yaml_objs.append(yaml_obj)
        if yaml_objs:
            markup = yaml.safe_dump(yaml_objs)
            print(markup)
            # write to file if index name provided
            if file_name:
                with open(file_name, 'w') as outfile:
                    outfile.write(markup)
                self.console.output('Module index created.')
        else:
            self.console.output('No modules found.')

    def do_marketplace(self, params):
        '''Interfaces with the module marketplace'''
        if not self._marketplace:
            self.console.alert('Marketplace disabled.')
            return
        if not params:
            self.help_marketplace()
            return
        arg, params = self._parse_params(params)
        if arg in self._parse_subcommands('marketplace'):
            return getattr(self, '_do_marketplace_'+arg)(params)
        else:
            self.help_marketplace()

    def _do_marketplace_refresh(self, params):
        '''Refreshes the marketplace index'''
        self._mm.fetch_marketplace_index()
        self.console.output('Marketplace index refreshed.')

    def _do_marketplace_search(self, params):
        '''Searches marketplace modules'''
        modules = [m for m in self._mm.get_module_index()]
        if params:
            self.console.output(f"Searching module index for '{params}'...")
            modules = self._mm.search_module_index(params)
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
            self.console.table(rows, header=header)
            print(f"{self.spacer}D = Has dependencies. See info for details.")
            print(f"{self.spacer}K = Requires keys. See info for details.{os.linesep}")
        else:
            self.console.error('No modules found.')
            self._help_marketplace_search()

    def _do_marketplace_info(self, params):
        '''Shows detailed information about available modules'''
        if not params:
            self._help_marketplace_info()
            return
        modules = [m for m in self._mm.get_module_index() if params in m['path'] or params == 'all']
        if modules:
            for module in modules:
                rows = []
                for key in ('path', 'name', 'author', 'version', 'last_updated', 'description', 'required_keys', 'dependencies', 'files', 'status'):
                    row = (key, module[key])
                    rows.append(row)
                self.console.table(rows)
        else:
            self.console.error('Invalid module path.')

    def _do_marketplace_install(self, params):
        '''Installs modules from the marketplace'''
        if not params:
            self._help_marketplace_install()
            return
        modules = [m for m in self._mm.get_module_index() if params in m['path'] or params == 'all']
        if modules:
            for module in modules:
                self._mm.install_module(module['path'])
            self._do_modules_reload('')
        else:
            self.console.error('Invalid module path.')

    def _do_marketplace_remove(self, params):
        '''Removes marketplace modules from the framework'''
        if not params:
            self._help_marketplace_remove()
            return
        target_modules = params.split(" ")

        # Process Modules
        modules_to_remove = []
        for module in self._mm.get_module_index():
            if self._mm.is_installed(module["path"]) and (module["path"] in target_modules or "all" in target_modules):
                modules_to_remove.append(module["path"])

        # Remove Modules
        if modules_to_remove:
            for module in modules_to_remove:
                self._mm.uninstall_module(module)
            self._do_modules_reload('')
        else:
            self.console.error('Invalid module path --> %s' % params)

    def do_workspaces(self, params):
        '''Manages workspaces'''
        if not params:
            self.help_workspaces()
            return
        arg, params = self._parse_params(params)
        if arg in self._parse_subcommands('workspaces'):
            return getattr(self, '_do_workspaces_'+arg)(params)
        else:
            self.help_workspaces()

    def _do_workspaces_list(self, params):
        '''Lists existing workspaces'''
        rows = []
        for workspace in self._wm.get_workspaces():
            rows.append((workspace.get_name(), workspace.get_mod_time()))
        rows.sort(key=lambda x: x[0])
        self.console.table(rows, header=['Workspaces', 'Modified'])

    def _do_workspaces_create(self, params):
        '''Creates a new workspace'''
        if not params:
            self._help_workspaces_create()
            return
        if not self._init_workspace(params):
            self.console.output(f"Unable to create '{params}' workspace.")

    def _do_workspaces_load(self, params):
        '''Loads an existing workspace'''
        if not params:
            self._help_workspaces_load()
            return
        if params in [x.get_name() for x in self._wm.get_workspaces()]:
            if not self._init_workspace(params):
                self.console.output(f"Unable to initialize '{params}' workspace.")
        else:
            self.console.output('Invalid workspace name.')

    def _do_workspaces_remove(self, params):
        '''Removes an existing workspace'''
        if not params:
            self._help_workspaces_remove()
            return
        if not self._wm.remove_workspace(params):
            self.console.output(f"Unable to remove '{params}' workspace.")
        else:
            if params == self.workspace.split('/')[-1]:
                self._init_workspace('default')

    def do_snapshots(self, params):
        '''Manages workspace snapshots'''
        if not params:
            self.help_snapshots()
            return
        arg, params = self._parse_params(params)
        if arg in self._parse_subcommands('snapshots'):
            return getattr(self, '_do_snapshots_'+arg)(params)
        else:
            self.help_snapshots()

    def _do_snapshots_list(self, params):
        '''Lists existing database snapshots'''
        snapshots = self._get_snapshots()
        if snapshots:
            self.console.table([[x] for x in snapshots], header=['Snapshots'])
        else:
            self.console.output('This workspace has no snapshots.')

    def _do_snapshots_take(self, params):
        '''Takes a snapshot of the current database'''
        ts = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')
        snapshot = f"snapshot_{ts}.db"
        src = os.path.join(self.workspace, 'data.db')
        dst = os.path.join(self.workspace, snapshot)
        shutil.copyfile(src, dst)
        self.console.output(f"Snapshot created: {snapshot}")

    def _do_snapshots_load(self, params):
        '''Loads an existing database snapshot'''
        if not params:
            self._help_snapshots_load()
            return
        if params in self._get_snapshots():
            src = os.path.join(self.workspace, params)
            dst = os.path.join(self.workspace, 'data.db')
            shutil.copyfile(src, dst)
            self.console.output(f"Snapshot loaded: {params}")
        else:
            self.console.error(f"No snapshot named '{params}'.")

    def _do_snapshots_remove(self, params):
        '''Removes an existing snapshot'''
        if not params:
            self._help_snapshots_remove()
            return
        if params in self._get_snapshots():
            os.remove(os.path.join(self.workspace, params))
            self.console.output(f"Snapshot removed: {params}")
        else:
            self.console.error(f"No snapshot named '{params}'.")

    def _do_modules_search(self, params):
        '''Searches installed modules'''
        modules = [x for x in self._mm.get_loaded_modules()]
        if params:
            self.console.output(f"Searching installed modules for '{params}'...")
            modules = [x for x in self._mm.get_loaded_modules() if re.search(params, x)]
        if modules:
            self._list_modules(modules)
        else:
            self.console.error('No modules found.')
            self._help_modules_search()

    def _do_modules_load(self, params):
        '''Loads a module'''
        # validate global options before loading the module
        try:
            self._validate_options()
        except framework.FrameworkException as e:
            self.console.error(e)
            return
        if not params:
            self._help_modules_load()
            return
        # finds any modules that contain params
        modules = self._match_modules(params)
        # notify the user if none or multiple modules are found
        if len(modules) != 1:
            if not modules:
                self.console.error('Invalid module name.')
            else:
                self.console.output(f"Multiple modules match '{params}'.")
                self._list_modules(modules)
            return
        # load the module
        mod_dispname = modules[0]
        # loop to support reload logic
        while True:
            y = self._mm._loaded_modules[mod_dispname]
            # send analytics information
            mod_loadpath = os.path.abspath(sys.modules[y.__module__].__file__)
            self._send_analytics(mod_dispname)
            # return the loaded module if not in console mode
            if self._mode != Mode.CONSOLE:
                return y
            # begin a command loop
            y.prompt = self._prompt_template.format(self.prompt[:-3], mod_dispname.split('/')[-1])
            try:
                y.cmdloop()
            except KeyboardInterrupt:
                print('')
            if y._exit == 1:
                return True
            if y._reload == 1:
                self.console.output('Reloading module...')
                # reload the module in memory
                is_loaded = self._load_module(os.path.dirname(mod_loadpath), os.path.basename(mod_loadpath))
                if is_loaded:
                    # reload the module in the framework
                    continue
                # shuffle category counts?
            break

    def _do_modules_reload(self, params):
        '''Reloads installed modules'''
        self.console.output('Reloading modules...')
        self._mm.load_modules()

    #==================================================
    # HELP METHODS
    #==================================================

    def help_index(self):
        print(getattr(self, 'do_index').__doc__)
        print(f"{os.linesep}Usage: index <module|all> <index>{os.linesep}")

    def help_marketplace(self):
        print(getattr(self, 'do_marketplace').__doc__)
        print(f"{os.linesep}Usage: marketplace <{'|'.join(self._parse_subcommands('marketplace'))}> [...]{os.linesep}")

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
        print(f"{os.linesep}Usage: workspaces <{'|'.join(self._parse_subcommands('workspaces'))}> [...]{os.linesep}")

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
        print(f"{os.linesep}Usage: snapshots <{'|'.join(self._parse_subcommands('snapshots'))}> [...]{os.linesep}")

    def _help_snapshots_load(self):
        print(getattr(self, '_do_snapshots_load').__doc__)
        print(f"{os.linesep}Usage: snapshots load <name>{os.linesep}")

    def _help_snapshots_remove(self):
        print(getattr(self, '_do_snapshots_remove').__doc__)
        print(f"{os.linesep}Usage: snapshots remove <name>{os.linesep}")

    #==================================================
    # COMPLETE METHODS
    #==================================================

    def complete_index(self, text, line, *ignored):
        if len(line.split(' ')) == 2:
            return [x for x in self._mm._loaded_modules if x.startswith(text)]
        return []

    def complete_marketplace(self, text, line, *ignored):
        arg, params = self._parse_params(line.split(' ', 1)[1])
        subs = self._parse_subcommands('marketplace')
        if arg in subs:
            return getattr(self, '_complete_marketplace_'+arg)(text, params)
        return [sub for sub in subs if sub.startswith(text)]

    def _complete_marketplace_refresh(self, text, *ignored):
        return []
    _complete_marketplace_search = _complete_marketplace_refresh

    def _complete_marketplace_info(self, text, *ignored):
        return [x['path'] for x in self._mm.get_module_index() if x['path'].startswith(text)]
    _complete_marketplace_install = _complete_marketplace_info

    def _complete_marketplace_remove(self, text, *ignored):
        return [x['path'] for x in self._mm.get_module_index() if x['status'] == 'installed' and x['path'].startswith(text)]

    def complete_workspaces(self, text, line, *ignored):
        arg, params = self._parse_params(line.split(' ', 1)[1])
        subs = self._parse_subcommands('workspaces')
        if arg in subs:
            return getattr(self, '_complete_workspaces_'+arg)(text, params)
        return [sub for sub in subs if sub.startswith(text)]

    def _complete_workspaces_list(self, text, *ignored):
        return []
    _complete_workspaces_create = _complete_workspaces_list

    def _complete_workspaces_load(self, text, *ignored):
        return [x.get_name() for x in self._wm.get_workspaces() if x.get_name().startswith(text)]
    _complete_workspaces_remove = _complete_workspaces_load

    def complete_snapshots(self, text, line, *ignored):
        arg, params = self._parse_params(line.split(' ', 1)[1])
        subs = self._parse_subcommands('snapshots')
        if arg in subs:
            return getattr(self, '_complete_snapshots_'+arg)(text, params)
        return [sub for sub in subs if sub.startswith(text)]

    def _complete_snapshots_list(self, text, *ignored):
        return []
    _complete_snapshots_take = _complete_snapshots_list

    def _complete_snapshots_load(self, text, *ignored):
        return [x for x in self._get_snapshots() if x.startswith(text)]
    _complete_snapshots_remove = _complete_snapshots_load

    def _complete_modules_reload(self, text, *ignored):
        return []

#=================================================
# SUPPORT CLASSES
#=================================================

class Mode(object):
   '''Contains constants that represent the state of the interpreter.'''
   CONSOLE = 0
   CLI     = 1
   WEB     = 2
   JOB     = 3
   
   def __init__(self):
       raise NotImplementedError('This class should never be instantiated.')
