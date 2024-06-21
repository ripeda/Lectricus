"""
__init__.py: Lectricus initialization file.
"""

__version__:      str = "0.0.1"
__description__:  str = "Electron and NWJS Vulnerability Detection Utility"
__url__:          str = "https://github.com/ripeda/lectricus"
__license__:      str = "3-clause BSD License"
__author__:       str = "RIPEDA Consulting"
__author_email__: str = "info@ripeda.com"
__status__:       str = "Beta"
__all__:         list = ["lectricus"]


from .command_line   import main
from .binary_search  import BinarySearch, ElectronVulnerabilityClassification, Classification
from .export_results import ExportVulnerableApplications