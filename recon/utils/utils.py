# =====================================================================================
# Imports: External
# =====================================================================================
import random
import string
import json
import os
import sys
import re
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


def is_hash(hashstr):
    '''
    Checks if the specified string is a valid hash

    :param hashstr: The string to check
    :type hashstr: str
    :returns: True if the string is a valid hash, False otherwise
    :rtype: bool
    '''
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
            return hashitem['type']
    return False

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
