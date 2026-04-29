# =====================================================================================
# Imports: External
# =====================================================================================
import os
import re
import shutil
from datetime import datetime
from dateutil import parser as date_parser
from dateutil.parser import ParserError
from rq.worker_pool import run_worker

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
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

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
        Adds a domain name to the Workspace Database

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

        # Add data to table
        rowcount = self._insert("domains", data.copy(), data.keys())
        if not mute:
            self._display_insert_results(data, rowcount)
        return rowcount

    def insert_companies(self, company=None, description=None, notes=None, mute=False):
        '''
        Adds a company to the Workspace Database

        :param company: The new company name to add
        :type company: str
        :param description: A description of the company
        :type description: str
        :param notes: Any notes on the company being added
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''

        # Build Data
        data = dict(
            company = company,
            description = description,
            notes = notes
        )

        # Add company to table
        rowcount = self._insert('companies', data.copy(), ('company',))
        if not mute:
            self._display_insert_results(data, rowcount)
        return rowcount

    def insert_netblocks(self, netblock=None, notes=None, mute=False):
        '''
        Adds a netblock to the Workspace Database

        :param netblock: The netblock to add
        :type netblock: str
        :param notes: Any notes on the netblock being added
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''

        # Build Data
        data = dict(
            netblock = netblock,
            notes = notes
        )

        # Add netblock to table
        rowcount = self._insert('netblocks', data.copy(), data.keys())
        if not mute:
            self._display_insert_results(data, rowcount)
        return rowcount

    def insert_locations(self, latitude=None, longitude=None, street_address=None, notes=None, mute=False):
        '''
        Adds a location to the Workspace Database

        :param latitude: The Latitude of the location
        :type latitude: str
        :param latitude: The Latitude of the location
        :type latitude: str
        :param street_address: The street address of the location
        :type street_address: str
        :param notes: Any notes on the location being added
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''

        # Build location data
        data = dict(
            latitude = latitude,
            longitude = longitude,
            street_address = street_address,
            notes = notes
        )

        # Add data to table
        rowcount = self._insert('locations', data.copy(), data.keys())
        if not mute:
            self._display_insert_results(data, rowcount)
        return rowcount

    def insert_vulnerabilities(self, host=None, reference=None, example=None, publish_date=None, category=None, status=None, notes=None, mute=False):
        '''
        Adds a vulnerability to the database and returns the affected row count.

        :param host: The Hostname or IP Address of the vulnerable host
        :type host: str
        :param reference: The vulnerability reference
        :type reference: str
        :param example: The vulnerability example
        :type example: str
        :param publish_date: The publish date of the vulnerability
        :type publish_date: str
        :param category: A category for the vulnerability
        :type category: str
        :param status: A vulnerability status
        :type status: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''

        # Process Publish Date
        if publish_date:
            try:
                publish_date = date_parser.parse(publish_date)
            except ParserError:
                self._console.error("Publish Date is not a valid date/time")
                return 0

        # Build vuln data
        data = dict(
            host = host,
            reference = reference,
            example = example,
            publish_date = publish_date.strftime(self.DATE_FORMAT) if publish_date else None,
            category = category,
            status = status,
            notes = notes
        )

        # Add data to table
        rowcount = self._insert('vulnerabilities', data.copy(), data.keys())
        if not mute:
            self._display_insert_results(data, rowcount)
        return rowcount

    def insert_ports(self, ip_address=None, host=None, port=None, protocol=None, banner=None, notes=None, mute=False):
        '''
        Adds a port to the Workspace Database

        :param ip_address: The IP Address of the host for this port
        :type ip_address: str
        :param host: The Hostname of the host for this port
        :type host: str
        :param port: The Port Number
        :type port: str
        :param protocol: The Protocol associated with the port number, e.g. SSH
        :type protocol: str
        :param banner: The banner of the service listening on the port
        :type banner: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''

        # Build Port data
        data = dict(
            ip_address = ip_address,
            port = port,
            host = host,
            protocol = protocol,
            banner = banner,
            notes = notes
        )

        # Add data to table
        rowcount = self._insert('ports', data.copy(), ('ip_address', 'port', 'host'))
        if not mute:
            self._display_insert_results(data, rowcount)
        return rowcount

    def insert_hosts(self, host=None, ip_address=None, region=None, country=None, latitude=None, longitude=None, notes=None, mute=False):
        '''
        Adds a host to the Workspace Database

        :param host: The hostname of the host
        :type host: str
        :param ip_address: The IP Address of the host
        :type ip_address: str
        :param region: The region in which the host is located
        :type region: str
        :param country: The country in which the host is located
        :type country: str
        :param latitude: The latitude where the host is located
        :type latitude: str
        :param longitude: The longitude where the host is located
        :type longitude: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''

        # Build Host data
        data = dict(
            host = host,
            ip_address = ip_address,
            region = region,
            country = country,
            latitude = latitude,
            longitude = longitude,
            notes = notes
        )

        # Add data to table
        rowcount = self._insert('hosts', data.copy(), ('host', 'ip_address'))
        if not mute:
            self._display_insert_results(data, rowcount)
        return rowcount

    def insert_contacts(self, first_name=None, middle_name=None, last_name=None, email=None, title=None, region=None, country=None, phone=None, notes=None, mute=False):
        '''
        Adds a contact to the Workspace Database

        :param first_name: The first name of the contact
        :type first_name: str
        :param middle_name: The middle name of the contact
        :type middle_name: str
        :param last_name: The last name of the contact
        :type last_name: str
        :param email: The email address of the contact
        :type email: str
        :param title: The contact's title
        :type title: str
        :param region: The region in which the contact is located
        :type region: str
        :param country: The country in which the contact is located
        :type country: str
        :param phone: The phone number of the contact
        :type phone: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''

        # Build Contact data
        data = dict(
            first_name = first_name,
            middle_name = middle_name,
            last_name = last_name,
            title = title,
            email = email,
            region = region,
            country = country,
            phone = phone,
            notes = notes
        )

        # Add data to table
        rowcount = self._insert('contacts', data.copy(), ('first_name', 'middle_name', 'last_name', 'title', 'email', 'phone'))
        if not mute:
            self._display_insert_results(data, rowcount)
        return rowcount

    def insert_credentials(self, username=None, password=None, _hash=None, _type=None, leak=None, notes=None, mute=False):
        '''
        Adds a set of credentials to the Workspace Database

        :param username: The username
        :type username: str
        :param password: The password
        :type password: str
        :param _hash: The hash of the password
        :type _hash: str
        :param _type: The hash type of the password
        :type _type: str
        :param leak: A leak associated with this credential set
        :type leak: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''

        # =====================================================================================
        # Process Hash
        # =====================================================================================
        hash_type = _type
        if password and not _hash:
            hash_type = utils.get_hash_type(password)
            if hash_type:
                _hash = password
                password = None
        # handle hashes provided without a type
        if _hash and not _type:
            hash_type = utils.get_hash_type(_hash)

        # =====================================================================================
        # Process Email Addresses
        # =====================================================================================
        if username is not None and '@' in username:
            self.insert_contacts(first_name=None, last_name=None, title=None, email=username)

        # Build Credential data
        data = dict (
            username = username,
            password = password,
            hash = _hash,
            type = hash_type,
            leak = leak,
            notes = notes
        )

        rowcount = self._insert('credentials', data.copy(), data.keys())
        if not mute:
            self._display_insert_results(data, rowcount)
        return rowcount


    def insert_leaks(self, leak_id=None, description=None, source_refs=None, leak_type=None, title=None, import_date=None, leak_date=None, attackers=None, num_entries=None, score=None, num_domains_affected=None, attack_method=None, target_industries=None, password_hash=None, password_type=None, targets=None, media_refs=None, notes=None, mute=False):
        '''
        Adds a leak to the Workspace Database

        :param leak_id: The ID associated with the leak
        :type leak_id: int
        :param description: A description of the leak
        :type description: str
        :param source_refs: References for the leak
        :type source_refs: str
        :param leak_type: The leak type
        :type leak_type: str
        :param title: The leak's title
        :type title: str
        :param import_date: The source data of the leak (TBC)
        :type import_date: str
        :param leak_date: The date of the leak
        :type leak_date: str
        :param attackers: The attackers responsible for/associated with the leak
        :type attackers: str
        :param num_entries: The number of entries associated within the leak
        :type num_entries: str
        :param score: A score associated with the leak
        :type score: str
        :param num_domains_affected: The number of domains affected by the leak
        :type num_domains_affected: str
        :param attack_method: An attack method associated with the leak
        :type attack_method: str
        :param target_industries: The industries targeted in the leak
        :type target_industries: str
        :param password_hash: The password hash of the leak (TBC)
        :type password_hash: str
        :param password_type: The password's hash type (TBV)
        :type password_type: str
        :param targets: The targets associated with the leak
        :type targets: str
        :param media_refs: Any media references associated with the leak
        :type media_refs: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''

        # Build Leak data
        data = dict(
            leak_id = leak_id,
            description = description,
            source_refs = source_refs,
            leak_type = leak_type,
            title = title,
            import_date = import_date,
            leak_date = leak_date,
            attackers = attackers,
            num_entries = num_entries,
            score = score,
            num_domains_affected = num_domains_affected,
            attack_method = attack_method,
            target_industries = target_industries,
            password_hash = password_hash,
            password_type = password_type,
            targets = targets,
            media_refs = media_refs,
            notes = notes
        )

        # Add leak data to table
        rowcount = self._insert('leaks', data.copy(), data.keys())
        if not mute:
            self._display_insert_results(data, rowcount)
        return rowcount

    def insert_pushpins(self, source=None, screen_name=None, profile_name=None, profile_url=None, media_url=None, thumb_url=None, message=None, latitude=None, longitude=None, time=None, notes=None, mute=False):
        '''
        Adds a pushpin to the Workspace Database

        :param source: The source associated with the pushpin
        :type source: str
        :param screen_name: The screen_name of the account associated with the pushpin (TBC)
        :type screen_name: str
        :param profile_name: The profile_name of the account associated with the pushpin (TBC)
        :type profile_name: str
        :param profile_url: The URL of the account associated with the pushpin (TBC)
        :type profile_url: str
        :param media_url: The Media URL of the pushpin (TBC)
        :type media_url: str
        :param thumb_url: The URL of the thumbnail associated with the pushpin (TBC)
        :type thumb_url: str
        :param message: The pushpin message/text content
        :type message: str
        :param latitude: The latitude of the pushpin
        :type latitude: str
        :param longitude: The longitude of the pushpin
        :type longitude: str
        :param time: The pushpin time/date
        :type time: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''

        # Process time/date
        if time:
            try:
                time = date_parser.parse(time)
            except ParserError:
                self._console.error("Time is not a valid date/time")
                return 0


        # Create pushpin data
        data = dict(
            source = source,
            screen_name = screen_name,
            profile_name = profile_name,
            profile_url = profile_url,
            media_url = media_url,
            thumb_url = thumb_url,
            message = message,
            latitude = latitude,
            longitude = longitude,
            time = time.strftime(self.DATE_FORMAT) if time else None,
            notes = notes
        )

        # Add pushpin data to table
        rowcount = self._insert('pushpins', data.copy(), data.keys())
        if not mute: self._display_insert_results(data, rowcount)
        return rowcount

    def insert_profiles(self, username=None, resource=None, url=None, category=None, notes=None, mute=False):
        '''
        Adds a profile to the Workspace Database

        :param username: The username of the profile's account
        :type username: str
        :param resource: The profile resource (TBC)
        :type resource: str
        :param url: The profile url
        :type url: str
        :param category: A category for the profile
        :type category: str
        :param notes: Any additional notes
        :type notes: str
        :param mute: Whether the table should be displayed after row insertion
        :type mute: bool
        '''

        # Build profile data
        data = dict(
            username = username,
            resource = resource,
            url = url,
            category = category,
            notes = notes
        )

        # Add profile data to table
        rowcount = self._insert('profiles', data.copy(), ('username', 'url'))
        if not mute:
            self._display_insert_results(data, rowcount)
        return rowcount

    def insert_repositories(self, name=None, owner=None, description=None, resource=None, category=None, url=None, notes=None, mute=False):
        '''
        Adds a repository to the Workspace Database
        '''

        # Build Repository data
        data = dict(
            name = name,
            owner = owner,
            description = description,
            resource = resource,
            category = category,
            url = url,
            notes = notes
        )

        # Add repository data to database
        rowcount = self._insert('repositories', data.copy(), data.keys())
        if not mute:
            self._display_insert_results(data, rowcount)
        return rowcount

    # =====================================================================================
    # General Functions
    # =====================================================================================
    def set_row_note(self, table, row_id, note):
        '''
        Sets the note for a row in the specified table

        :param table: The target table
        :type table: str
        :param row_id: The ID of the row to add the note to
        :type row_id: int
        :param note: The note to add
        :type note: str
        '''
        query = "UPDATE %s SET notes=? WHERE ROWID = ?" % (table)
        return self.query(query, (note, row_id))

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

    def _generate_snapshot_timestamp(self):
        '''
        Generates a new Snapshot timestamp

        :returns: Snapshot timestamp string
        :rtype: str
        '''
        return datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')
