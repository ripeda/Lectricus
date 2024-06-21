"""
lectricus_gui.py: GUI frontend for Lectricus
"""

import wx
import random
import plistlib
import lectricus
import threading
import subprocess

from pathlib import Path


class LectricusFrame(wx.Frame):

    def __init__(self, *args, **kw):
        super(LectricusFrame, self).__init__(*args, **kw)

        self.vulnerable_apps = None

        self.unused_names = []
        self.unused_icons = []
        self.demo_mode = self._demo_mode_status()

        if self.demo_mode is True:
            self._load_names()
            self._load_icons()

        self.SetMenuBar(wx.MenuBar())
        self.InitUI()
        self.Centre()


    def _demo_mode_status(self) -> bool:
        """
        Check if demo mode is enabled
        """
        return Path("/tmp/lectricus_demo").exists()


    def _load_names(self):
        """
        Load names from wordlist.txt
        """
        with open("/tmp/lectricus_demo/wordlist.txt", "r") as f:
            self.unused_names = f.readlines()


    def _load_icons(self):
        """
        Grab list of icons from icons directory
        """
        self.unused_icons = [str(icon) for icon in Path("/tmp/lectricus_demo/icons").glob("*.png")]


    def _randomized_app_name(self) -> str:
        """
        Generate randomized application name
        """
        words = self.unused_names
        if len(words) == 0:
            self._load_names()
            words = self.unused_names

        first_name = random.choice(words)
        words.remove(first_name)

        last_name = random.choice(words)
        words.remove(last_name)

        return f"/Applications/{first_name.strip().capitalize()} {last_name.strip().capitalize()}.app"


    def _randomize_app_icon(self) -> str:
        """
        Randomize application icon
        """
        icons = self.unused_icons
        if len(icons) == 0:
            self._load_icons()
            icons = self.unused_icons

        icon = random.choice(icons)
        icons.remove(icon)

        return icon


    def _friendly_host_os_to_sys(self, os: str) -> str:
        """
        Resolve friendly OS name to system name
        """
        os = os.split(" ")[-1]
        if os == "macOS":
            return "darwin"
        if os == "Windows":
            return "win32"
        if os == "Linux":
            return "linux"
        raise ValueError(f"Invalid OS: {os}")


    def _get_vulnerable_apps(self):
        self.vulnerable_apps = lectricus.BinarySearch(
            platform=self._friendly_host_os_to_sys(self.os_dropdown.GetStringSelection()),
            search_paths=[self.directory_dropdown.GetPath()]
        ).apps


    def _export_vulnerable_apps(self, location: str, format: str):
        lectricus.ExportVulnerableApplications(location=location, format=format, binary_search_results=self.vulnerable_apps).export()


    def OnExport(self, e):
        dlg = wx.FileDialog(
            parent=self,
            message="Choose a file",
            defaultDir=str(Path("~/Desktop").expanduser()),
            defaultFile="vulnerability-breakdown",
            wildcard="PLIST (*.plist)|*.plist|XML (*.xml)|*.xml|JSON (*.json)|*.json|CSV (*.csv)|*.csv",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        if dlg.ShowModal() == wx.ID_OK:
            filters = ["plist", "xml", "json", "csv"]
            self._export_vulnerable_apps(dlg.GetPath(), filters[dlg.GetFilterIndex()])
        dlg.Destroy()
        subprocess.run(["/usr/bin/open", "--reveal", dlg.GetPath()])


    def _resolve_icon_from_path(self, path: str) -> str:
        """
        Resolve application icon from path
        """
        os = self._friendly_host_os_to_sys(self.os_dropdown.GetStringSelection())
        if os == "darwin":
            return self._resolve_macos_icon(path)

        raise NotImplementedError(f"Icon resolution for {os} is not implemented")


    def _resolve_macos_icon(self, input_path: str) -> str:
        """
        Resolve macOS application icon
        """
        default_icon = "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericApplicationIcon.icns"

        info_plist = Path(input_path) / "Contents" / "Info.plist"
        if not info_plist.is_file():
            return default_icon
        plist = plistlib.load(open(info_plist, "rb"))
        if "CFBundleIconFile" not in plist:
            return default_icon
        icon_path = plist["CFBundleIconFile"]
        if not icon_path:
            return default_icon

        icon_path = Path(input_path) / "Contents" / "Resources" / icon_path
        if not icon_path.is_file():
            return default_icon

        return str(icon_path)


    def _icon_to_bitmap(self, icon: str, size: tuple = (32, 32)) -> wx.Bitmap:
        """
        Convert icon to bitmap
        """
        return wx.Bitmap(wx.Bitmap(icon, wx.BITMAP_TYPE_ICON).ConvertToImage().Rescale(size[0], size[1], wx.IMAGE_QUALITY_HIGH))


    def OnList(self, e: wx.Event):
        # Create new Model Frame with indeterminate progress bar
        frame = wx.Dialog(self, -1, "Listing vulnerable applications")
        title = wx.StaticText(frame, label="Searching for vulnerable applications")
        title.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        title.SetPosition((-1, 15))
        title.Center(wx.HORIZONTAL)

        subtitle = wx.StaticText(frame, label="Please wait...")
        subtitle.SetPosition((-1, title.GetPosition()[1] + 20))
        subtitle.Center(wx.HORIZONTAL)

        gauge = wx.Gauge(frame, -1, subtitle.GetPosition()[1] + 20, (20, 50), (250, 25))
        gauge.Center(wx.HORIZONTAL)
        gauge.Pulse()
        frame.SetSize((-1, gauge.GetPosition()[1] + 80))

        frame.ShowWindowModal()
        wx.Yield()

        thread = threading.Thread(target=self._get_vulnerable_apps)
        thread.start()

        while thread.is_alive():
            wx.Yield()

        # Close the Model Frame
        frame.Destroy()

        # Create new Model Frame with list of vulnerable applications
        frame = wx.Dialog(self, -1, "Vulnerable applications")
        frame.SetSize((890, -1))

        title = wx.StaticText(frame, label="Vulnerable applications")
        title.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        title.SetPosition((-1, 15))
        title.Center(wx.HORIZONTAL)

        vulnerable_apps = 0
        for category, apps in self.vulnerable_apps.items():
            if category in [lectricus.Classification.CORRECTLY_CONFIGURED_FUSES.value, lectricus.Classification.NO_KNOWN_VULNERABILITIES.value]:
                continue
            vulnerable_apps += len(apps)

        subtitle = wx.StaticText(frame, label=f"Number of vulnerable applications: {vulnerable_apps}")
        subtitle.SetPosition((-1, title.GetPosition()[1] + 20))
        subtitle.Center(wx.HORIZONTAL)

        position = title.GetPosition()[1] + 50

        id = wx.NewIdRef()
        list = wx.ListCtrl(frame, id, (20, position), style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        list.SetSize((850, 600))
        list.Center(wx.HORIZONTAL)
        list.InsertColumn(0, "Path", width=350)
        list.InsertColumn(1, "Vulnerability", width=250)
        list.InsertColumn(2, "Electron Version", width=100)
        list.InsertColumn(3, "Chromium Version", width=130)


        # Build bit map bundle, and handle demo mode if applicable
        app_icon_cache = {
            # "app": {
            #   "bundle": wx.BitmapBundle,
            #   "raw": str
            #}
        }
        for category, apps in self.vulnerable_apps.items():
            for app in apps:
                # Mask true application in demo mode
                if self.demo_mode is True and category not in [lectricus.Classification.CORRECTLY_CONFIGURED_FUSES.value, lectricus.Classification.NO_KNOWN_VULNERABILITIES.value]:
                    _original_app = app["app"]
                    _new_app = self._randomized_app_name()

                    app["app"] = _new_app
                    app["framework"] = app["framework"].replace(_original_app, _new_app)

                    icon = self._randomize_app_icon()
                else:
                    icon = self._resolve_icon_from_path(app["app"])

                if app["app"] not in app_icon_cache:
                    app_icon_cache[app["app"]] = {
                        "bundle": wx.BitmapBundle.FromBitmaps([self._icon_to_bitmap(icon), self._icon_to_bitmap(icon, (64, 64))]),
                    }

        list.SetSmallImages([app_icon_cache[app["app"]]["bundle"] for category, apps in self.vulnerable_apps.items() for app in apps])

        for category, apps in self.vulnerable_apps.items():
            for app in apps:
                index = list.InsertItem(list.GetItemCount(), app["app"])
                list.SetItemImage(index, list.GetItemCount() - 1)

                list.SetItem(index, 1, category)
                list.SetItem(index, 2, app["electron_version"])
                list.SetItem(index, 3, app["chromium_version"])


        # Get position of last item
        if list.GetItemCount() == 0:
            position = list.GetPosition()[1] + 20
        else:
            position = list.GetItemRect(list.GetItemCount() - 1).GetBottom() + 20
        if position > 600:
            position = 600
        list.SetSize((-1, position))
        position += 90

        export_button = wx.Button(frame, label="Export report to file")
        export_button.Bind(wx.EVT_BUTTON, self.OnExport)
        export_button.SetPosition((-1, position))
        export_button.Center(wx.HORIZONTAL)

        return_button = wx.Button(frame, label="Return")
        return_button.Bind(wx.EVT_BUTTON, lambda e: frame.Destroy())
        return_button.SetPosition((-1, export_button.GetPosition()[1] + 30))
        return_button.Center(wx.HORIZONTAL)

        frame.SetSize((-1, return_button.GetPosition()[1] + 70))

        frame.ShowWindowModal()
        wx.Yield()


    def InitUI(self):
        self.SetSize((400, 200))

        self.title = wx.StaticText(self, label="Lectricus")
        self.title.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        self.title.SetPosition((-1, 10))
        self.title.Center(wx.HORIZONTAL)

        self.subtitle = wx.StaticText(self, label="Detect misconfigured Electron applications")
        self.subtitle.SetPosition((-1, self.title.GetPosition()[1] + 20))
        self.subtitle.Center(wx.HORIZONTAL)

        # Dropdown to select directory to search for vulnerable applications
        self.directory_dropdown = wx.DirPickerCtrl(self, message="Search Directory", path="/Applications")
        self.directory_dropdown.SetSize((194, -1))
        self.directory_dropdown.SetPosition((-1, self.subtitle.GetPosition()[1] + 30))
        self.directory_dropdown.Center(wx.HORIZONTAL)

        # Dropdown to configure OS (darwin, win32, linux)
        self.os_dropdown = wx.Choice(self, choices=["Search Schema: macOS", "Search Schema: Windows", "Search Schema: Linux"])
        self.os_dropdown.SetSize((194, -1))
        self.os_dropdown.SetSelection(0)
        self.os_dropdown.SetPosition((-1, self.directory_dropdown.GetPosition()[1] + 30))
        self.os_dropdown.Center(wx.HORIZONTAL)

        # Button to list vulnerable applications
        self.list_button = wx.Button(self, label="List vulnerable applications")
        self.list_button.Bind(wx.EVT_BUTTON, self.OnList)
        self.list_button.SetSize((194, -1))
        self.list_button.SetPosition((-1, self.os_dropdown.GetPosition()[1] + 30))
        self.list_button.Center(wx.HORIZONTAL)
        self.list_button.SetDefault()

        # RIPEDA Consulting
        self.ripeda = wx.StaticText(self, label=f"Engineered by {lectricus.__author__}")
        self.ripeda.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        self.ripeda.SetPosition((-1, self.list_button.GetPosition()[1] + 40))
        self.ripeda.Center(wx.HORIZONTAL)

        self.SetTitle(f"Lectricus v{lectricus.__version__}")
        self.Centre()

        self.SetSize((-1, self.ripeda.GetPosition()[1] + 60))

        self.Show(True)


def main():
    app = wx.App()
    LectricusFrame(None, style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
    app.MainLoop()


if __name__ == "__main__":
    main()