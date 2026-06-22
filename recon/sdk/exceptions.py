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