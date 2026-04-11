# =====================================================================================
# Imports: External
# =====================================================================================
import random
import string
import json
import os

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
