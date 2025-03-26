from cx_Freeze import setup, Executable
import os

# Function to collect files in static and templates folder
def include_folder(folder):
    file_list = []
    for dirpath, _, files in os.walk(folder):
        for filename in files:
            # Append as a tuple of (source path, destination path)
            source = os.path.join(dirpath, filename)
            destination = os.path.join(dirpath, filename)
            file_list.append((source, destination))
    return file_list

# Include static and templates folders
include_files = include_folder('templates') + include_folder('static')

# Add any packages your app needs (Flask, Pandas, MySQL, etc.)
packages = [
    'flask', 'flask_wtf', 'wtforms', 'flask_login', 'mysql.connector',
    'base64', 'pandas', 'io', 'jinja2', 'werkzeug'
]

# Setup script for Cx_Freeze
setup(
    name="My Flask App",
    version="1.0",
    description="My Flask Application",
    options={
        'build_exe': {
            'packages': packages,
            'include_files': include_files,
            'excludes': [],  # Any modules to exclude, if necessary
        }
    },
    executables=[Executable('app.py')]
)
