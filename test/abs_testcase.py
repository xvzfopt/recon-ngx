# =====================================================================================
# Imports: External
# =====================================================================================
from unittest import TestCase

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

    # =====================================================================================
    # Methods
    # =====================================================================================
    def setUp(self):
        '''
        Base Test Case setUp Method
        '''
        super(AbsTestCase, self).setUp()

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
        self.assertEqual(len(container), length)

