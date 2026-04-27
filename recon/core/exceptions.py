# =====================================================================================
# Base Recon-NGX Exeception
# =====================================================================================
class ReconNGXException(Exception):
    '''
    Base Recon-NGX Exception
    '''

# =====================================================================================
# Validation Exception
# =====================================================================================
class ValidationException(ReconNGXException):
    '''
    Validation Exception. Raised when validation fails
    '''