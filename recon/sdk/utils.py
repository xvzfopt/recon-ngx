"""
Recon-NGX - Module SDK - utils
================================
Contains a collection of utility function and helpers that Module developers can use
"""

# =====================================================================================
# Imports: External
# =====================================================================================
import gzip
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

