'''
# Recon-NGX SDK - Exception Classes
'''

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.core.exceptions import ReconNGXException

# =====================================================================================
# Module Validation Exception
# =====================================================================================
class ModuleValidationException(ReconNGXException):
    '''
    To be raised when a module fails to validate
    '''

# =====================================================================================
# Module Runtime Exception
# =====================================================================================
class ModuleRuntimeException(ReconNGXException):
    '''
    To be raised in the event of a general Module runtime failure, error, or exception
    '''