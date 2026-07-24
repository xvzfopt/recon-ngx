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
    
# =====================================================================================
# Module Download Failure Exception
# =====================================================================================
class ModuleDownloadFailure(ReconNGXException):
    '''
    Raised when a module fails to download from the Module Marketplace
    '''

# =====================================================================================
# Module Dependency Installation Failure
# =====================================================================================
class DependencyInstallationFailure(ReconNGXException):
    '''
    Raised when a Module dependency fails to install
    '''

    def __init__(self, requirement):
        super(DependencyInstallationFailure, self).__init__(
            "Dependency installation failed for requirement '%s'. Install this dependency manually and attempt module "
            "installation again. For more details, Run Recon-NGX in verbose mode." % requirement
        )

# =====================================================================================
# Module Dependency Uninstallation Failure
# =====================================================================================
class DependencyUninstallationFailure(ReconNGXException):
    '''
    Raised when a Module dependency fails to uninstall
    '''

    def __init__(self, package):
        super(DependencyUninstallationFailure, self).__init__(
            "Dependency uninstallation failed for package '%s'. Uninstall this dependency manually and attempt "
            "module uninstallation again. For more details, Run Recon-NGX in verbose mode." % package
        )
