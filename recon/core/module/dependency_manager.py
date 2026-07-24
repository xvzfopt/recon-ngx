# =====================================================================================
# Imports: External
# =====================================================================================
import sys
import shlex
from subprocess import Popen
from subprocess import PIPE
from packaging.requirements import Requirement
from importlib.metadata import version
from importlib.metadata import PackageNotFoundError

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.core.exceptions import DependencyInstallationFailure
from recon.core.exceptions import DependencyUninstallationFailure

# =====================================================================================
# Dependency Manager Class
# =====================================================================================
class DependencyManager:
    '''
    Recon-NGX Module Dependency Manager
    '''

    def __init__(self, console):
        '''
        Constructor

        :param console: ConsoleOutput Instance
        :type console: ConsoleOutput
        '''
        self._console = console

    def is_satisfied(self, requirement):
        '''
        Checks if the specified dependency requirement is satisfied

        :param requirement: The requirement specifier to check for, such as "dnspython<=2.6.3", or "requests"
        :type requirement: str
        :returns: True if the requirement is satisfied, otherwise False
        :rtype: bool
        '''
        req = Requirement(requirement)

        try:
            installed = version(req.name)
            if installed in req.specifier:
                return True
        except PackageNotFoundError:
            pass

        return False

    def install(self, requirement):
        '''
        Installs the specified requirement

        :param requirement: The requirement specifier for the package to install, such as "dnspython<=2.6.3"
        :type requirement: str
        '''

        # Run Command
        cmd = f"{sys.executable} -m pip install %s" % requirement
        proc = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)

        # Process Output
        stdout, stderr = proc.communicate()
        self._console.debug("Installation Process RC: %s" % proc.returncode)
        self._console.debug("Installation Process stdout: %s" % stdout.decode("utf-8"))
        self._console.debug("Installation Process stderr: %s" % stderr.decode("utf-8"))

        # Check Output
        if proc.returncode != 0:
            raise DependencyInstallationFailure(requirement)

    def uninstall(self, package):
        '''
        Uninstalls the specified package

        :param package: The name of the package to uninstall
        :type package: str
        '''

        # Run Command
        cmd = f"{sys.executable} -m pip uninstall -y %s" % package
        proc = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)

        # Process Output
        stdout, stderr = proc.communicate()
        self._console.debug("Uninstallation Process RC: %s" % proc.returncode)
        self._console.debug("Uninstallation Process stdout: %s" % stdout.decode("utf-8"))
        self._console.debug("Uninstallation Process stderr: %s" % stderr.decode("utf-8"))

        # Check Output
        if proc.returncode != 0:
            raise DependencyUninstallationFailure(package)

    # =====================================================================================
    # Helpers
    # =====================================================================================
    def package_name_from_specifier(self, specifier):
        '''
        Extracts the package name from a requirement specifier string, such as "dnspython<=2.6.3"

        :param specifier: The specifier string to extract the package name from
        :type specifier: str
        :returns: The package name
        :rtype: str
        '''
        req = Requirement(specifier)
        return req.name
