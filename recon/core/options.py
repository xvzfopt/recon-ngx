# =====================================================================================
# Imports: External
# =====================================================================================

# =====================================================================================
# Imports: Internal
# =====================================================================================

# =====================================================================================
# Options Class
# =====================================================================================
class Options(dict):
    '''
    Options Data Object
    recon-ngx --> Migrated across from framework.py of recon-ng
    '''

    def __init__(self, *args, **kwargs):
        self.required = {}
        self.description = {}
        super(Options, self).__init__(*args, **kwargs)

    def __getitem__(self, name):
        name = self.__keytransform__(name)
        return super(Options, self).__getitem__(name)

    def __setitem__(self, name, value):
        name = self.__keytransform__(name)
        value = self._autoconvert(value)
        super(Options, self).__setitem__(name, value)

    def __delitem__(self, name):
        name = self.__keytransform__(name)
        super(Options, self).__delitem__(name)
        if name in self.required:
            del self.required[name]
        if name in self.description:
            del self.description[name]

    def __keytransform__(self, key):
        return key.upper()

    def _boolify(self, value):
        # designed to throw an exception if value is not a string representation of a boolean
        return {'true':True, 'false':False}[value.lower()]

    def _autoconvert(self, value):
        if value in (None, True, False):
            return value
        elif (isinstance(value, str)) and value.lower() in ('none', "''", '""'):
            return None
        orig = value
        for fn in (self._boolify, int, float):
            try:
                value = fn(value)
                break
            except ValueError: pass
            except KeyError: pass
            except AttributeError: pass
        if type(value) is int and '.' in str(orig):
            return float(orig)
        return value

    def init_option(self, name, value=None, required=False, description=''):
        name = self.__keytransform__(name)
        self[name] = value
        self.required[name] = required
        self.description[name] = description

    def serialize(self):
        options = []
        for key in self:
            option = {}
            option['name'] = key
            option['value'] = self[key]
            option['required'] = self.required[key]
            option['description'] = self.description[key]
            options.append(option)
        return options

