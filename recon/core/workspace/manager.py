# =====================================================================================
# Imports: External
# =====================================================================================
import os
import shutil

# =====================================================================================
# Imports: Internal
# =====================================================================================
from .workspace import Workspace
from .db import WorkspaceDB

# =====================================================================================
# Workspace Manager Class
# =====================================================================================
class WorkspaceManager:
    '''
    recon-ngx Workspace Manager
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, spaces_path, output):
        '''
        Constructor

        :param spaces_path: Path to the workspaces folder
        :type spaces_path: str
        '''
        self._spaces_path = spaces_path
        self._output = output

    def create_workspace(self, name):
        '''
        Creates and initialises a new workspace

        :param name: Name of the workspace to create
        :type name: str
        :returns: The new Workspace instance
        :rtype: Workspace
        '''

        # Set up Directories
        wpath = os.path.join(self._spaces_path, name)
        os.makedirs(wpath)

        # Initialise Database
        db = WorkspaceDB(os.path.join(wpath, "data.db"), self._output)

        # Initialise Workspace
        workspace = Workspace(name, wpath, db)

        return workspace

    def remove_workspace(self, name):
        '''
        Removes the target workspaces

        :param name: Name of the workspace to remove
        :type name: str
        :returns: True if the workspace was removed, otherwise False
        :rtype: bool
        '''
        w = self.get_workspace(name)
        try:
            shutil.rmtree(w.get_path())
        except OSError:
            return False
        return True

    def get_workspace(self, name):
        '''
        Gets the Workspace instance for the specified workspace name

        :param name: Name of the workspace to get
        :type name: str
        :returns: The Workspace instance
        :rtype: Workspace
        '''
        wpath = os.path.join(self._spaces_path, name)

        # Initialise Database
        db = WorkspaceDB(os.path.join(wpath, "data.db"), self._output)

        # Initialise Workspace
        workspace = Workspace(name, wpath, db)

        return workspace

    def get_workspaces(self):
        '''
        Gets all available workspaces

        :returns: List of Workspace instances
        :rtype: list<Workspace>
        '''
        workspaces = []
        for name in os.listdir(self._spaces_path):
            path = os.path.join(self._spaces_path, name)
            if os.path.isdir(path):
                workspaces.append(self.get_workspace(name))
        return workspaces

    def workspace_exists(self, name):
        '''
        Checks if a Workspace with the specified name exists

        :param name: Name of the workspace to check
        :type name: str
        '''
        path = os.path.join(self._spaces_path, name)
        return os.path.isdir(path)
