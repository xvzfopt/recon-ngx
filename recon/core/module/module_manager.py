# =====================================================================================
# Imports: External
# =====================================================================================
import requests
import os
import yaml
import re
import sys
import json
import importlib
import importlib.util
import shutil
from copy import deepcopy
from datetime import datetime
from requests.exceptions import HTTPError

# =====================================================================================
# Imports: Internal
# =====================================================================================
from .dependency_manager import DependencyManager
from recon.utils import utils
from recon.core.exceptions import ModuleDownloadFailure

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
    URL_MARKETPLACE = 'https://raw.githubusercontent.com/xvzfopt/recon-ngx-marketplace'

    MODULE_STATUS_UNINSTALLED   = "Uninstalled"
    MODULE_STATUS_INSTALLED     = "Installed"
    MODULE_STATUS_OUTDATED      = "Outdated"
    MODULE_STATUS_DISABLED      = "Disabled"

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, home_path, modules_path, console, framework, marketplace_branch):
        '''
        Constructor

        :param home_path: Path to the recon-ngx home directory
        :type home_path: str
        :param modules_path: Path to the modules directory
        :type modules_path: str
        :param console: Console Output Instance
        :type console: ConsoleOutput
        :param marketplace_branch: The Marketplace Branch to use
        :type marketplace_branch
        '''
        self._console = console
        self._module_index = []
        self._loaded_modules = {}
        self._module_categories = {}
        self._framework = framework
        self._marketplace_branch = marketplace_branch

        # Build Paths
        self._home_path = home_path
        self._modules_path = modules_path

        # Initialise Local Modules Ind, indent=2ex
        self._build_local_index()

        # Initialse Dependency Manager
        self._dep_manager = DependencyManager(self._console)

    # =====================================================================================
    # Index Functions
    # =====================================================================================
    def fetch_marketplace_index(self):
        '''
        Fetches the Modules index from the Marketplace
        '''
        url = self.get_marketplace_url() + "/modules.yml"
        self._console.debug("Fetching Marketplace Index => %s" % url)
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
                if loaded.meta.version != module['version']:
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
        # Store Options
        options = module.get_options()
        success, reloaded_module = self._load_package_module(module.get_package_path(), True)
        reloaded_module.set_options(options)
        return success, reloaded_module

    def load_modules(self):
        '''
        Loads locally installed modules
        '''
        self._loaded_modules.clear()

        # Traverse Modules Folder for recon-ngx modules
        self._console.debug("Loading Modules from %s" % self._modules_path)
        for dirpath, dirnames, filenames in os.walk(self._modules_path, followlinks=True):

            # =====================================================================================
            # LOAD: Module Package
            # =====================================================================================
            if utils.is_python_package(dirpath):
                self._console.debug("Found a Package to load: %s" % dirpath)
                self._load_package_module(dirpath)
                # Don't traverse any further
                dirnames.clear()

        # Clean Modules Directory
        utils.remove_empty_dirs(self._modules_path)
        # Refresh Modules Index
        self._build_local_index()

    def _load_package_module(self, dirpath, reload=False):
        '''
        Loads a specific module

        :param dirpath: Path to the directory containing the file module
        :type dirpath: str
        :param filename: The filename of the module
        :type filename: str
        :param reload: Whether the module is being reloaded. Defaults to False
        :type reload: bool
        :returns: Whether the module was imported successfully, the loaded module instance
        :rtype: bool, BaseModule
        '''
        self._console.debug("Processing module ---> %s" % dirpath)
        saved_options = None
        modules_dir_name = os.path.split(self._modules_path.rstrip("/"))[1]

        # Build Module information
        package_name = os.path.split(dirpath)[-1]
        mod_info = {}
        mod_info["name"] = package_name
        mod_info["category"] = re.search('.*?/%s/([^/]*)' % modules_dir_name, dirpath).group(1)
        mod_info["fqn"] = '/'.join(re.split('.*?/%s/' % modules_dir_name, dirpath)[-1].split('/'))
        mod_info["loadname"] = mod_info["fqn"].replace('/', '_')
        mod_info["loadpath"] = dirpath
        self._console.debug("Processing Package module ---> %s" % json.dumps(mod_info, indent=2))

        # =====================================================================================
        # Handle Module Reload
        # =====================================================================================
        if reload and mod_info["loadname"] in sys.modules:
            self._console.debug("Module is being reloaded...")

            # Save options so they can be restored
            current_module = self.get_module_instance(mod_info["fqn"])
            saved_options = deepcopy(current_module.get_options())

            # Clean current imports & instances
            importlib.invalidate_caches()
            sys.modules.pop(mod_info["loadname"])
            del self._loaded_modules[mod_info["fqn"]]

        # =====================================================================================
        # Attempt Module Import
        # =====================================================================================
        try:

            # Import module and instantiate
            module = utils.load_package_module(package_name, mod_info["loadpath"])
            sys.modules[mod_info["loadname"]] = module
            mod_instance = module.Module(mod_info["name"], mod_info["fqn"], self._framework)

            self._console.debug("Module ID: %s" % id(module))
            self._console.debug("Module class ID: %s" % id(module.Module))

            # Add the module to the framework's loaded modules
            self._loaded_modules[mod_info["fqn"]] = mod_instance
            self._add_module_to_category(mod_info["category"], mod_info["fqn"])

            # Restore options
            if saved_options:
                mod_instance._options = saved_options

            # Success
            return True, mod_instance

        # =====================================================================================
        # Exception: Unhandled
        # =====================================================================================
        except:
            # notify the user of errors
            self._console.error(f"An exception occurred while importing module '{mod_info["name"]}'")
            self._console.print_exception()
            self._console.error(f"Module '{mod_info["fqn"]}' disabled.")

        # Module Import failed: Remove the module from the loaded modules
        self._loaded_modules.pop(mod_info["fqn"], None)
        self._add_module_to_category('disabled', mod_info["fqn"])

        return False, None

    # def _load_package_module(self, path):
    #     '''
    #     Loads a package module at the specified path
    #
    #     :param path: Path to the package module to load
    #     :type path: str
    #     '''
    #
    #     mod_info = {}
    #     mod_info["dirpath"], mod_info["name"] = os.path.split(path)
    #     mod_info["category"] = re.search('/modules/([^/]*)', mod_info["dirpath"]).group(1)
    #     mod_info["fqn"] = '/'.join(re.split('/modules/', mod_info["dirpath"])[-1].split('/') + [mod_info["name"]])
    #
    #     self._console.debug("Processing Package module ---> %s" % json.dumps(mod_info, indent=2))
    #
    #     # =====================================================================================
    #     # Attempt Package Import
    #     # =====================================================================================
    #     with utils.add_to_path(mod_info["dirpath"]):
    #         try:
    #             package_import = importlib.import_module(mod_info["name"])
    #             print(package_import)
    #             sys.exit()
    #
    #             self._loaded_modules[mod_info["fqn"]] = sys.modules[mod_info["name"]].Module(mod_info["fqn"])
    #             self._add_module_to_category(mod_info["category"], mod_info["fqn"])
    #
    #             # Success
    #             return True
    #         # =====================================================================================
    #         # Exception: Module has missing dependency
    #         # =====================================================================================
    #         except ImportError as e:
    #             # notify the user of missing dependencies
    #             self._console.error(f"Module '{mod_info["fqn"]}' disabled. Dependency required: '{utils.to_unicode_str(e)[16:]}'")
    #
    #         # =====================================================================================
    #         # Exception: Unhandled
    #         # =====================================================================================
    #         except:
    #             # notify the user of errors
    #             self._console.error(f"An exception occurred while importing module '{mod_info["name"]}'")
    #             self._console.print_exception()
    #             self._console.error(f"Module '{mod_info["fqn"]}' disabled.")
    #
    #     # Module Import failed: Remove the module from the loaded modules
    #     self._loaded_modules.pop(mod_info["fqn"], None)
    #     self._add_module_to_category("disabled", mod_info["fqn"])
    #
    #     return False

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
    def install_module(self, module_data):
        '''
        Installs the specified module

        :param module_data: The module's data dict
        :type module_data: dict
        '''
        downloads = {}

        # Process Module Data
        path = module_data["path"]
        dependencies = module_data["dependencies"]

        # =====================================================================================
        # Check Module Dependencies
        # =====================================================================================
        if dependencies:
            self._console.debug("Checking dependencies for module --> %s" % path)
            missing_dependencies = []

            for dependency in dependencies:
                if not self._dep_manager.is_satisfied(dependency):
                    missing_dependencies.append(dependency)

            if missing_dependencies:
                self._console.alert("Missing dependencies detected")
                for dependency in missing_dependencies:
                    self._console.alert(f"{self._console.SPACER} - {dependency}")

                choice = ""
                while choice not in ["y", "n"]:
                    choice = self._framework.read_input("Install dependencies now? (Y/n):", default="y")

                if choice == "n":
                    self._console.output("Skipping module installation")
                    return

            self._console.output("Installing dependencies. Please Wait...")
            for dependency in missing_dependencies:
                self._dep_manager.install(dependency)
                self._console.output("Dependency installed: %s" % dependency)

        # =====================================================================================
        # Download the module
        # =====================================================================================
        try:
            self._console.output("Downloading Module from Marketplace. Please wait...")
            success = self.fetch_marketplace_module(module_data)
            if not success:
                raise ModuleDownloadFailure()
        except:
            self._console.error(f"Module installation failed: {path}")
            raise

        self._console.output(f"Module installed: {path}")

    def uninstall_module(self, module_data):
        '''
        Uninstalls the specified module

        :param module_data: The module's data dict
        :type module_data: dict
        '''

        # Process Module Data
        path = module_data["path"]
        dependencies = module_data["dependencies"]
        
        # =====================================================================================
        # Process Dependencies
        # =====================================================================================
        if dependencies:
            self._console.output("Processing module dependencies (%s)" % len(dependencies))
        for dependency in dependencies:
            choice = ""
            while choice not in ["y", "n"]:
               choice = self._framework.read_input(
                   f"Uninstall dependency '{self._dep_manager.package_name_from_specifier(dependency)}'? (y/N):",
                   default="n"
               )

            if choice == "y":
                self._dep_manager.uninstall(dependency)
                self._console.output("Dependency uninstalled")

        # =====================================================================================
        # Remove Module File
        # =====================================================================================
        abs_path = os.path.join(self._modules_path, path)
        self._console.debug("Deleting Module at path: %s" % abs_path)
        shutil.rmtree(abs_path)

        self._console.output(f"Module uninstalled: {path}")

    # =====================================================================================
    # Getters
    # =====================================================================================
    def get_marketplace_url(self):
        '''
        Gets the Recon-NGX Marketplace URL

        :returns: The Recon-NGX Marketplace URL
        :rtype:
        '''
        return self.URL_MARKETPLACE + f"/{self._marketplace_branch}"

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
    def fetch_marketplace_module(self, module_data):
        '''
        Fetches a module from the Marketplace

        :param module_data: The module data
        :type module_data: dict
        :returns: True if the module was downloaded successfully, otherwise False
        :rtype bool
        '''
        module_path = module_data["path"]

        # Iterate and fetch Module files
        for filename in module_data['files']:
            self._console.debug("Fetching Module file: %s" % filename)
            self.fetch_marketplace_file(
                target_file=os.path.join("modules", module_path, filename),
                dest=os.path.join(self._modules_path, module_path, filename)
            )

        return True

    def fetch_marketplace_file(self, target_file, dest):
        '''
        Fetches the specified file from the recon-ngx Marketplace

        :param target_file: The path of the file to fetch
        :type target_file: str
        :param dest: The destination path to write the file to
        :type dest: str
        :returns: The file content
        :rtype: str
        '''
        success = False
        url = self.get_marketplace_url() + "/%s" % target_file
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
            module_data["files"]            = utils.find_directory_files(module.get_package_path(), excluded_dirs=["__pycache__"])

            # Meta data
            module_data["author"]           = module.meta.authors
            module_data["name"]             = module.meta.name
            module_data["description"]      = module.meta.description
            module_data["version"]          = module.meta.version

            # Optional Data
            module_data["dependencies"]     = module.meta.dependencies
            module_data["required_keys"]    = module.meta.required_keys

            index.append(module_data)

        return index
