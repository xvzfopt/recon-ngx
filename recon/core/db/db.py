# =====================================================================================
# Imports: External
# =====================================================================================
import os
import sqlite3
import inspect
from datetime import datetime
from contextlib import closing

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.utils import utils

# =====================================================================================
# Recon-NGX Database Class
# =====================================================================================
class ReconNGXDatabase:
    '''
    Recon-NGX Database
    '''
    
    # =====================================================================================
    # Properties
    # =====================================================================================
    
    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, path, console):
        '''
        Constructor

        :param path: path to database file
        :type path: str
        :param console: The Output Console instance
        :type console: ConsoleOutput
        '''
        self._path = path
        self._console = console
        self._summary_counts = {}

        # Perform DB Setup/Migration
        if not self.db_exists():
            self.create()
        else:
            self.migrate()

    def create(self):
        '''
        Creates and sets up the database
        '''
        self._create_db()

    def migrate(self):
        '''
        Performs Database migration tasks
        '''
        self._migrate_db()

    def db_exists(self):
        '''
        Checks if the Database exists

        :return: True if exists, otherwise False
        :rtype: bool
        '''
        return os.path.isfile(self._path)

    def query(self, *args, **kwargs):
        return self._query(self._path, *args, **kwargs)

    def get_path(self):
        '''
        Gets the path to the Database file

        :return: path to the database file
        :rtype: str
        '''
        return self._path

    def get_mod_time(self):
        '''
        Gets the Modification time of the Database

        :return: The Modification Time of this Database
        :rtype: str
        '''
        return datetime.fromtimestamp(
            os.path.getmtime(self._path)
        ).strftime('%Y-%m-%d %H:%M:%S')

    # =====================================================================================
    # Internal Functions
    # =====================================================================================
    def _insert(self, table, data, unique_columns=[]):
        '''
        Inserts items into database and returns the affected row count.
        recon-ngx --> Migrated across from recon-ng

        :param table: The name of the table to insert data into
        :type table: str
        :param data: The data to insert into table. This should be a dictionary of <column_name>:<value>
        :type data: dict[str:any]
        :param unique_columns: A list of columns that should be used to determine if the data being inserted is unique
        :returns: The count of affected rows
        :rtype: int
        '''
        # set module to the calling module unless the do_add command was used
        data['module'] = 'user_defined' if '_do_db_insert' in [x[3] for x in inspect.stack()] else self._modulename.split('/')[-1]

        # sanitize the inputs to remove NoneTypes, blank strings, and zeros
        columns = [x for x in data.keys() if data[x]]

        # make sure that module is not seen as a unique column
        unique_columns = [x for x in unique_columns if x in columns and x != 'module']

        # exit if there is nothing left to insert
        if not columns:
            return 0

        # convert any type to unicode (str) for external processing
        for column in columns:
            data[column] = utils.to_unicode_str(data[column])

        # build the insert query
        columns_str = '`, `'.join(columns)
        placeholder_str = ', '.join('?'*len(columns))
        unique_columns_str = ' and '.join([f"`{column}`=?" for column in unique_columns])
        if not unique_columns:
            query = f"INSERT INTO `{table}` (`{columns_str}`) VALUES ({placeholder_str})"
        else:
            query = f"INSERT INTO `{table}` (`{columns_str}`) SELECT {placeholder_str} WHERE NOT EXISTS(SELECT * FROM `{table}` WHERE {unique_columns_str})"
        values = tuple([data[column] for column in columns] + [data[column] for column in unique_columns])

        # query the database
        rowcount = self.query(query, values)

        # increment summary tracker
        if table not in self._summary_counts:
            self._summary_counts[table] = {'count': 0, 'new': 0}
        self._summary_counts[table]['new'] += rowcount
        self._summary_counts[table]['count'] += 1

        return rowcount

    def table_exists(self, table):
        '''
        Checks if the specified table exists in the database

        :param table: The name of the table to check
        :type table: str
        :return: True if exists, otherwise False
        :rtype: bool
        '''
        query = "SELECT 1 FROM sqlite_master WHERE type='table' AND name='%s';" % table
        results = self.query(query)
        if results:
            return True
        return False


    def _query(self, path, query, values=(), include_header=False):
        '''
        recon-ngx --> Migrated across from recon-ng

        Queries the database and returns the results as a list.
        '''
        self._console.debug(f"DATABASE => {path}")
        self._console.debug(f"QUERY => {query}")
        with sqlite3.connect(path) as conn:
            with closing(conn.cursor()) as cur:
                if values:
                    self._console.debug(f"VALUES => {repr(values)}")
                    cur.execute(query, values)
                else:
                    cur.execute(query)
                # a rowcount of -1 typically refers to a select statement
                if cur.rowcount == -1:
                    rows = []
                    if include_header:
                        rows.append(tuple([x[0] for x in cur.description]))
                    rows.extend(cur.fetchall())
                    results = rows
                # a rowcount of 1 == success and 0 == failure
                else:
                    conn.commit()
                    results = cur.rowcount
                return results


    def _migrate_db(self):
        '''
        Migrates the database from a previous version, if necessary
        '''
        raise NotImplementedError("Database class must implement _migrate_db()")

    def _create_db(self):
        '''
        Creates and sets up the database
        '''
        raise NotImplementedError("Database class must implement _create_db()")