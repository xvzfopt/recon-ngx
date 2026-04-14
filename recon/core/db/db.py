# =====================================================================================
# Imports: External
# =====================================================================================
import os
import sqlite3
from datetime import datetime
from contextlib import closing

# =====================================================================================
# Imports: Internal
# =====================================================================================
from recon.utils import utils


# =====================================================================================
# Workspace Database Class
# =====================================================================================
class WorkspaceDB:
    '''
    Workspace Database
    '''
    
    # =====================================================================================
    # Properties
    # =====================================================================================
    
    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, path, output):
        '''
        Constructor

        :param path: path to database file
        :type path: str
        '''
        self._path = path
        self._output = output

        # Perform DB Setup/Migration
        if not self.db_exists():
            self.create()
        else:
            self.migrate()

    def create(self):
        '''
        Creates and sets up the Workspace database
        '''
        self._create_db()

    def migrate(self):
        '''
        Performs Database migration tasks
        '''
        self._migrate_db()

    def db_exists(self):
        '''
        Checks if the Workspace Database exists

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

        :return: The Modification Time of this workspace
        :rtype: str
        '''
        return datetime.fromtimestamp(
            os.path.getmtime(self._path)
        ).strftime('%Y-%m-%d %H:%M:%S')

    # =====================================================================================
    # Internal Functions
    # =====================================================================================
    def _query(self, path, query, values=(), include_header=False):
        '''
        recon-ngx --> Migrated across from recon-ng

        Queries the database and returns the results as a list.
        '''
        self._output.debug(f"DATABASE => {path}")
        self._output.debug(f"QUERY => {query}")
        with sqlite3.connect(path) as conn:
            with closing(conn.cursor()) as cur:
                if values:
                    self._output.debug(f"VALUES => {repr(values)}")
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
        recon-ngx --> Migrated across from recon-ng
        '''
        db_version = lambda self: self.query('PRAGMA user_version')[0][0]
        db_orig = db_version(self)
        if db_version(self) == 0:
            # add mname column to contacts table
            tmp = utils.get_random_str(20)
            self.query(f"ALTER TABLE contacts RENAME TO {tmp}")
            self.query('CREATE TABLE contacts (fname TEXT, mname TEXT, lname TEXT, email TEXT, title TEXT, region TEXT, country TEXT)')
            self.query(f"INSERT INTO contacts (fname, lname, email, title, region, country) SELECT fname, lname, email, title, region, country FROM {tmp}")
            self.query(f"DROP TABLE {tmp}")
            self.query('PRAGMA user_version = 1')
        if db_version(self) == 1:
            # rename name columns
            tmp = utils.get_random_str(20)
            self.query(f"ALTER TABLE contacts RENAME TO {tmp}")
            self.query('CREATE TABLE contacts (first_name TEXT, middle_name TEXT, last_name TEXT, email TEXT, title TEXT, region TEXT, country TEXT)')
            self.query(f"INSERT INTO contacts (first_name, middle_name, last_name, email, title, region, country) SELECT fname, mname, lname, email, title, region, country FROM {tmp}")
            self.query(f"DROP TABLE {tmp}")
            # rename pushpin table
            self.query('ALTER TABLE pushpin RENAME TO pushpins')
            # add new tables
            self.query('CREATE TABLE IF NOT EXISTS domains (domain TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS companies (company TEXT, description TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS netblocks (netblock TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS locations (latitude TEXT, longitude TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS vulnerabilities (host TEXT, reference TEXT, example TEXT, publish_date TEXT, category TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS ports (ip_address TEXT, host TEXT, port TEXT, protocol TEXT)')
            self.query('CREATE TABLE IF NOT EXISTS leaks (leak_id TEXT, description TEXT, source_refs TEXT, leak_type TEXT, title TEXT, import_date TEXT, leak_date TEXT, attackers TEXT, num_entries TEXT, score TEXT, num_domains_affected TEXT, attack_method TEXT, target_industries TEXT, password_hash TEXT, targets TEXT, media_refs TEXT)')
            self.query('PRAGMA user_version = 2')
        if db_version(self) == 2:
            # add street_address column to locations table
            self.query('ALTER TABLE locations ADD COLUMN street_address TEXT')
            self.query('PRAGMA user_version = 3')
        if db_version(self) == 3:
            # account for db_version bug
            if 'creds' in self.get_tables():
                # rename creds table
                self.query('ALTER TABLE creds RENAME TO credentials')
            self.query('PRAGMA user_version = 4')
        if db_version(self) == 4:
            # add status column to vulnerabilities table
            if 'status' not in [x[0] for x in self.get_columns('vulnerabilities')]:
                self.query('ALTER TABLE vulnerabilities ADD COLUMN status TEXT')
            # add module column to all tables
            for table in ['domains', 'companies', 'netblocks', 'locations', 'vulnerabilities', 'ports', 'hosts', 'contacts', 'credentials', 'leaks', 'pushpins']:
                if 'module' not in [x[0] for x in self.get_columns(table)]:
                    self.query(f"ALTER TABLE {table} ADD COLUMN module TEXT")
            self.query('PRAGMA user_version = 5')
        if db_version(self) == 5:
            # add profile table
            self.query('CREATE TABLE IF NOT EXISTS profiles (username TEXT, resource TEXT, url TEXT, category TEXT, notes TEXT, module TEXT)')
            self.query('PRAGMA user_version = 6')
        if db_version(self) == 6:
            # add repositories table
            self.query('CREATE TABLE IF NOT EXISTS repositories (name TEXT, owner TEXT, description TEXT, resource TEXT, category TEXT, url TEXT, module TEXT)')
            self.query('PRAGMA user_version = 7')
        if db_version(self) == 7:
            # add password_type column to leaks table
            self.query('ALTER TABLE leaks ADD COLUMN password_type TEXT')
            self.query('UPDATE leaks SET password_type=\'unknown\'')
            self.query('PRAGMA user_version = 8')
        if db_version(self) == 8:
            # add banner column to ports table
            self.query('ALTER TABLE ports ADD COLUMN banner TEXT')
            # add notes column to all tables
            for table in ['domains', 'companies', 'netblocks', 'locations', 'vulnerabilities', 'ports', 'hosts', 'contacts', 'credentials', 'leaks', 'pushpins', 'profiles', 'repositories']:
                if 'notes' not in [x[0] for x in self.get_columns(table)]:
                    self.query(f"ALTER TABLE {table} ADD COLUMN notes TEXT")
            self.query('PRAGMA user_version = 9')
        if db_version(self) == 9:
            # add phone column to contacts table
            self.query('ALTER TABLE contacts ADD COLUMN phone TEXT')
            self.query('PRAGMA user_version = 10')
        if db_orig != db_version(self):
            self.alert(f"Database upgraded to version {db_version(self)}.")

    def _create_db(self):
        '''
        recon-ngx --> Migrated across from recon-ng
        '''
        self.query('CREATE TABLE IF NOT EXISTS domains (domain TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS companies (company TEXT, description TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS netblocks (netblock TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS locations (latitude TEXT, longitude TEXT, street_address TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS vulnerabilities (host TEXT, reference TEXT, example TEXT, publish_date TEXT, category TEXT, status TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS ports (ip_address TEXT, host TEXT, port TEXT, protocol TEXT, banner TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS hosts (host TEXT, ip_address TEXT, region TEXT, country TEXT, latitude TEXT, longitude TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS contacts (first_name TEXT, middle_name TEXT, last_name TEXT, email TEXT, title TEXT, region TEXT, country TEXT, phone TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS credentials (username TEXT, password TEXT, hash TEXT, type TEXT, leak TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS leaks (leak_id TEXT, description TEXT, source_refs TEXT, leak_type TEXT, title TEXT, import_date TEXT, leak_date TEXT, attackers TEXT, num_entries TEXT, score TEXT, num_domains_affected TEXT, attack_method TEXT, target_industries TEXT, password_hash TEXT, password_type TEXT, targets TEXT, media_refs TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS pushpins (source TEXT, screen_name TEXT, profile_name TEXT, profile_url TEXT, media_url TEXT, thumb_url TEXT, message TEXT, latitude TEXT, longitude TEXT, time TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS profiles (username TEXT, resource TEXT, url TEXT, category TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS repositories (name TEXT, owner TEXT, description TEXT, resource TEXT, category TEXT, url TEXT, notes TEXT, module TEXT)')
        self.query('CREATE TABLE IF NOT EXISTS dashboard (module TEXT PRIMARY KEY, runs INT)')
        self.query('PRAGMA user_version = 10')


    def test(self):
        pass