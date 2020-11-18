import sys

from cx_Freeze import Executable, setup

sys.path.append('bin')

includefiles = ['README.md', 'LICENSE', r'townshell.cfg']
includes = ['readline', 'pyreadline']
excludes = ['tkinter']
packages = ['readline', 'pyreadline']
zip_exclude_packages = []
icon = "Pictures\\TownShell.ico"
targetName = "TownShell.exe"
target_name_msi = "TownShell_installer.msi"

shortcut_table = [
    ("DesktopShortcut",        # Shortcut
     "DesktopFolder",          # Directory_
     "TownShell",           # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]TownShell.exe",# Target
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     None,                     # Icon
     None,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     ),
    ]

msi_data = {"Shortcut": shortcut_table}

setup(
    name = 'TownShell',
    version = '0.2',
    description = 'For Townscaper, a command line shell providing additional keyboard shortcuts and tools to manipulate .scape files',
    author = 'MokoJ',
    author_email = 'mokoj.triforce@gmail.com',
    options = {'build_exe': {'includes':includes,'excludes':excludes,'packages':packages,'include_files':includefiles, "zip_include_packages":'*', "zip_exclude_packages":zip_exclude_packages, 'silent':True},
    'bdist_msi': {'data': msi_data, "target_name": target_name_msi}}, 
    executables = [Executable(r'bin\Town_table.py', targetName = targetName, icon=icon)]
)
