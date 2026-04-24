# =====================================================================================
# Imports: External
# =====================================================================================
from importlib.metadata.diagnose import inspect

import requests
import os
import yaml
import re
import sys
import importlib
import json
from datetime import datetime

from requests.exceptions import HTTPError
from importlib.machinery import SourceFileLoader
from contextlib import contextmanager

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.utils import utils

# =====================================================================================
# Module Manager Class
# =====================================================================================
class ModuleManager:
    '''
    Recon-NGX Module Manager
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    URL_MARKETPLACE = 'https://raw.githubusercontent.com/xvzfopt/recon-ngx-marketplace/master/'

    MODULE_STATUS_UNINSTALLED   = "Uninstalled"
    MODULE_STATUS_INSTALLED     = "Installed"
    MODULE_STATUS_OUTDATED      = "Outdated"
    MODULE_STATUS_DISABLED      = "Disabled"

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, home_path, console, framework):
        '''
        Constructor

        :param home_path: Path to the recon-ngx home directory
        :type home_path: str
        :param console: Console Output Instance
        :type console: ConsoleOutput
        '''
        self._console = console
        self._module_index = []
        self._loaded_modules = {}
        self._module_categories = {}
        self._framework = framework

        # Build Paths
        self._home_path = home_path
        self._modules_path = os.path.join(self._home_path, 'modules')
        self._data_path = os.path.join(self._home_path, 'data')

        # Initialise Local Modules Index
        self._build_local_index()

    # =====================================================================================
    # Index Functions
    # =====================================================================================
    def fetch_marketplace_index(self):
        '''
        Fetches the Modules index from the Marketplace
        '''
        self._console.debug("Fetching Marketplace Index...")
        url = self.URL_MARKETPLACE + "/modules.yml"
        file_dest = os.path.join(self._home_path, "modules.yml")

        # Fetch Index
        try:
            r = requests.get(url)
            if not r.status_code == 200:
                raise HTTPError(r.status_code)
        except Exception as ex:
            self._console.error(f"Unable to fetch Marketplace Index ({type(ex).__name__} --> {str(ex)})")
            return

        utils.write_local_file(file_dest, r.text)
        self._build_local_index()

    def search_module_index(self, s):
        '''
        Searches the module index for a specific module

        :param s: The search string
        :type s: str
        '''
        keys = ('path', 'name', 'description', 'status')
        modules = []
        for module in self._module_index:
            for key in keys:
                if re.search(s, module[key]):
                    modules.append(module)
                    break
        return modules

    def _build_local_index(self):
        '''
        Builds the local Modules index
        '''
        self._console.debug('Updating index file...')
        self._module_index = []

        # Initialise module index from local copy
        path = os.path.join(self._home_path, 'modules.yml')
        if os.path.exists(path):
            with open(path, 'r') as infile:
                self._module_index = yaml.safe_load(infile)

        # Add status to index for each module
        for module in self._module_index:
            status = self.MODULE_STATUS_UNINSTALLED
            if module['path'] in self._loaded_modules.get('disabled', []):
                status = self.MODULE_STATUS_DISABLED
            elif module['path'] in self._loaded_modules.keys():
                status = self.MODULE_STATUS_INSTALLED
                loaded = self._loaded_modules[module['path']]
                if loaded.meta['version'] != module['version']:
                    status = self.MODULE_STATUS_OUTDATED
            module['status'] = status

        self._console.debug("Module index: %s" % self._module_index)

    # =====================================================================================
    # Module Load Functions
    # =====================================================================================
    def reload_module(self, module):
        '''
        Reloads a specific Module

        :param module: The module to reload
        :type module: BaseModule
        '''
        dirpath = os.path.dirname(os.path.join(self._modules_path, module.get_fqn()))
        filename = module.get_name() + ".py"
        return self._load_file_module(dirpath, filename)

    def load_modules(self):
        '''
        Loads locally installed modules
        '''

        # Traverse Modules Folder for recon-ngx modules
        for dirpath, dirnames, filenames in os.walk(self._modules_path, followlinks=True):

            # LOAD: Package Module
            if self.is_python_package(dirpath):
                # self._load_package_module(dirpath)
                # Don't traverse any further
                dirnames.clear()
            # LOAD: File Module
            else:
                for filename in filenames:
                    if not filename.endswith('.py'):
                        continue
                    self._load_file_module(dirpath, filename)

        # Clean Modules Directory
        utils.remove_empty_dirs(self._modules_path)
        # Refresh Modules Index
        self._build_local_index()

    def _load_file_module(self, dirpath, filename):
        '''
        Loads a specific module

        :param dirpath: Path to the directory containing the file module
        :type dirpath: str
        :param filename: The filename of the module
        :type filename: str
        :returns: Whether the module was imported successfully
        :rtype: bool
        '''

        # Build Module information
        mod_info = {}
        mod_info["name"] = filename.split('.')[0]
        mod_info["category"] = re.search('/modules/([^/]*)', dirpath).group(1)
        mod_info["dispname"] = '/'.join(re.split('/modules/', dirpath)[-1].split('/') + [mod_info["name"]])
        mod_info["loadname"] = mod_info["dispname"].replace('/', '_')
        mod_info["loadpath"] = os.path.join(dirpath, filename)
        mod_file = open(mod_info["loadpath"])
        self._console.debug("Processing file module ---> %s" % json.dumps(mod_info, indent=2))

        # =====================================================================================
        # Attempt Module Import
        # =====================================================================================
        try:
            # Import the module into memory
            mod = SourceFileLoader(mod_info["loadname"], mod_info["loadpath"]).load_module()
            __import__(mod_info["loadname"])

            # Add the module to the framework's loaded modules
            self._loaded_modules[mod_info["dispname"]] = sys.modules[mod_info["loadname"]].Module(mod_info["name"], mod_info["dispname"], self._framework)
            self._add_module_to_category(mod_info["category"], mod_info["dispname"])

            # Success
            return True

        # =====================================================================================
        # Exception: Module has missing dependency
        # =====================================================================================
        except ImportError as e:
            # notify the user of missing dependencies
            self._console.error(f"Module '{mod_info["dispname"]}' disabled. Dependency required: '{utils.to_unicode_str(e)[16:]}'")

        # =====================================================================================
        # Exception: Unhandled
        # =====================================================================================
        except:
            # notify the user of errors
            self._console.error(f"An exception occurred while importing module '{mod_info["name"]}'")
            self._console.print_exception()
            self._console.error(f"Module '{mod_info["dispname"]}' disabled.")

        # Module Import failed: Remove the module from the loaded modules
        self._loaded_modules.pop(mod_info["dispname"], None)
        self._add_module_to_category('disabled', mod_info["dispname"])

        return False

    def _load_package_module(self, path):
        '''
        Loads a package module at the specified path

        :param path: Path to the package module to load
        :type path: str
        '''

        mod_info = {}
        mod_info["dirpath"], mod_info["name"] = os.path.split(path)
        mod_info["category"] = re.search('/modules/([^/]*)', mod_info["dirpath"]).group(1)
        mod_info["dispname"] = '/'.join(re.split('/modules/', mod_info["dirpath"])[-1].split('/') + [mod_info["name"]])

        self._console.debug("Processing Package module ---> %s" % json.dumps(mod_info, indent=2))

        # =====================================================================================
        # Attempt Package Import
        # =====================================================================================
        with utils.add_to_path(mod_info["dirpath"]):
            try:
                mod_import = importlib.import_module(mod_info["name"])
                self._loaded_modules[mod_info["dispname"]] = sys.modules[mod_info["name"]].Module(mod_info["dispname"])
                self._add_module_to_category(mod_info["category"], mod_info["dispname"])

                # Success
                return True
            # =====================================================================================
            # Exception: Module has missing dependency
            # =====================================================================================
            except ImportError as e:
                # notify the user of missing dependencies
                self._console.error(f"Module '{mod_info["dispname"]}' disabled. Dependency required: '{utils.to_unicode_str(e)[16:]}'")

            # =====================================================================================
            # Exception: Unhandled
            # =====================================================================================
            except:
                # notify the user of errors
                self._console.error(f"An exception occurred while importing module '{mod_info["name"]}'")
                self._console.print_exception()
                self._console.error(f"Module '{mod_info["dispname"]}' disabled.")

        # Module Import failed: Remove the module from the loaded modules
        self._loaded_modules.pop(mod_info["dispname"], None)
        self._add_module_to_category("disabled", mod_info["dispname"])

        return False

    def _add_module_to_category(self, category, mod_name):
        '''
        Adds the module to the specified category

        :param category: The category to add the module to
        :type category: str
        :param mod_name: The name of the module
        :type mod_name: str
        '''
        if not category in self._module_categories:
            self._module_categories[category] = []
        if not mod_name in self._module_categories[category]:
            self._module_categories[category].append(mod_name)


    # =====================================================================================
    # Installation Functions
    # =====================================================================================
    def install_module(self, path):
        '''
        Installs the specified module

        :param path: The module's path (e.g. discovery/module1)
        :type path: str
        '''
        downloads = {}

        # Download supporting data files
        data_files = self.get_module_from_index(path).get('files', [])
        for data_file in data_files:
            try:
                dest_path = os.path.join(self._data_path, data_file)
                success = self.fetch_marketplace_file('/'.join(['data', data_file]), dest_path)
                if not success:
                    raise Exception()
            except:
                self._console.error(f"Supporting file download for {path} failed: ({data_file})")
                self._console.error('Module installation aborted.')
                raise

        # Download the module
        rel_path = '.'.join([path, 'py'])
        try:
            dest_path = os.path.join(self._modules_path, rel_path)
            success = self.fetch_marketplace_file('/'.join(['modules', rel_path]), dest_path)
            if not success:
                raise Exception()
        except:
            self._console.error(f"Module installation failed: {path}")
            raise

        self._console.output(f"Module installed: {path}")

    def uninstall_module(self, path):
        '''
        Uninstalls the specified module

        :param path: The module's path (e.g. discovery/module1)
        :type path: str
        '''

        # Remove Module File
        rel_path = '.'.join([path, 'py'])
        abs_path = os.path.join(self._modules_path, rel_path)
        os.remove(abs_path)

        # Remove supporting data files
        files = self.get_module_from_index(path).get('files', [])
        for filename in files:
            abs_path = os.path.join(self._data_path, filename)
            if os.path.exists(abs_path):
                os.remove(abs_path)

        self._console.output(f"Module uninstalled: {path}")

    # =====================================================================================
    # Getters
    # =====================================================================================
    def get_modules_path(self):
        '''
        Gets the path to the modules directory

        :returns: The path to the modules directory
        :rtype: string
        '''
        return self._modules_path

    def get_module_categories(self):
        '''
        Gets the dictionary of module categories and their loaded modules

        :returns: Dictionary of module categories and their loaded modules
        :rtype: dict<str:list>
        '''
        return self._module_categories

    def get_loaded_modules(self):
        '''
        Returns the dictionary of loaded modules

        :returns: Dictionary of loaded modules (name: module object)
        :rtype: dict<str:object>
        '''
        return self._loaded_modules

    def get_module_index(self):
        '''
        Returns the current Module Index

        :returns: The current Module Index
        :rtype: dict
        '''
        return self._module_index

    def get_module_instance(self, path):
        '''
        Gets the instance of the specified module, if it exists

        :returns: The matching Module instance, or None if not found
        :rtype: BaseModule, None
        '''
        instance = None
        if path in self.get_loaded_modules():
            instance = self.get_loaded_modules()[path]
        return instance

    def get_module_from_index(self, path):
        '''
        Gets the module instance of the module with the specified name

        :param path: The path of the target module
        :type path: str
        :returns: The module instance, or None if not found
        :rtype: BaseModule
        '''
        for module in self._module_index:
            if module['path'] == path:
                return module
        return None

    def is_installed(self, path):
        '''
        Checks if the specified module is installed

        :param path: The module's path
        :type path: str
        :returns: True if the module is installed, False otherwise
        :rtype: bool
        '''
        for module in self.get_module_index():
            if module['path'] == path and module["status"] in (self.MODULE_STATUS_INSTALLED, self.MODULE_STATUS_DISABLED, self.MODULE_STATUS_OUTDATED):
                return True
        return False

    def is_enabled(self, path):
        '''
        Checks if the specified module is enabled

        :param path: The module's path
        :type path: str
        :returns: True if the module is enabled, False otherwise
        :rtype: bool
        '''
        if self.is_installed(path):
            return self.get_module_index()[path]["status"] not in (self.MODULE_STATUS_UNINSTALLED, self.MODULE_STATUS_DISABLED)
        return False


    def find_matching_installed_modules(self, s):
        '''

        '''
        # return an exact match
        if s in self._loaded_modules:
            return [s]
        # use the provided name as a keyword search and return the results
        return [x for x in self._loaded_modules if s in x]

    # =====================================================================================
    # Helper Functions
    # =====================================================================================
    def is_python_package(self, path):
        '''
        Checks if the specified path points to a valid Python Package

        :param path: The path to check
        :type path: str
        :returns: True if path points to a valid python package, False otherwise
        :rtype: bool
        '''
        if not path.startswith("__") and os.path.isdir(path):
            package_init = os.path.join(path, '__init__.py')
            if os.path.isfile(package_init):
                return True
        return False

    def fetch_marketplace_file(self, path, dest):
        '''
        Fetches the specified file from the recon-ngx Marketplace

        :param path: The path of the file to fetch
        :type path: str
        :param dest: The destination path to write the file to
        :type dest: str
        :returns: The file content
        :rtype: str
        '''
        success = False
        url = self.URL_MARKETPLACE + "/%s" % path
        self._console.debug("Fetching Marketplace file --> %s" % url)

        # Fetch File
        try:
            r = requests.get(url)

            if not r.status_code == 200:
                raise HTTPError(r.status_code)
            utils.write_local_file(dest, r.text)
            success = True
        except Exception as ex:
            self._console.error(f"Unable to fetch Marketplace file ({type(ex).__name__} --> {str(ex)})")

        return success

    def create_modules_index(self, mod_path=""):
        '''
        Creates an index of the currently loaded modules (dev only)

        :param mod_path: The base module path for modules to include in the index, e.g. "reporting"
        :type mod_path: str, optional
        :returns: The produced index
        :rype: dict
        '''
        index = []

        # Find matching modules
        modules = []
        for fqn in self.get_loaded_modules():
            module = self.get_loaded_modules()[fqn]
            if fqn.startswith(mod_path) or mod_path == "all":
                modules.append(module)

        # Build Index
        for module in modules:
            module_data = {}

            # Not in Meta
            module_data["path"]             = module.get_fqn()
            module_data["last_updated"]     = datetime.strftime(datetime.now(), "%Y-%m-%d")

            # Meta data
            module_data["author"]           = module.meta.get("author")
            module_data["name"]             = module.meta.get("name")
            module_data["description"]      = module.meta.get("description")
            module_data["version"]          = module.meta.get("version", "1.0")

            # Optional Data
            module_data["dependencies"]     = module.meta.get("dependencies", [])
            module_data["files"]            = module.meta.get("files", [])
            module_data["required_keys"]    = module.meta.get("required_keys", [])

            index.append(module_data)

        return index




    def test(self):
        pass

# =====================================================================================
# Testbed
# =====================================================================================
if __name__ == '__main__':
    from recon.core.options import Options
    from recon.core.output import ConsoleOutput
    from recon.utils import utils

    options = Options()
    options.initialise_global_options("0.1.0")
    options["verbosity"] = 2
    co = ConsoleOutput(options)

    home_path = os.path.join(os.getcwd(), "test/tmp")
    mm = ModuleManager(home_path, co)
    mm.fetch_marketplace_index()
    mm.load_modules()

    print(mm._loaded_modules)
    print(mm._module_categories)