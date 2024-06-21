"""
binary_search.py: Electron and nwjs search and categorization
"""

import electron_fuses
import electron_search

from pathlib import Path

from .binary_classification import ElectronVulnerabilityClassification, Classification


class BinarySearch:
    """
    Search for Electron and nwjs applications, and categorize them into
    vulnerable and non-vulnerable applications.

    Parameters:
        search_nwjs (bool): Search for nwjs applications. Defaults to True, otherwise only Electron applications are searched.
        **kwargs: Keyword arguments to pass to the electron_search.Search class.
            search_paths: list = None, platform: str = sys.platform, variant = "electron"
    """
    def __init__(self, search_nwjs: bool = True, **kwargs) -> None:
        self._electron_apps = electron_search.Search(**kwargs, variant="electron").apps
        self._nwjs_apps     = electron_search.Search(**kwargs, variant="nwjs").apps if search_nwjs else []


    @property
    def apps(self) -> list:
        """
        Get a list of categorized applications.
        """
        categorized_apps = {
            # category: [
            #   {
            #       "app":              str,
            #       "framework":        str, # Path to the Electron framework, if different from the application path
            #       "electron_version": str,
            #       "chromium_version": str,
            #       "vulnerabilities":  list
            #   }
            # ]
        }

        # Electron applications
        for app in self._electron_apps:
            electron_core = app
            if Path(electron_core).is_dir():
                electron_core = electron_fuses.ResolveFramework(electron_core).framework

            classification: dict = ElectronVulnerabilityClassification(electron_core).vulnerability_classification()
            category = classification["category"]
            if category not in categorized_apps:
                categorized_apps[category] = []

            categorized_apps[category].append({
                "app":              app,
                "framework":        electron_core,
                "electron_version": classification["electron_version"],
                "chromium_version": classification["chromium_version"],
                "vulnerabilities":  classification["vulnerabilities"]
            })

        # nwjs applications
        for app in self._nwjs_apps:
            if Classification.NWJS.value not in categorized_apps:
                categorized_apps[Classification.NWJS.value] = []

            core = app
            if Path(core).is_dir():
                core = str(Path(app) / "Contents" / "Frameworks" / "nwjs Framework.framework" / "nwjs Framework")

            categorized_apps[Classification.NWJS.value].append({
                "app":              app,
                "framework":        core,
                "electron_version": "N/A",
                "chromium_version": electron_fuses.ElectronVersion(core).chromium_version,
                "vulnerabilities": [electron_fuses.FuseV1Options.RUN_AS_NODE.name]
            })

        # Sort alphabetically
        for category, apps in categorized_apps.items():
            categorized_apps[category] = sorted(apps, key=lambda x: x["app"])
        categorized_apps = dict(sorted(categorized_apps.items(), key=lambda x: x[0]))

        return categorized_apps