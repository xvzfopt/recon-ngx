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

def html_escape(s):
    '''
    Escapes HTML characters in the specified content

    :param s: The string to escape
    :type s: str
    :return: The escaped string
    :rtype: str
    '''
    escapes = {
        '&': '&amp;',
        '"': '&quot;',
        "'": '&apos;',
        '>': '&gt;',
        '<': '&lt;',
    }
    return ''.join(escapes.get(c,c) for c in s)

def html_unescape(s):
    '''
    Unescapes HTML markup and returns an unescaped string.

    :param s: The string to unescape
    :type s: str
    :return: The unescaped string
    :rtype: str
    '''
    return html.unescape(s)

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
    return result

def load_file_module(name, path):
    '''
    Loaded the module at the specified path

    :param path: The path to the module .py file
    :type path: str
    :returns: The loaded module class
    :rtype: Module # TODO
    '''


    # Load Module spec file
    spec = importlib.util.spec_from_file_location(name, path)

    # Import module from spec
    module = importlib.util.module_from_spec(spec)

    # Create Module Instance
    spec.loader.exec_module(module)

    return module

