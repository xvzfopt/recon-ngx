# =====================================================================================
# Imports: External
# =====================================================================================
import os.path
import shutil
from unittest import TestCase

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.core.options import Options

# =====================================================================================
# Base Test Case Class
# =====================================================================================
class AbsTestCase(TestCase):
    '''
    Base Test Case. Not to be instantiated directly.
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    TMP_PATH    = os.path.join(os.path.dirname(__file__), "tmp")
    HOME_PATH   = os.path.join(TMP_PATH, "home")

    # =====================================================================================
    # Methods
    # =====================================================================================
    def setUp(self):
        '''
        Base Test Case setUp Method
        '''
        super(AbsTestCase, self).setUp()

        # Get Recon-NGX version
        self._version = self.get_version()

        # Set up test home dir
        if os.path.isdir(self.HOME_PATH):
            shutil.rmtree(self.HOME_PATH)
        os.makedirs(self.HOME_PATH)

        # Set up Global Options
        self._options = Options()
        self._options.initialise_global_options(self._version)

    def tearDown(self):
        '''
        Base Test Case tearDown Method
        '''
        super(AbsTestCase, self).setUp()

    # =====================================================================================
    # Custom Assertions
    # =====================================================================================
    def assertLength(self, length, container):
        '''
        Checks that the provided container has the expected length.

        :param length: Expected length
        :type length: int
        :param container: The container to check
        :type container: list
        '''
        self.assertEqual(len(container), length, "Container is not of expected length.")

    def assertEmpty(self, container):
        '''
        Checks that the provided container is empty.

        :param container: The container to check
        :type container: list
        '''
        self.assertEqual(len(container), 0, "Container is not empty.")

    # =====================================================================================
    # Helpers
    # =====================================================================================
    def get_version(self):
        '''
        Reads the version file and parses the version number

        :returns: The recon-ngx version number
        :rtype: str
        '''
        version = None

        # Parse Version File
        project_dir = os.path.dirname(os.path.dirname(__file__))
        path = os.path.join(project_dir, 'VERSION')
        with open(path, "r") as version_file:
            for line in version_file.readlines():
                if line.startswith("version"):
                    version = line.split("=")[1].rstrip().strip()

        # Validate
        if not version:
            raise ValueError("Could not parse Recon-NGX version file.")

        return version


