# =====================================================================================
# Imports: External
# =====================================================================================
import os
import re
import shutil
from datetime import datetime

# =====================================================================================
# Imports: Internal
# =====================================================================================
from .db import ReconNGXDatabase
from recon.utils import utils

# =====================================================================================
# Workspace Database Class
# =====================================================================================
class WorkspaceDB(ReconNGXDatabase):
    '''
    Recon-NGX Workspace Database
    '''

    # =====================================================================================
    # Properties
    # =====================================================================================

    # =====================================================================================
    # Functions
    # =====================================================================================
    def __init__(self, path, console, modulename):
        '''
        Constructor
        '''
        super(WorkspaceDB, self).__init__(path, console)
        self._modulename = modulename

    # =====================================================================================
    # Insert Function
    # =====================================================================================
    def insert_domains(self, domain=None, notes=None, mute=None):
        '''
        Inserts a new domain name into the Workspace Database

        :param domain: The new domain name to add
        :type domain: str
        :param notes: Any notes on the domain name being added
        :type notes: str
        :param mute: Whether the returns of the table should be displayed after row insertion
        :type mute: bool
        '''

        # Build Data
        data = dict(
            domain=domain,
            notes=notes
        )

        # Insert into table
        rowcount = self._insert("domains", data.copy(), data.keys())
        if not mute:
            self._display_insert_results(data, rowcount)
        return rowcount

    def _display_insert_results(self, data, rowcount):
        '''
        Displays the results of an insert operation

        :param data: The data that was inserted into the table
        :type data: dict
        :param rowcount: The number of rows affected
        :type rowcount: int
        '''
        display = self._console.alert if rowcount else self._console.verbose
        for key in sorted(data.keys()):
            display(f"{key.title()}: {data[key]}")
        display("-"*50)

    # =====================================================================================
    # Snapshot Functions
    # =====================================================================================
    def take_snapshot(self):
        '''
        Takes a snapshot of the database in its current state
        '''

        snapshot_fn = "snapshot_%s.db" % self._generate_snapshot_timestamp()
        workspace_folder = os.path.dirname(self._path)
        dest = os.path.join(workspace_folder, snapshot_fn)
        shutil.copyfile(self._path, dest)
        self._console.output("Snapshot created: %s" % snapshot_fn)

    def get_snapshots(self):
        '''
        Gets all snapshots for this database

        :returns: List of snapshots
        :rtype: list
        '''
        workspace_folder = os.path.dirname(self._path)

        snapshots = []
        for f in os.listdir(workspace_folder):
            if re.search(r'^snapshot_\d{14}.db$', f):
                snapshots.append(f)
        return snapshots

    def load_snapshot(self, snapshot_name):
        '''
        Loads a snapshot for this database

        :param snapshot_name: The name of the snapshot file to load
        :type snapshot_name: str
        '''

        workspace_folder = os.path.dirname(self._path)
        src = os.path.join(workspace_folder, snapshot_name)
        shutil.copy(src, self._path)
        self._console.output(f"Snapshot loaded: {snapshot_name}")

    def remove_snapshot(self, snapshot_name):
        '''
        Removes/delete a snapshot for this database

        :param snapshot_name: The name of the snapshot file to delete
        :type snapshot_name: str
        '''
        workspace_folder = os.path.dirname(self._path)

        snapshot_path = os.path.join(workspace_folder, snapshot_name)
        os.remove(snapshot_path)
        self._console.output(f"Snapshot removed: {snapshot_name}")

    # =====================================================================================
    # Getters
    # =====================================================================================
    def is_modifiable_table(self, table_name):
        '''
        Checks if the specified table supports modification by the user, such as the addition and deletion of rows

        :param table_name: The name of the table to check
        :type table_name: str
        :returns: True if the table supports modification, False otherwise
        :rtype: bool
        '''
        return hasattr(self, "insert_%s" % table_name)

    # =====================================================================================
    # Internal Functions
    # =====================================================================================
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

    def _generate_snapshot_timestamp(self):
        '''
        Generates a new Snapshot timestamp

        :returns: Snapshot timestamp string
        :rtype: str
        '''
        return datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')
