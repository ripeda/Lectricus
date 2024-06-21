"""
binary_classification.py: Vulnerability classification for Electron and nwjs applications
"""

import enum
import electron_fuses

import packaging.version


class Classification(enum.Enum):
    """
    Vulnerability classification for Electron and nwjs applications.
    """
    CORRECTLY_CONFIGURED_FUSES = "Correctly Configured Electron Fuses"
    MISCONFIGURED_FUSES        = "Misconfigured Electron Fuses"
    LACKING_FUSE_SUPPORT       = "Lacking Electron Fuse Support"
    NO_KNOWN_VULNERABILITIES   = "No known vulnerabilities"
    NWJS                       = "nwjs"


class ElectronVulnerabilityClassification:
    """
    Classify Electron and nwjs applications into vulnerable and non-vulnerable applications.

    Parameters:
        app:       Application path
        framework: Framework path (if different from the application path, ex. macOS and Electron framework)
    """
    def __init__(self, app: str, framework: str = None) -> None:
        self._app       = app
        self._framework = framework if framework else self._app

        self._common_binary_vulnerabilities = {
            electron_fuses.FuseV1Options.RUN_AS_NODE.name: {
                "introduced": packaging.version.parse("0.35.2"),
                "fuse":       electron_fuses.FuseV1Options.RUN_AS_NODE
            },
            electron_fuses.FuseV1Options.ENABLE_NODE_CLI_INSPECT_ARGUMENTS.name: {
                "introduced": packaging.version.parse("2.0.0"),
                "fuse":       electron_fuses.FuseV1Options.ENABLE_NODE_CLI_INSPECT_ARGUMENTS
            },
        }


    def vulnerability_classification(self) -> dict:
        try:
            return self._vulnerable_fuse_config_app()
        except electron_fuses.SentinelNotFound:
            return self._vulnerable_legacy_app()


    def _vulnerable_legacy_app(self) -> dict:
        """
        Vulnerability classification for Electron applications lacking fuse support (v12.0.0)
        """
        version_obj = electron_fuses.ElectronVersion(self._framework)
        try:
            electron_version = packaging.version.parse(version_obj.electron_version)
        except packaging.version.InvalidVersion:
            electron_version = packaging.version.parse("0.0.0")

        vulnerabilities = []
        for vulnerability, data in self._common_binary_vulnerabilities.items():
            if electron_version < data["introduced"]:
                # Feature not implemented in this version
                continue
            vulnerabilities.append(vulnerability)

        return {
            "category": Classification.LACKING_FUSE_SUPPORT.value if len(vulnerabilities) > 0 else Classification.NO_KNOWN_VULNERABILITIES.value,
            "electron_version": version_obj.electron_version,
            "chromium_version": version_obj.chromium_version,
            "vulnerabilities":  vulnerabilities
        }


    def _vulnerable_fuse_config_app(self) -> dict:
        """
        Vulnerability classification for Electron applications with fuse support (v12.0.0+)
        """
        fuse_obj = electron_fuses.FuseConfig(self._framework)
        version_obj = electron_fuses.ElectronVersion(self._framework)
        electron_version = packaging.version.parse(version_obj.electron_version)

        vulnerabilities = []
        for vulnerability, data in self._common_binary_vulnerabilities.items():
            if data["fuse"] not in fuse_obj.config:
                if electron_version < data["introduced"]:
                    # Feature not implemented in this version
                    continue
                vulnerabilities.append(vulnerability)
                continue
            if fuse_obj.config[data["fuse"]] != electron_fuses.FuseState.ENABLE:
                continue
            vulnerabilities.append(vulnerability)

        return {
            "category": Classification.MISCONFIGURED_FUSES.value if len(vulnerabilities) > 0 else Classification.CORRECTLY_CONFIGURED_FUSES.value,
            "electron_version": version_obj.electron_version,
            "chromium_version": version_obj.chromium_version,
            "vulnerabilities":  vulnerabilities
        }