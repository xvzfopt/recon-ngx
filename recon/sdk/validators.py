"""
Recon-NGX - Module SDK - Validator Functions
================================
Contains Validator functions for validating module option values
"""

# =====================================================================================
# Imports: External
# =====================================================================================

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.sdk.exceptions import ModuleValidationException

# =====================================================================================
# Validator Classes
# =====================================================================================
class AbsValidator:
    '''
    Abstract Validator Class. To be used as the base class for any validators
    '''

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self):
        '''
        Constructor
        '''
        self._error = None

    def validate(self, data):
        '''
        Performs the validation

        :param data: The data to validate`
        :type data: Any
        '''
        raise NotImplementedError("Validator classes must implement the validate() method")

    def get_error(self):
        '''
        Gets the Validator's error message

        :returns: The error message
        :rtype: str
        '''
        return self._error

# =====================================================================================
# IPv4 Address Validator
# =====================================================================================
class Ipv4AddressValidator(AbsValidator):
    '''
    IPv4 Address Validator. Validates that the supplied data is a valid IPv4 Address
    '''

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self):
        '''
        Constructor
        '''
        super(Ipv4AddressValidator, self).__init__()
        self._error = "Not a valid IPv4 Address"

    def validate(self, data):
        '''
        Checks if the specified data is a valid IPv4 address

        :param data: The data to check
        :type data: str
        :returns: True if data is a valid IPv4 address, otherwise False
        :rtype
        '''

        # Check for string
        if not isinstance(data, str):
            return False

        # Parse octets
        octets = data.split('.')

        # Check for 4 octets
        if len(octets) != 4:
            return False

        # Check octet ranges
        for octet in octets:
            try:
                octet = int(octet)
            except ValueError:
                return False

            if octet < 0 or octet > 255:
                return False

        # Success!
        return True