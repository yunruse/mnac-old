import os
import sys
from cx_Freeze import setup, Executable

PY_PATH = r'C:\Program Files (x86)\Python36-32'
os.environ['TCL_LIBRARY'] = PY_PATH + r'\tcl\tcl8.6'
os.environ['TK_LIBRARY'] = PY_PATH + r'\tcl\tk8.6'

options = {
    'build_exe': {    
        'packages': [
            'idna'
        ],
        'includes': [
            'numpy.core._methods',
            'numpy.lib.format',
        ],
        'include_files': [
            PY_PATH + r'\DLLs\tcl86t.dll',
            PY_PATH + r'\DLLs\tk86t.dll'
        ]
    },    
}

base = 'Win32GUI' if sys.platform == 'win32' else None    
executables = [Executable("MNAC/tk.py", base=base)]

setup(
    name = "MNAC",
    options = options,
    version = "1.3",
    description = 'Meta Noughts and Crosses by yunru.se',
    executables = executables
)
