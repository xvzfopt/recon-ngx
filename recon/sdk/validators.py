"""
Recon-NGX - Module SDK - Validator Functions
================================
Contains Validator functions for validating module option values
"""
import os.path

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
    def __init__(self, recon=None, module=None):
        '''
        Constructor

        :param recon: The Recon-NGX app instance, if available
        :type recon: ReconNGXApp
        :param module: If validation is being performed for a Module, this should be the Module for which the validation
            is being performed
        :type module: BaseModule, Optional
        '''
        self._error = None
        self._recon = recon
        self._module = module

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
# HTTP Protocol Validator Class
# =====================================================================================
class ProtocolHTTPValidator(AbsValidator):
    '''
    HTTPS Protocol Validator. Validates that the supplied data is a valid HTTP protocol
    '''

    # =====================================================================================
    # Functions
    # =====================================================================================
    def validate(self, value):
        '''
        Checks if the specified value is a valid HTTP protocol

        :param value: The value to check
        :type value: str
        :returns: True if value is a HTTP protocol value, otherwise False
        :rtype
        '''

        # Check for Boolean types
        if isinstance(value, str):
            if value.lower().strip() in ["http", "https"]:
                return True

        self._error = "Not a valid HTTP protocol (HTTP/HTTPS)"
        return False

# =====================================================================================
# Boolean Value Validator
# =====================================================================================
class BooleanValidator(AbsValidator):
    '''
    Boolean Validator. Validates that the supplied data is a boolean value
    '''

    # =====================================================================================
    # Functions
    # =====================================================================================
    def validate(self, value):
        '''
        Checks if the specified value is a valid boolean value

        :param value: The value to check
        :type value: str
        :returns: True if value is a boolean value, otherwise False
        :rtype
        '''

        # Check for Boolean types
        if isinstance(value, bool):
            return True

        # Try to coerce value
        if isinstance(value, str):
            if value.lower().strip() == "true":
                return True
            elif value.lower().strip() == "false":
                return True

        self._error = "Not a valid boolean value"
        return False

# =====================================================================================
# Integer Validator Class
# =====================================================================================
class IntegerValidator(AbsValidator):
    '''
    Integer Validator. Validates that the supplied data is an integer value
    '''

    # =====================================================================================
    # Functions
    # =====================================================================================
    def validate(self, data):
        '''
        Checks if the specified data is an integer

        :param data: The data to check
        :type data: str
        :returns: True if data is an integer, otherwise False
        :rtype: bool
        '''

        # Test Data Type
        if not isinstance(data, int):
            self._error = "Not an integer"
            return False

        return True


# =====================================================================================
# Number Validator Class
# =====================================================================================
class NumberValidator(AbsValidator):
    '''
    Number Validator. Validates that the supplied data is a number
    '''

    # =====================================================================================
    # Functions
    # =====================================================================================
    def validate(self, data):
        '''
        Checks if the specified data is a number

        :param data: The data to check
        :type data: str
        :returns: True if data is a number, otherwise False
        :rtype: bool
        '''

        # Test Data Type
        if not isinstance(data, int) and not isinstance(data, float):
            self._error = "Not a number"
            return False

        return True

# =====================================================================================
# Valid File Validator Class
# =====================================================================================
class ValidFileValidator(AbsValidator):
    '''
    Valid File Validator. Validates that the supplied path leads to a valid file
    '''

    # =====================================================================================
    # Functions
    # =====================================================================================
    def validate(self, path):
        '''
        Checks if the specified path points to a valid file. Checks the following:
            1. Absolute path
            2. Data directory relative path
            3. Relative path

        :param path: The data to check
        :type path: str
        :returns: True if path points to a valid file, otherwise False
        :rtype
        '''

        # Check: Absolute Path
        if path.startswith("/") and os.path.isfile(path):
            return True
        else:
            # Check: Module Relative Path and Standard Relative Path
            if self._module:
                rel_path = os.path.join(self._module.get_package_path(), path)
                if os.path.isfile(rel_path):
                    return True
            if os.path.isfile(path):
                return True

        self._error = "The specified path does not point to a valid, existing file"
        return False

# =====================================================================================
# Port Number Validator Class
# =====================================================================================
class PortNumberValidator(AbsValidator):
    '''
    Port Number Validator. Validates that the supplied data is a valid port number
    '''

    # =====================================================================================
    # Functions
    # =====================================================================================
    def validate(self, data):
        '''
        Checks if the specified data is a valid port number

        :param data: The data to check
        :type data: str
        :returns: True if data is a valid port number, otherwise False
        :rtype: bool
        '''
        self._error = "Not a valid port number"

        # Test Data Type
        try:
            data = int(data)
        except ValueError:
            return False

        # Check range
        if data > 0 and data <= 65535:
            return True

        return False

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
    def validate(self, data):
        '''
        Checks if the specified data is a valid IPv4 address

        :param data: The data to check
        :type data: str
        :returns: True if data is a valid IPv4 address, otherwise False
        :rtype
        '''
        self._error = "Not a valid IPv4 Address"

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