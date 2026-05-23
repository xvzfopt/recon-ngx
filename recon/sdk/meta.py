"""
Recon-NGX - Module SDK - Metadata classes
================================
Contains Metadata classes to be used when defining a Module's metadata
"""

# =====================================================================================
# Imports: External
# =====================================================================================
from typing import Any
from dataclasses import dataclass
from dataclasses import field

# =====================================================================================
# Module Metadata Class
# =====================================================================================
@dataclass
class ModuleMetadata:
    '''
    Specifies the metadata for a module

    Attributes:
        name: The module's name
        author: The name(s) of the module's author(s)
        version: The module's version number in the format MAJ.MIN.PATCH
        description: A description of the module and the functionality it provides
        comments: List of module comments displayed when the "info" command is run
        options: List of module options (ModuleOption instances)
        files: A list of modules files TODO
        dependencies: A list of Python packages that this module depends on
        query: A default database query that populates the input data the module runs against
        required_keys: A list of API keys that this modules needs in order to run
        validator: An optional module validator to run against the input data
    '''

    name: str
    author: str
    description: str
    version: str = "1.0.0"
    comments: list = field(default_factory=list)
    options: list = field(default_factory=list)
    files: list = field(default_factory=list)
    dependencies: list = field(default_factory=list)
    query: str = None
    required_keys: list = field(default_factory=list)
    validator: str = None

# =====================================================================================
# Module Option Class
# =====================================================================================
@dataclass
class ModuleOption:
    '''
    Defines the properties of a Module Option

    Attributes:
        name: The option name
        default: The option's default value
        required: Whether the option is required for the module to run
        description: The option's description
    '''

    name: str
    default: Any
    required: bool
    description: str
    validators: list = field(default_factory=list)
