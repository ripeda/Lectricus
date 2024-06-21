"""
setup.py: Setup script for lectricus application.

Usage:
    python3 -m build --wheel
"""

from setuptools import setup, find_packages


def resolve_readme() -> str:
    """
    README may reference local resources that PyPI does not have access to.
    Thus resolve local resources to their remote counterparts.

    Returns:
        The resolved README contents.
    """
    repo_base = fetch_property("__url__:")
    repo_raw = repo_base.replace("github.com", "raw.githubusercontent.com")

    contents = open("README.md", "r").read()

    replacements = [
        ".resources/icons/",
        ".resources/images/",
    ]

    for replacement in replacements:
        contents = contents.replace(replacement, f"{repo_raw}/main/{replacement}")

    return contents


def fetch_property(property: str) -> str:
    """
    Fetch a property from the main lectricus class.

    Parameters:
        property (str): The name of the property to fetch.

    Returns:
        The value of the property.
    """
    for line in open("lectricus/__init__.py", "r").readlines():
        if not line.startswith(property):
            continue
        return line.split("=")[1].strip().strip('"')
    raise ValueError(f"Property {property} not found.")


def status_to_classifier(status: str) -> str:
    """
    Convert a status to a classifier.

    Parameters:
        status (str): The status to convert.

    Returns:
        The classifier.
    """
    statuses = [
        "Planning",
        "Pre-Alpha",
        "Alpha",
        "Beta",
        "Production/Stable",
        "Mature",
        "Inactive",
    ]

    if status not in statuses:
        raise ValueError(f"Status {status} not found.")

    return f"Development Status :: {statuses.index(status) + 1} - {status}"


setup(
    name="lectricus",
    version=fetch_property("__version__:"),
    description=fetch_property("__description__:"),
    long_description_content_type="text/markdown",
    long_description=resolve_readme(),
    author=fetch_property("__author__:"),
    author_email=fetch_property("__author_email__:"),
    license=fetch_property("__license__:"),
    url=fetch_property("__url__:"),
    python_requires=">=3.6",
    packages=find_packages(include=["lectricus", "lectricus.electron_exploits"]),
    package_data={
        "lectricus": ["*"],
        "lectricus.electron_exploits": ["*"],
    },
    entry_points={
        "console_scripts": [
            "lectricus = lectricus.command_line:main",
        ],
    },
    py_modules=["lectricus"],
    include_package_data=True,
    install_requires=open("requirements.txt", "r").readlines(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        status_to_classifier(fetch_property("__status__:")),
    ],
)