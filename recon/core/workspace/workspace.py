# =====================================================================================
# Imports: External
# =====================================================================================
import os

# =====================================================================================
# Imports: Internal
# =====================================================================================

# =====================================================================================
# Workspace Class
# =====================================================================================
class Workspace:
    '''
    recon-ngx Workspace
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================


    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, name, path, db):
        '''
        Constructor

        :param name: workspace name
        :type name: str
        :param path: Path to the workspace
        :type path: str
        :param db: The database instance for this workspace
        :type db: WorkspaceDB
        '''
        self._name = name
        self._path = path
        self._db = db

    def get_name(self):
        '''
        Gets the workspace name

        :return: the name of this workspace
        :rtype: str
        '''
        return self._name

    def get_path(self):
        '''
        Gets the path to the workspace directory

        :return: the path to the workspace directory
        :rtype: str
        '''
        return self._path

    def get_db_path(self):
        '''
        Gets the path to the Workspace's Database

        :return: the path to the Workspace's Database
        :rtype: str
        '''
        return self._db.get_path()