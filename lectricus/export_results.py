"""
export_results.py: Export vulnerable applications to specified location
"""

import sys
import json
import logging
import plistlib

from .binary_search import Classification


class ExportVulnerableApplications:
    """
    Export vulnerable applications to specified location.

    Valid formats: xml, plist, json, csv

    If no location is specified, export to stdout.
    """
    def __init__(self, binary_search_results: dict, location: str = None, format: str = "plist"):
        self._results  = binary_search_results
        self._location = location
        self._format   = format


    def _plist_export(self):
        """
        Export vulnerable applications to plist file.
        """
        plistlib.dump(self._results, open(self._location, "wb") if self._location else sys.stdout.buffer)


    def _json_export(self):
        """
        Export vulnerable applications to JSON file.
        """
        if self._location is None:
            print(json.dumps(self._results, indent=4))
            return

        json.dump(self._results, open(self._location, "w"), indent=4)


    def _generic(self):
        """
        Export vulnerable applications to generic format for CLI.
        """
        vulnerable_apps = 0
        for category, apps in self._results.items():
            if category in [Classification.CORRECTLY_CONFIGURED_FUSES.value, Classification.NO_KNOWN_VULNERABILITIES.value]:
                continue
            vulnerable_apps += len(apps)

        if vulnerable_apps == 0:
            logging.info("No vulnerable applications found 🎉")
        else:
            logging.info(f"Found {vulnerable_apps} vulnerable applications 😱")

        for category, apps in self._results.items():
            logging.info(f"{category}:")
            for app in apps:
                logging.info(f"  - {app['app']}")
                if len(app["vulnerabilities"]) == 0:
                    continue
                logging.info("    - Vulnerabilities:")
                for vulnerability in app["vulnerabilities"]:
                    logging.info(f"      - {vulnerability}")


    def export(self):
        if self._format == "plist":
            self._plist_export()
        elif self._format == "json":
            self._json_export()
        elif self._format == "generic":
            self._generic()
        else:
            raise ValueError(f"Invalid format: {self._format}")