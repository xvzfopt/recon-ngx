# =====================================================================================
# Imports: External
# =====================================================================================
import re
import traceback
import os
import sys

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.utils import utils
from . import colors
from .banner import *
from recon.core.exceptions import *

# =====================================================================================
# Console Output Class
# =====================================================================================
class ConsoleOutput:
    '''
    Console Output. Facilitates console output functionality
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================
    RULER   = '-'
    SPACER  = '  '
    NAME    = "Recon-NGX"

    # =====================================================================================
    # Colours
    # =====================================================================================
    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, options, accessible):
        '''
        Constructor.

        :param options: Global options object
        :type options: Options
        '''
        self._console_handler = None
        self._spool_dest = None
        self._stdout = sys.stdout

        self._accessible = accessible
        self._global_options = options

        # Keep track of all console output for future checking/tests
        self.__output = []

    def write(self, line, end="\n", suppress=False):
        '''
        Main Console write function. Provides Cmd class with a stdout abstraction layer so that we can handle
        spooling

        :param line: The line to write/print
        :type line: str
        :param end: Optional line delimiter override. Defaults to newline (\n)
        :type end: str, optional
        :param suppress: Suppresses output from actually being printed to the console. This is used in cases where
            output should be logged or written to a spool file, but not printed because that is being handled elsewhere
            e.g. when the ProgressBar is being used
        '''
        # Append line delimiter if not present
        if not line.endswith(end):
            line += end

        # Write to stdout
        if not suppress:
            self._stdout.write(line)

        # Record to log for later usage
        self.__output.append(utils.ansi_clean(line))

        # Spool to file
        if self._spool_dest:
            self.spool_to_file(line)

    # =====================================================================================
    # Spooling Functions
    # =====================================================================================
    def spool_to_file(self, line):
        with open(self._spool_dest, "a") as spool_file:
            spool_file.write(line)

    def enable_spooling(self, path):
        '''
        Sets up output spooling to the specified file

        :param path: The path to the spool file
        :type path: str
        '''

        # Clear File
        open(path, "w").close()
        self._spool_dest = path

    def disable_spooling(self):
        '''
        Disables file spooling
        '''
        if self._spool_dest:
            self._spool_dest = None

    def is_spooling(self):
        '''
        Checks if output and input are currently being spooled to a file

        :returns:True if output and input are being spooled to a file
        :rtype: bool
        '''
        return self._spool_dest is not None

    def get_spool_file_path(self):
        '''
        Gets the path to the target spool file

        :returns: The path to the target spool file
        :rtype: str
        '''
        return self._spool_dest

    # =====================================================================================
    # General Output functions
    # =====================================================================================
    def print_banner(self, version, author, loaded_categories):
        '''
        Prints the recon-ngx application Banner

        :param version: The recon-ngx version number
        :type version: str
        :param author: The recon-ngx author name
        :type author: str
        :param loaded_categories: The currently loaded categories
        :type loaded_categories: dict<str:list>
        '''

        # Build Output --> Accessible
        author_block = ""
        if self._accessible:
            banner = BANNER_SMALL
            author_block += f"{colors.COLOR_O}{self.NAME}, version {version}, by {author}{colors.COLOR_N}"
        # Build Output --> Standard
        else:
            banner = BANNER_DEFAULT
            banner_len = len(max(banner.split(os.linesep), key=len))
            divider_string      = '{0:^{1}}'.format(f"{colors.COLOR_O}============================{colors.COLOR_N}", banner_len + 8)
            rngx_author_string  = '{0:^{1}}'.format(f"{colors.COLOR_O}[{self.NAME} v{version}, {author}]{colors.COLOR_N}", banner_len + 8)
            derivation_string   = '{0:^{1}}'.format(f"{colors.COLOR_O}Derived from{colors.COLOR_N}", banner_len + 8)
            rng_author_string   = '{0:^{1}}'.format(f"{colors.COLOR_O}[recon-ng v5.1.2, Tim Tomes (@lanmaster53)]{colors.COLOR_N}", banner_len + 8)

            # Build Author Block
            author_block += rngx_author_string + "\n"
            author_block += divider_string + "\n"
            author_block += derivation_string + "\n"
            author_block += divider_string + "\n"
            author_block += rng_author_string + "\n"

        # Print Banner & Author Block
        self.write(banner)
        self.write(author_block)
        self.write('')

        # Get Total Module Count
        max_count = 0
        for category in loaded_categories:
            module_count = len(loaded_categories[category])
            if module_count > max_count:
                max_count = module_count

        # Print Module Count by Category
        for category in loaded_categories:
            module_count = len(loaded_categories[category])
            cnt = f"[{module_count}]"
            self.write(f"{colors.COLOR_B}{cnt.ljust(max_count + 1)} {category.capitalize()} modules{colors.COLOR_N}")
        self.write('')

    def print_exception(self, line=''):
        '''
        Prints a caught exception

        :param line: Additional information to print alongside the exception. Optional
        :type line: str
        '''

        # Process Exception
        stack_list = [x.strip() for x in traceback.format_exc().strip().splitlines()]
        exctype = stack_list[-1].split(':', 1)[0].strip()
        message = stack_list[-1].split(':', 1)[-1].strip()

        # Verbosity 0: Suppress
        if self._global_options['verbosity'] == 0:
            return
        # Verbosity 1: Print included info
        elif self._global_options['verbosity'] == 1:
            line = ' '.join([x for x in [message, line] if x])
            self.error(line)
        # Verbosity 2: Print Stack Trace
        elif self._global_options['verbosity'] == 2:
            self.write(f"{colors.COLOR_R}{'-'*60}")
            traceback.print_exc()
            self.write(f"{'-'*60}{colors.COLOR_N}")

    def error(self, line):
        '''
        Formats and prints an Error

        :param line: The Error message/data to print
        :type line: str
        '''
        if not re.search('[.,;!?]$', line):
            line += '.'
        line = line[:1].upper() + line[1:]
        self.write(f"{colors.COLOR_R}[!] {line}{colors.COLOR_N}")

    def output(self, line):
        '''
        Formats and prints normal output

        :param line: The message/data to print
        :type line: str
        '''
        self.write(f"{colors.COLOR_B}[*]{colors.COLOR_N} {line}")
        pass

    def code_line(self, line):
        '''
        Formats and prints normal output

        :param line: The message/data to print
        :type line: str
        '''
        self.write(f"{colors.COLOR_R}[>]{colors.COLOR_N} {line}")
        pass

    def alert(self, line):
        '''
        Formats and prints important output

        :param line: The message/data to print
        :type line: str
        '''
        self.write(f"{colors.COLOR_G_BOLD}[*]{colors.COLOR_N} {line}")

    def verbose(self, line):
        '''
        Formats and prints output if in verbose mode

        :param line: The message/data to print
        :type line: str
        '''
        if self._global_options['verbosity'] >= 1:
            self.output(line)

    def debug(self, line):
        '''
        Formats and prints output if in debug mode

        :param line: The message/data to print
        :type line: str
        '''
        if self._global_options['verbosity'] >= 2:
            self.output(line)

    def heading(self, line, level=1):
        '''
        Formats and prints a styled header

        :param line: The header/title to print
        :type line: str
        :param level: The header/title indentation level
        '''
        line = line
        self.write('')

        # Indentation Level: 0
        if level == 0:
            self.write(self.RULER * len(line))
            self.write(line.upper())
            self.write(self.RULER * len(line))
        # Indentation Level: 1
        if level == 1:
            self.write(f"{self.SPACER}{line.title()}")
            self.write(f"{self.SPACER}{self.RULER * len(line)}")

    def table(self, data, header=[], title=''):
        '''
        Formats and prints a table

        :param data: The rows to print
        :type data: list
        :param header: Table Header row (Optional)
        :type header: list, optional
        :param title: The table's title (Optional)
        :type title: str
        '''
        tdata = list(data)

        # Add Table Header row
        if header:
            tdata.insert(0, header)

        # Check row lengths are consistent
        if len(set([len(x) for x in tdata])) > 1:
            raise ReconNGXException('Row lengths not consistent.')

        cols_count = len(tdata[0])

        # Create a list of max widths for each column
        col_lengths = []
        for i in range(0,cols_count):
            col_lengths.append(len(max([utils.to_unicode_str(x[i]) if x[i] != None else '' for x in tdata], key=len)))

        # Calculate dynamic widths based on the title, if required
        title_len = len(title)
        tdata_len = sum(col_lengths) + (3*(cols_count-1))
        diff = title_len - tdata_len
        if diff > 0:
            diff_per = diff / cols_count
            col_lengths = [x+diff_per for x in col_lengths]
            diff_mod = diff % cols_count
            for x in range(0, diff_mod):
                col_lengths[x] += 1

        # Build Table
        if len(tdata) > 0:
            # Build & Print table separator (Acts like a border, or divider)
            separator_str = f"{self.SPACER}+-{'%s---'*(cols_count-1)}%s-+"
            separator_sub = tuple(['-'*x for x in col_lengths])
            separator = separator_str % separator_sub
            data_str = f"{self.SPACER}| {'%s | '*(cols_count-1)}%s |"

            # Print Top of ascii table
            self.write('')
            self.write(separator)

            # Print Table Title
            if title:
                self.write(f"{self.SPACER}| {title.center(tdata_len)} |")
                self.write(separator)

            # Print Table Header
            if header:
                rdata = tdata.pop(0)
                data_sub = tuple([rdata[i].center(col_lengths[i]) for i in range(0,cols_count)])
                self.write(data_str % data_sub)
                self.write(separator)

            # Print Table Row Data
            for rdata in tdata:
                data_sub = tuple([utils.to_unicode_str(rdata[i]).ljust(col_lengths[i]) if rdata[i] != None else ''.ljust(col_lengths[i]) for i in range(0,cols_count)])
                self.write(data_str % data_sub)

            # Print bottom of ascii table
            self.write(separator)
            self.write('')

    # =====================================================================================
    # Getters
    # =====================================================================================
    def get_output(self):
        '''
        Returns all output lines that the console has logged so far in the current session

        :return: The console's output so far
        :rtype: list
        '''
        return self.__output

    # =====================================================================================
    # Setters
    # =====================================================================================
    def set_accessibility(self, accessible):
        '''
        Turns the accessibility mode on/off

        :param accessible: True or False
        :type accessible: bool
        '''
        self._accessible = accessible