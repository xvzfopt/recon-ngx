# =====================================================================================
# Imports: External
# =====================================================================================
import random
import string
import json
import os
import sys
import re
import html
import ipaddress
import subprocess
import re
import importlib.util
from pathlib import Path
from contextlib import contextmanager


# =====================================================================================
# Imports: Internal
# =====================================================================================

# =====================================================================================
# Utility Functions
# =====================================================================================
def get_random_str(length):
    '''
    Generates a random string of the specified length, containing ASCII characters
    '''
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))

def to_unicode_str(obj, encoding='utf-8'):
    '''
    Converts non-stringish types to unicode

    :param obj: The object to convert
    :type obj: object
    :return: The converted string
    :rtype: str
    '''
    if type(obj) not in (str, bytes):
        obj = str(obj)
    obj = to_unicode(obj, encoding)
    return obj

def to_unicode(obj, encoding='utf-8'):
    '''
    Converts bytes to unicode

    :param obj: The bytes object to convert
    :type obj: bytes
    :return: The converted bytes object
    :rtype: str
    '''
    if isinstance(obj, bytes):
        obj = obj.decode(encoding)
    return obj

def write_local_file(path, content):
    '''
    Writes the provided content to the specified local file

    :param path: The path to write the content to
    :type path: str
    :param content: The content to write
    :type content: str
    '''
    dirpath = os.path.dirname(path)
    if not os.path.isdir(dirpath):
        os.makedirs(dirpath)
    with open(path, 'w') as file:
        file.write(content)

def json_pretty_print(data):
    '''
    Pretty prints the provided data
    '''
    print(json.dumps(data, indent=4))


def remove_empty_dirs(base_path):
    '''
    Recursively removes empty directories

    :param base_path: The base path to remove empty directories from
    :type base_path: str
    '''
    for root, dirs, files in os.walk(base_path, topdown=False):
        for rel_path in dirs:
            abs_path = os.path.join(root, rel_path)
            if os.path.exists(abs_path) and not os.listdir(abs_path):
                os.removedirs(abs_path)

@contextmanager
def add_to_path(path):
    sys.path.insert(0, path)
    try:
        yield
    finally:
        sys.path.remove(path)


def get_hash_type(hashstr):
    '''
    Gets the hash type of the specified string

    :param hashstr: The string to check
    :type hashstr: str
    :returns: The type of
    :rtype: bool
    '''
    hash_type = None

    hashdict = [
        {'pattern': r'^[a-fA-F0-9]{32}$', 'type': 'MD5'},
        {'pattern': r'^[a-fA-F0-9]{16}$', 'type': 'MySQL'},
        {'pattern': r'^\*[a-fA-F0-9]{40}$', 'type': 'MySQL5'},
        {'pattern': r'^[a-fA-F0-9]{40}$', 'type': 'SHA1'},
        {'pattern': r'^[a-fA-F0-9]{56}$', 'type': 'SHA224'},
        {'pattern': r'^[a-fA-F0-9]{64}$', 'type': 'SHA256'},
        {'pattern': r'^[a-fA-F0-9]{96}$', 'type': 'SHA384'},
        {'pattern': r'^[a-fA-F0-9]{128}$', 'type': 'SHA512'},
        {'pattern': r'^\$[PH]{1}\$.{31}$', 'type': 'phpass'},
        {'pattern': r'^\$2[ya]?\$.{56}$', 'type': 'bcrypt'},
    ]

    # Check String
    for hashitem in hashdict:
        if re.match(hashitem['pattern'], hashstr):
            hash_type = hashitem['type']
    return hash_type

def is_writeable(path):
    '''
    Checks if the specified file is writeable

    :param path: The file to check
    :returns: True if the file is writeable, False otherwise
    :rtype: bool
    '''
    try:
        fp = open(path, 'a')
        fp.close()
        return True
    except IOError:
        return False

def get_user_home_path():
    '''
    Gets the path to the user's home directory

    :return: The path to the user's home directory
    :rtype: str
    '''
    return os.path.expanduser("~")

def print_http_request(request, console):
    '''
    Debug Function: Displays debug information about the specified HTTP request

    :param request: The request object
    :type request: PreparedRequest
    :param console: The current console output instance
    :type console: ConsoleOutput
    '''
    console.debug(f"{'=' * 25} REQUEST {'=' * 25}")

    # Display configured URL
    print(f"url:    {request.url}")

    # Display HTTP Method
    print(f"method: {request.method} {request.path_url}")

    # Display Headers
    for k, v in request.headers.items():
        print(f"header: {k}: {v}")

    # Display Body
    if request.body:
        print(f"body: {request.body}")

def print_http_response(response, console):
    '''
    Debug Function: Displays debug information about the specified HTTP response

    :param response: The response object
    :type response: Response
    :param console: The current console output instance
    :type console: ConsoleOutput
    '''
    console.debug(f"{'=' * 25} RESPONSE {'=' * 25}")

    # Display Status
    print(f"status: {response.status_code} {response.reason}")

    # Display Response Headers
    for k, v in response.headers.items():
        print(f"header: {k}: {v}")

    # Display Content
    if response.content:
        print(f"body:   {response.content}")

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
    domains = []

    # Iterate hosts
    for host in hosts:
        elements = host.split('.')

        # Recursively walk through the elements, extracting all possible (sub)domains
        while len(elements) >= 2:
            # account for domains stored as hosts
            if len(elements) == 2:
                domain = '.'.join(elements)
            else:
                # Drop the host element
                domain = '.'.join(elements[1:])

            # Apply any exclusions
            if domain not in domains + exclusions:
                domains.append(domain)
            del elements[0]

    return domains

def cidr_to_list(string):
    '''
    Expands the provided CIDR string to a range of IP Addresses

    :param string: The CIDR string to expand
    :type string: str
    :return: A list of IP Addresses
    :rtype: list
    '''
    return [str(ip) for ip in ipaddress.ip_network(string)]


def execute_shell_command(command):
    '''
    Executes a shell command
    '''
    # Execute Command
    proc = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE
    )

    # Process Outputs
    stdout = proc.stdout.read()
    stderr = proc.stderr.read()

    return stdout, stderr

def get_version_number(path):
    '''
    Parses and returns the Recon-NGX version number from the specified version file path

    :param path: The path to the version file
    :type path: str
    '''

    # Parse Version File
    with open(path, "r") as version_file:
        for line in version_file.readlines():
            if line.startswith("version"):
                version = line.split("=")[1].rstrip().strip()

    # Validate
    if not version:
        raise ValueError("Could not parse Recon-NGX version file.")

    return version


# 7-bit C1 ANSI sequences
def ansi_clean(text):
    '''
    Cleans the provided text of any ANSI sequences

    :param text: The text to clean
    :type text: str
    :returns: The original text, with any ANSI sequences removed
    :rtype: str
    '''
    ansi_escape = re.compile(r'''
        \x1B  # ESC
        (?:   # 7-bit C1 Fe (except CSI)
            [@-Z\\-_]
        |     # or [ for CSI, followed by a control sequence
            \[
            [0-?]*  # Parameter bytes
            [ -/]*  # Intermediate bytes
            [@-~]   # Final byte
        )
    ''', re.VERBOSE)
    result = ansi_escape.sub('', text)
    result = result.replace("\x01", "").replace("\x02", "")
    return result

def find_directory_files(path, excluded_dirs=None):
    '''
    Traverses the specified directory and builds a flat list of contained files.

    :param path: The path to the target directory
    :type path: str
    :param excluded_dirs: An optional list of directories to exclude and ignore
    :type: excluded_dirs: list, optional
    :returns: A flat list of contained files
    :rtype: bool
    '''
    files = []

    # Traverse path and find files
    for dirpath, dirnames, filenames in os.walk(path, followlinks=True):
        # Check for Directory exclusions
        dirname = os.path.split(dirpath)[-1]
        if excluded_dirs and dirname in excluded_dirs:
            continue

        for filename in [f for f in filenames]:
            abs_path = os.path.join(dirpath, filename)
            files.append(os.path.relpath(abs_path, path))

    return files

def is_python_package(path):
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

def load_module_meta(path):
    '''
    Loads a Module's metadata

    :param path: The path of the Module's package
    :type path: str
    :returns: The module's ModuleMetadata object
    :rtype: ModuleMetadata
    '''

    # Get Module spec
    spec = importlib.util.spec_from_file_location(
        "meta",
        "%s/meta.py" % path,
        submodule_search_locations=[path]
    )

    # Import meta module
    meta_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = meta_module
    spec.loader.exec_module(meta_module)

    return meta_module.meta

def load_package_module(name, path):
    '''
    Loads a package-based module

    :param name: The name of the module being loaded
    :type name: str
    :param path: The path of the module package
    :type path: str
    :returns The loaded Module class
    :rtype: BaseModule
    '''

    # Get Module spec
    spec = importlib.util.spec_from_file_location(
        name,
        "%s/module.py" % path,
        submodule_search_locations=[path]
    )

    # Import module from spec
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module

    # Create Module Instance
    spec.loader.exec_module(module)

    # Load module Metadata
    meta = load_module_meta(path)
    module.Module.meta = meta

    return module



def get_user_agents():
    '''
    Gets the available User-Agent options from the UserAgents file

    :returns: List of available User-Agents
    :rtype: list[dict]
    '''
    useragents = []

    # Build Paths
    root_path = os.path.join(Path(__file__).parent.parent.parent.parent, "recon-ngx")
    path = os.path.join(root_path, "recon", "data", "useragents.json")
    version_path = os.path.join(root_path, "VERSION")

    # Read User Agents file
    with open(path, "r") as useragents_file:
        useragents = json.loads(useragents_file.read())

    # Adjust Recon-NGX Agent
    version_number = get_version_number(version_path)
    useragents[-1]["agent_string"] = useragents[-1]["agent_string"].replace("<version>", version_number)
    useragents[-1]["summary"] = useragents[-1]["summary"].replace("<version>", version_number)

    return useragents


# =====================================================================================
# Testbed
# =====================================================================================
if __name__ == "__main__":
    # Load package-based module and get back its class
    root_path = os.path.join(Path(__file__).parent.parent.parent.parent.parent, "recon-ngx-main", "recon-ngx")
    package_mod_path = os.path.join(root_path, "test/modules_dev/modules/recon/domains-hosts/shodan_hostname")
    module = load_package_module("shodan_hostname", package_mod_path)
    print(dir(module))


