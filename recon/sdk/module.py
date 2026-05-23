"""
Recon-NGX - Module SDK - Base Module
================================
Contains The BaseModule class that all Recon-NGX Modules should inherit from.
"""

# =====================================================================================
# Imports: External
# =====================================================================================
import html
import http.cookiejar
import io
import os
import sys
import json
import requests

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.core.options import Options
from recon.sdk.exceptions import ModuleValidationException
from recon.utils import validators, utils

# =====================================================================================
# Recon-NGX Base Module
# =====================================================================================
class BaseModule:
    '''
    Recon-NGX Base Module
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    meta = None
    data_path = ""

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, name, fqn, recon):
        '''
        Constructor

        :param name: The name of the module
        :type name: str
        :param fqn: The Fully Qualified Name of the module, e.g. discovery/test/module1
        :type fqn: str
        :param recon: The Recon-NGX App instance
        :type recon: ReconNGXApp
        '''
        self.__name = name
        self.__fqn = fqn
        self.__recon = recon
        self.__workspace = self.__recon.get_current_workspace()
        self.__db = self.__workspace.get_db()
        self.__key_manager = self.__recon.get_key_manager()
        self.__module_manager = self.__recon.get_module_manager()
        self.__console = self.__recon.get_console()
        self.__options = Options()
        self._summary_counts = {}
        self.keys = {}

        # =====================================================================================
        # Set query for SOURCE inputs
        # =====================================================================================
        if self.meta.query:
            self._default_source = self.meta.query
            self.__options.register_option('source', 'default', True, 'source of input (see \'info\' for details)')

        # =====================================================================================
        # Register Module Options
        # =====================================================================================
        if self.meta.options:
            for option in self.meta.options:
                self.__options.register_module_option(option)

        # =====================================================================================
        # Register any required keys
        # =====================================================================================
        for key in self.meta.required_keys:
            # Add key to the database
            if not self.__key_manager.has_key(key):
                self.___key_manager.add_key(key, "")

            # Migrate the old key if needed (from .dat file to DB)
            self.__key_manager.migrate_key(key)

            # Add key to local keys dict
            self.keys[key] = self.__key_manager.get_key_value(key)

    def preflight(self):
        '''
        Pre-run validation function. Runs any validation tasks to check that a module is correctly configured, and
        ready to execute

        :returns: True if validation succeeds, otherwise False
        :rtype: bool
        '''

        # Check Keys
        for key in self.meta.required_keys:
            # Fetch any key updates
            self.keys[key] = self.__key_manager.get_key_value(key)

            # Check key is set
            if not self.keys.get(key):
                self.__console.debug("Module preflight checks failed.")
                self.__console.error(
                    f"'{key}' key must be set for this module to run. See 'keys' command"
                )
                return False

        self.__console.debug("Module preflight checks passed.")
        return True

    def run(self, inputs):
        '''
        Module Run. Executes the Module functionality
        '''
        params = []
        self._summary_counts.clear()

        # Execute any pre-run tasks
        try:
            additional_params = self.module_pre()
        except ModuleValidationException as e:
            self.__console.error(str(e))
            return
        if additional_params is not None:
            params += additional_params

        # Add SOURCE inputs to parameters
        if inputs:
            params.insert(0, inputs)

        # Execute Module!
        self.module_run(*params)
        self._record_module_run()

        # Execute any post-run tasks
        self.module_post()

    # =====================================================================================
    # Module Hook Methods
    # =====================================================================================
    def module_pre(self):
        '''
        Pre-process function

        Called prior to execution of the "module_run" method. Provides an opportunity for Modules to perform
        setup tasks, further validation, etc. This function can return a list additional parameters, which are
        passed to the "module_run" function

        :returns: A list of additional parameters
        :rtype: list, optional
        '''
        pass

    def module_run(self, inputs):
        '''
        Module Execution Function. Add the main logic of your Module here

        :param inputs: The Source inputs that the module will be run against
        :type inputs: list
        '''
        pass

    def module_post(self):
        '''
        Post-process function

        Called after execution of the "module_run" method. Provides an opportunity for Modules to perform any
        clean-up or tear-down tasks
        '''
        pass

    # =====================================================================================
    # Keys Functions (Backward compatibility)
    # =====================================================================================
    def get_key(self, key_name):
        '''
        Gets the value of the specified key

        :param key_name: The name of the target key
        :type key_name: str
        '''
        return self.__key_manager.get_key_value(key_name)

    # =====================================================================================
    # Console Output Functions
    # =====================================================================================
    def print_exception(self, line=''):
        '''
        Prints a caught exception

        :param line: Additional information to print alongside the exception. Optional
        :type line: str
        '''
        self.__get_console().print_exception(line)

    def output(self, line):
        '''
        Formats and prints normal output

        :param line: The message/data to print
        :type line: str
        '''
        self.__get_console().output(line)

    def error(self, line):
        '''
        Formats and prints an Error

        :param line: The Error message/data to print
        :type line: str
        '''
        self.__get_console().error(line)

    def alert(self, line):
        '''
        Formats and prints important output

        :param line: The message/data to print
        :type line: str
        '''
        self.__get_console().alert(line)

    def verbose(self, line):
        '''
        Formats and prints output if in verbose mode

        :param line: The message/data to print
        :type line: str
        '''
        self.__get_console().verbose(line)

    def debug(self, line):
        '''
        Formats and prints output if in debug mode

        :param line: The message/data to print
        :type line: str
        '''
        self.__get_console().debug(line)

    def heading(self, line, level=1):
        '''
        Formats and prints a styled header

        :param line: The header/title to print
        :type line: str
        :param level: The header/title indentation level
        '''
        return self.__get_console().heading(line, level)

    def table(self, data, header=[], title=''):
        '''
        Formats and prints a table

        :param data: The rows to print
        :type data: list
        :param header: Table Header row (Optional)
        :type header: list, optional
        :param title: The table's title (Optional)
        :type title: str
        '''
        return self.__get_console().table(data, header, title)

    # =====================================================================================
    # Support/Helper Methods
    # =====================================================================================
    def html_unescape(self, s):
        '''
        Unescapes HTML markup and returns an unescaped string.

        :param s: The string to unescape
        :type s: str
        :return: The unescaped string
        :rtype: str
        '''
        return utils.html_unescape(s)

    def html_escape(self, s):
        '''
        Escapes HTML characters in the specified content

        :param s: The string to escape
        :type s: str
        :return: The escaped string
        :rtype: str
        '''
        return utils.html_escape(s)

    def cidr_to_list(self, string):
        '''
        Expands the provided CIDR string to a range of IP Addresses

        :param string: The CIDR string to expand
        :type string: str
        :return: A list of IP Addresses
        :rtype: list
        '''
        return utils.cidr_to_list(string)

    @staticmethod
    def hosts_to_domains(hosts, exclusions=[]):
        '''
        Parses a list of "hosts" and extracts all possible domains.

        This function is a little misleading/amgiguous. What it's effectively doing is ignoring the lowest subdomain,
        and then expanding all levels of the remaining domain name.
        For example, "test.apis.google.com" would become ["apis.google.com", "google.com"]. Domain names in the
        exclusions list will be skipped

        :param hosts: The list of hosts to extract domains from
        :type hosts: list
        :param exclusions: A list of domain names that should be included and skipped (optional)
        :type exclusions: list, optional
        '''
        return utils.hosts_to_domains(hosts, exclusions)

    def make_cookie(self, name, value, domain, path='/'):
        '''
        Builds a HTTP request cookie

        :param name: The Cookie name
        :type name: str
        :param value: The Cookie value
        :type value: str
        :param domain: The domain associated with the Cookie
        :type domain: str
        :param path: The cookie path (TBC)
        :type path: str
        '''
        return http.cookiejar.Cookie(
            version=0, name=name, value=value, port=None, port_specified=False, domain=domain, domain_specified=True,
            domain_initial_dot=False, path=path, path_specified=True, secure=False, expires=None, discard=False,
            comment=None, comment_url=None, rest=None
        )

    def request(self, method, url, **kwargs):
        '''
        Performs an HTTP request

        :param method: The HTTP method to use
        :type method: str
        :param url: The target URL
        :type url: str
        '''

        # Process Timeout
        kwargs["timeout"] = kwargs.get("timeout", self.__recon.get_options()["timeout"])

        # =====================================================================================
        # Build headers
        # =====================================================================================
        kwargs["headers"] = kwargs.get("headers", {})
        if "user-agent" not in [header.lower() for header in kwargs["headers"]]:
            kwargs["headers"]["user-agent"] = self.__recon.get_options()["user-agent"]
        # Normalize Headers capitalisation
        kwargs["headers"] = {k.title(): v for k, v in kwargs["headers"].items()}

        # =====================================================================================
        # Process Proxy
        # =====================================================================================
        proxy = self.__recon.get_options()["proxy"]
        if proxy:
            kwargs["proxies"] = {
                "http": "http://%s" % proxy,
                "https": "https://%s" % proxy,
            }

        # =====================================================================================
        # TLS Validation
        # =====================================================================================
        kwargs["verify"] = False
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

        # =====================================================================================
        # Send Request
        # =====================================================================================
        func = getattr(requests, method.lower())
        resp = func(url, **kwargs)

        # =====================================================================================
        # Handle Output
        # =====================================================================================
        if self.__recon.get_verbosity() > 1:
            utils.print_http_request(resp.request, self.__console)
            utils.print_http_response(resp, self.__console)

        return resp

    # =====================================================================================
    # DB Methods (Proxy/Facade methods)
    # =====================================================================================
    def query(self, *args, **kwargs):
        '''
        Performs a direct Workspace Database query
        '''
        return self.__get_db().query(*args, **kwargs)

    def insert_domains(self, domain=None, notes=None, mute=None):
        '''
        Adds a domain name to the Workspace Database

        :param domain: The new domain name to add
        :type domain: str
        :param notes: Any notes on the domain name being added
        :type notes: str
        :param mute: Whether the returns of the table should be displayed after row insertion
        :type mute: bool
        '''
        return self.__get_db().insert_domains(domain, notes, mute)

    def insert_companies(self, company=None, description=None, notes=None, mute=False):
        '''
        Adds a company to the Workspace Database

        :param company: The new company name to add
        :type company: str
        :param description: A description of the company
        :type description: str
        :param notes: Any notes on the company being added
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''
        return self.__get_db().insert_companies(company, description, notes, mute)

    def insert_netblocks(self, netblock=None, notes=None, mute=False):
        '''
        Adds a netblock to the Workspace Database

        :param netblock: The netblock to add
        :type netblock: str
        :param notes: Any notes on the netblock being added
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''
        return self.__get_db().insert_netblocks(netblock, notes, mute)

    def insert_locations(self, latitude=None, longitude=None, street_address=None, notes=None, mute=False):
        '''
        Adds a location to the Workspace Database

        :param latitude: The Latitude of the location
        :type latitude: str
        :param latitude: The Latitude of the location
        :type latitude: str
        :param street_address: The street address of the location
        :type street_address: str
        :param notes: Any notes on the location being added
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''
        return self.__get_db().insert_locations(latitude, longitude, street_address, notes, mute)

    def insert_vulnerabilities(self, host=None, reference=None, example=None, publish_date=None, category=None,
                               status=None, notes=None, mute=False):
        '''
        Adds a vulnerability to the database and returns the affected row count.

        :param host: The Hostname or IP Address of the vulnerable host
        :type host: str
        :param reference: The vulnerability reference
        :type reference: str
        :param example: The vulnerability example
        :type example: str
        :param publish_date: The publish date of the vulnerability
        :type publish_date: str
        :param category: A category for the vulnerability
        :type category: str
        :param status: A vulnerability status
        :type status: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''
        return self.__get_db().insert_vulnerabilities(host, reference, example, publish_date, category, status, notes, mute)

    def insert_ports(self, ip_address=None, host=None, port=None, protocol=None, banner=None, notes=None, mute=False):
        '''
        Adds a port to the Workspace Database

        :param ip_address: The IP Address of the host for this port
        :type ip_address: str
        :param host: The Hostname of the host for this port
        :type host: str
        :param port: The Port Number
        :type port: str
        :param protocol: The Protocol associated with the port number, e.g. SSH
        :type protocol: str
        :param banner: The banner of the service listening on the port
        :type banner: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''
        return self.__get_db().insert_ports(ip_address, host, port, protocol, banner, notes, mute)

    def insert_hosts(self, host=None, ip_address=None, region=None, country=None, latitude=None, longitude=None,
                     notes=None, mute=False):
        '''
        Adds a host to the Workspace Database

        :param host: The hostname of the host
        :type host: str
        :param ip_address: The IP Address of the host
        :type ip_address: str
        :param region: The region in which the host is located
        :type region: str
        :param country: The country in which the host is located
        :type country: str
        :param latitude: The latitude where the host is located
        :type latitude: str
        :param longitude: The longitude where the host is located
        :type longitude: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''
        return self.__get_db().insert_hosts(host, ip_address, region, country, latitude, longitude, notes, mute)

    def insert_contacts(self, first_name=None, middle_name=None, last_name=None, email=None, title=None, region=None,
                        country=None, phone=None, notes=None, mute=False):
        '''
        Adds a contact to the Workspace Database

        :param first_name: The first name of the contact
        :type first_name: str
        :param middle_name: The middle name of the contact
        :type middle_name: str
        :param last_name: The last name of the contact
        :type last_name: str
        :param email: The email address of the contact
        :type email: str
        :param title: The contact's title
        :type title: str
        :param region: The region in which the contact is located
        :type region: str
        :param country: The country in which the contact is located
        :type country: str
        :param phone: The phone number of the contact
        :type phone: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''
        return self.__get_db().insert_contacts(
            first_name, middle_name, last_name, email, title, region, country, phone, notes, mute
        )

    def insert_credentials(self, username=None, password=None, _hash=None, _type=None, leak=None, notes=None,
                           mute=False):
        '''
        Adds a set of credentials to the Workspace Database

        :param username: The username
        :type username: str
        :param password: The password
        :type password: str
        :param _hash: The hash of the password
        :type _hash: str
        :param _type: The hash type of the password
        :type _type: str
        :param leak: A leak associated with this credential set
        :type leak: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''
        return self.__get_db().insert_credentials(username, password, _hash, _type, leak, notes, mute)

    def insert_leaks(self, leak_id=None, description=None, source_refs=None, leak_type=None, title=None,
                     import_date=None, leak_date=None, attackers=None, num_entries=None, score=None,
                     num_domains_affected=None, attack_method=None, target_industries=None, password_hash=None,
                     password_type=None, targets=None, media_refs=None, notes=None, mute=False):
        '''
        Adds a leak to the Workspace Database

        :param leak_id: The ID associated with the leak
        :type leak_id: int
        :param description: A description of the leak
        :type description: str
        :param source_refs: References for the leak
        :type source_refs: str
        :param leak_type: The leak type
        :type leak_type: str
        :param title: The leak's title
        :type title: str
        :param import_date: The source data of the leak (TBC)
        :type import_date: str
        :param leak_date: The date of the leak
        :type leak_date: str
        :param attackers: The attackers responsible for/associated with the leak
        :type attackers: str
        :param num_entries: The number of entries associated within the leak
        :type num_entries: str
        :param score: A score associated with the leak
        :type score: str
        :param num_domains_affected: The number of domains affected by the leak
        :type num_domains_affected: str
        :param attack_method: An attack method associated with the leak
        :type attack_method: str
        :param target_industries: The industries targeted in the leak
        :type target_industries: str
        :param password_hash: The password hash of the leak (TBC)
        :type password_hash: str
        :param password_type: The password's hash type (TBV)
        :type password_type: str
        :param targets: The targets associated with the leak
        :type targets: str
        :param media_refs: Any media references associated with the leak
        :type media_refs: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''
        return self.__get_db().insert_leaks(
            leak_id, description, source_refs, leak_type, title, import_date, leak_date, attackers, num_entries,
            score, num_domains_affected, attack_method, target_industries, password_hash, password_type, targets,
            media_refs, notes, mute
        )

    def insert_pushpins(self, source=None, screen_name=None, profile_name=None, profile_url=None, media_url=None,
                        thumb_url=None, message=None, latitude=None, longitude=None, time=None, notes=None, mute=False):
        '''
        Adds a pushpin to the Workspace Database

        :param source: The source associated with the pushpin
        :type source: str
        :param screen_name: The screen_name of the account associated with the pushpin (TBC)
        :type screen_name: str
        :param profile_name: The profile_name of the account associated with the pushpin (TBC)
        :type profile_name: str
        :param profile_url: The URL of the account associated with the pushpin (TBC)
        :type profile_url: str
        :param media_url: The Media URL of the pushpin (TBC)
        :type media_url: str
        :param thumb_url: The URL of the thumbnail associated with the pushpin (TBC)
        :type thumb_url: str
        :param message: The pushpin message/text content
        :type message: str
        :param latitude: The latitude of the pushpin
        :type latitude: str
        :param longitude: The longitude of the pushpin
        :type longitude: str
        :param time: The pushpin time/date
        :type time: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''
        return self.__get_db().insert_pushpins(
            source, screen_name, profile_name, profile_url, media_url, thumb_url,
            message, latitude, longitude, time, notes, mute
        )

    def insert_profiles(self, username=None, resource=None, url=None, category=None, notes=None, mute=False):
        '''
        Adds a profile to the Workspace Database

        :param username: The username of the profile's account
        :type username: str
        :param resource: The profile resource (TBC)
        :type resource: str
        :param url: The profile url
        :type url: str
        :param category: A category for the profile
        :type category: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''
        return self.__get_db().insert_profiles(username, resource, url, category, notes, mute)

    def insert_repositories(self, name=None, owner=None, description=None, resource=None, category=None, url=None,
                            notes=None, mute=False):
        '''
        Adds a repository to the Workspace Database

        :param name: The name of the repository
        :type name: str
        :param owner: The owner of the repository
        :type owner: str
        :param description: A description of the repository
        :type description: str
        :param resource: The repository resource (TBC)
        :type resource: str
        :param category: The repository's category
        :type category: str
        :param url: The repository url
        :type url: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''
        return self.__get_db().insert_repositories(name, owner, description, resource, category, url, notes, mute)

    # =====================================================================================
    # Getters
    # =====================================================================================
    def get_name(self):
        '''
        Gets the module's name

        :return: The module's name
        :rtype: str
        '''
        return self.__name

    def get_fqn(self):
        '''
        Gets the Module's Fully Qualified Name, e.g. reporting/test/module1
        '''
        return self.__fqn

    def get_options(self):
        '''
        Gets the module's options
        '''
        return self.__options

    def get_option_value(self, option_name, default=None):
        '''
        Gets the value of the specified option

        :param option_name: The name of the target option
        :type option_name: str
        :param default: A value to be returned if the option does not exist. Defaults to None
        :type: any, optional
        '''
        value = default
        options = self.get_options()
        if option_name in options:
            value = options[option_name]
        return value

    def get_meta_property(self, property):
        '''
        Gets the value of the specified meta property. Returns None if property does not exist

        :returns: The value of the specified meta property, or None
        :rtype: any
        '''
        value = None
        if hasattr(self.meta, property):
            value = getattr(self.meta, property)
        return value

    def get_data_path(self):
        '''
        Gets the path to the Recon NGX data folder

        '''
        return self.__recon.get_data_path()

    def get_downloads_path(self):
        '''
        Gets the path to the current Workspace Downloads folder

        '''
        return self.get_workspace().get_downloads_path()

    def get_workspace(self):
        '''
        Gets the current Workspace instance

        :return: The current Workspace instance
        :rtype: Workspace
        '''
        return self.__workspace

    def __get_db(self):
        '''
        Gets the current Database instance

        :return: The current Database instance for the active Workspace
        :rtype: WorkspaceDB
        '''
        return self._db

    def __get_console(self):
        '''
        Gets the Console Output instance

        :return: The Console Output instance
        :rtype: ConsoleOutput
        '''
        return self.__console

    # =====================================================================================
    # Internal Functions
    # =====================================================================================
    def _validate_inputs(self, inputs):
        '''
        Module input Validator. Validates the SOURCE inputs that the module is acting upon
        This function takes the "validator" value in the module's meta dictionary, tries to match it to a validator
        class, e.g. UrlValidator, and runs the validate() function against each input

        :param inputs: The source inputs to validate
        :type inputs: list
        '''
        validator = None

        # Get Module validation type
        validator_type = self.meta.validator
        if not validator_type:
            # Passthru, no validator required
            self.__console.debug('No validator required.')
            return
        validator_name = validator_type.capitalize() + 'Validator'

        # Find validator functions
        for obj in [self, validators]:
            if hasattr(obj, validator_name):
                validator = getattr(validators, validator_name)()

        # Check Validator found
        if not validator:
            # Passthru, no validator defined
            self.__console.debug('No validator defined.')
            return

        # Run Validators against inputs
        for _input in inputs:
            validator.validate(_input)
            self.__console.debug('All inputs validated.')

    def _record_module_run(self):
        '''
        Records the execution of a module for analytics and stats
        '''
        # Get DB
        workspace = self.__recon.get_current_workspace()
        db = workspace.get_db()
        db.query(
            f"INSERT OR REPLACE INTO dashboard (module, runs) VALUES ('{self.get_fqn()}', "
            f"COALESCE((SELECT runs FROM dashboard WHERE module='{self.get_fqn()}')+1, 1))"
        )


