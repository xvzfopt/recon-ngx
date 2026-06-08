# =====================================================================================
# Imports: External
# =====================================================================================
from tqdm import tqdm

# =====================================================================================
# Progress Bar Class
# =====================================================================================
class ProgressBar:
    '''
    Recon-NGX Progress Bar
    '''

    def __init__(self, console, total, description="", unit="item", enabled=True):
        '''
        Constructor

        :param console: The Console Output instance
        :type console: ConsoleOutput
        :param total: The total number of items that are being iterated. Used as the Progress Bar's % scale
        :type total: int
        :param description An optional description for the progress bar. Not specified by default
        :type description: str, optional
        :param enabled: Whether the progress bar is enabled. Defaults to True
        :type enabled: bool, optional
        '''
        self._console = console
        self._total = total
        self._unit = unit
        self._description = description
        self._enabled = enabled
        self._bar = None

    def __enter__(self):
        '''
        "with" enter method. Sets up the Progress Bar
        '''
        if self._enabled:
            self._bar = tqdm(
                total=self._total,
                desc=self._description,
                unit=f" {self._unit}",
                dynamic_ncols=True,
                leave=True,
            )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        '''
        "with" exit method. Shuts down the Progress Bar
        '''
        if self._bar:
            self._bar.close()

    def update(self, amount = 1):
        '''
        Updates the progress bar. To be called when an iteration has completed

        :param amount: The amount of progress/iterations/tasks that have been completed. This is relative to the "total"
        :type amount: int
        '''
        if self._bar:
            self._bar.update(amount)

    def write(self, message):
        '''
        Writes a message to the console for displaying additional information to the user

        :param message: The message to be displayed
        :type message: str
        '''
        self._console.write(message, suppress=True)
        if self._bar:
            self._bar.write(message)

    def set_status(self, message):
        '''
        Sets a status message for the progress bar, to be displayed alongside it. It's recommended to keep these
        quite short.

        :param message: The status message to be displayed
        :type message: str
        '''
        if self._bar:
            self._bar.set_postfix_str(message)