# =====================================================================================
# Imports: External
# =====================================================================================

# =====================================================================================
# Imports: Internal
# =====================================================================================
from .base import BaseInterpreter

# =====================================================================================
# Module Interpreter Class
# =====================================================================================
class ModuleInterpreter(BaseInterpreter):
    '''
    Module Command Interpreter for use in Module context/mode
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, recon, console, module):
        '''
        Constructor
        '''
        '''
        Constructor

        :param recon: The ReconNGX App instance
        :type recon: ReconNGXApp
        :param console: The console output instance
        :type console: ConsoleOutput
        :param module: The Module instance
        :type module: BaseModule
        '''
        super(ModuleInterpreter, self).__init__(recon, console)
        self._module = module
        self._workspace = self._recon.get_current_workspace()
        self.prompt = "%s[%s][%s] " % (self._base_prompt, self._workspace.get_name(), module.get_name())


    def start(self):
        '''
        Start the Module Interpreter

        :note: Overrides base start to avoid banner print
        '''
        self.cmdloop()
