"""
Recon-NGX - Module SDK - utils
================================
Contains a collection of utility function and helpers that Module developers can use
"""

# =====================================================================================
# Imports: External
# =====================================================================================
import gzip
import re
import unicodedata
from io import BytesIO

# =====================================================================================
# Imports: Internal
# =====================================================================================
def decompress_gz(data):
    '''
    Decompresses a a gzipped data stream

    :param data: The gzipped data to decompress
    :type: str
    :returns: The decompressed data
    :rtype: bytes
    '''
    compressed_data = BytesIO(data.encode())
    decompressed_data = ''

    # Attempt Decompression
    f = gzip.GzipFile(mode='rb', fileobj=compressed_data)
    try:
        data_ct = f.read()
    except IOError:
        pass

    f.close()
    return decompressed_data

def clean_unicode_characters(value):
    '''
    Removes Unicode control characters from the provided string

    :param value: The string to remove Unicode characters from
    :type value: str
    :returns: The cleaned value
    :rtype: str
    '''
    return "".join(char for char in value if unicodedata.category(char) != "Cf")

def parse_fullname(fullname):
    '''
    Parses a person's full-name into its components (first, middle and last name)

    :param fullname: The full name to parse
    :type fullname: str
    :returns: The person's first, middle and last names. Any or all of these components will be None if that component
        could not be processed, or was not present
    :rtype: tuple
    '''
    elements = fullname.strip().split(" ")
    names = []

    # Process name elements
    for i in range(0,len(elements)):
        # Process initials
        if re.search(r'^\w\.$', elements[i]):
            elements[i] = elements[i][:-1]

        # remove unnecessary prefixes and suffixes
        elif re.search(r'(?:\.|^the$|^jr$|^sr$|^I{2,3}$)', elements[i], re.IGNORECASE):
            continue

        names.append(elements[i])

    # Clean up any remaining garbage characters
    names = [re.sub(r"[,']", '', x) for x in names]

    # Set final values
    fname = names[0] if len(names) >= 1 else None
    mname = " ".join(names[1:-1]) if len(names) >= 3 else None
    lname = names[-1] if len(names) >= 2 else None

    return fname, mname, lname