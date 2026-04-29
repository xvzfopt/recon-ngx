# =====================================================================================
# Imports: External
# =====================================================================================
import re
import traceback
import os

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.utils import utils
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
    NAME    = "recon-ngx"

    # =====================================================================================
    # Colours
    # =====================================================================================
    COLOR_N = '\033[m'      # native
    COLOR_R = '\033[31m'    # red
    COLOR_G = '\033[32m'    # green
    COLOR_O = '\033[33m'    # orange
    COLOR_B = '\033[34m'    # blue

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, options):
        '''
        Constructor.

        :param options: Global options object
        :type options: Options
        '''
        self._accessible = False
        self._global_options = options

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
        if self._accessible:
            banner = BANNER_SMALL
            author_string = f"{self.COLOR_O}{self.NAME}, version {version}, by {author}{self.COLOR_N}"
        # Build Output --> Standard
        else:
            banner = BANNER_DEFAULT
            banner_len = len(max(banner.split(os.linesep), key=len))
            author_string = '{0:^{1}}'.format(f"{self.COLOR_O}[{self.NAME} v{version}, {author}]{self.COLOR_N}", banner_len + 8)

        # Print Banner & Author
        print(banner)
        print(author_string)
        print('')

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
            print(f"{self.COLOR_B}{cnt.ljust(max_count + 1)} {category.capitalize()} modules{self.COLOR_N}")
        print('')

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
            print(f"{self.COLOR_R}{'-'*60}")
            traceback.print_exc()
            print(f"{'-'*60}{self.COLOR_N}")

    def error(self, line):
        '''
        Formats and prints an Error

        :param line: The Error message/data to print
        :type line: str
        '''
        if not re.search('[.,;!?]$', line):
            line += '.'
        line = line[:1].upper() + line[1:]
        print(f"{self.COLOR_R}[!] {line}{self.COLOR_N}")

    def output(self, line):
        '''
        Formats and prints normal output

        :param line: The message/data to print
        :type line: str
        '''
        print(f"{self.COLOR_B}[*]{self.COLOR_N} {line}")

    def alert(self, line):
        '''
        Formats and prints important output

        :param line: The message/data to print
        :type line: str
        '''
        print(f"{self.COLOR_G}[*]{self.COLOR_N} {line}")

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
        print('')

        # Indentation Level: 0
        if level == 0:
            print(self.RULER * len(line))
            print(line.upper())
            print(self.RULER * len(line))
        # Indentation Level: 1
        if level == 1:
            print(f"{self.SPACER}{line.title()}")
            print(f"{self.SPACER}{self.RULER * len(line)}")

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
            print('')
            print(separator)

            # Print Table Title
            if title:
                print(f"{self.SPACER}| {title.center(tdata_len)} |")
                print(separator)

            # Print Table Header
            if header:
                rdata = tdata.pop(0)
                data_sub = tuple([rdata[i].center(col_lengths[i]) for i in range(0,cols_count)])
                print(data_str % data_sub)
                print(separator)

            # Print Table Row Data
            for rdata in tdata:
                data_sub = tuple([utils.to_unicode_str(rdata[i]).ljust(col_lengths[i]) if rdata[i] != None else ''.ljust(col_lengths[i]) for i in range(0,cols_count)])
                print(data_str % data_sub)

            # Print bottom of ascii table
            print(separator)
            print('')

    def set_accessibility(self, accessible):
        '''
        Turns the accessibility mode on/off

        :param accessible: True or False
        :type accessible: bool
        '''
        self._accessible = accessible