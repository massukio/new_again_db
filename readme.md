# New Again Project

## Overview

This project is a car plate information management system built using Python and PyQt5. It allows users to add, view, update, and delete car plate information, including phone numbers and notes. The data is stored in an SQLite database.

## Features

- **Add Car Plate Information**: Add new car plate information with phone numbers and notes.
- **View All Information**: View all stored car plate information in a table format.
- **Update Information**: Update existing car plate information.
- **Delete Information**: Delete car plate information.
- **Search Functionality**: Search for car plate information by plate number or phone number.
- **Database Backup**: Backup the database to a specified location.

## Requirements

- Python 3.8+
- PyQt5
- SQLite3

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/new_again.git
    cd new_again
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install .
    ```
    or
    ```sh
    pip install -r requirement.txt
    ```

## Usage

1. Run the application (it will automatically initialize the database if needed):
    ```sh
    python start.py
    ```

## Building the Executable

To build the application into a standalone executable using PyInstaller, follow these steps:

1. Install PyInstaller:
    ```sh
    pip install pyinstaller
    ```

2. Create a PyInstaller spec file:
    ```sh
    pyinstaller --name new_again_db --onefile --noconsole start.py
    ```

3. Build the executable:
    ```sh
    pyinstaller new_again_db.spec
    ```

The executable will be created in the dist directory.

## Project Structure

- core: Contains the main application logic and core components.
  - `__init__.py`: Makes the directory a package.
  - `application.py`: Main application class.
  - `logger.py`: Configures logging for the application.
- ui: Contains UI components and handlers.
  - `__init__.py`: Makes the directory a package.
  - `add_plate_dialog.py`: Dialog for adding car plate information.
  - `main_ui.py`: Main UI setup for the application.
  - `table_view_handler.py`: Handles the table view operations.
- database: Contains database-related scripts.
  - `__init__.py`: Makes the directory a package.
  - `database.py`: Database operations.
  - `initialize_db.py`: Script to initialize the database.
- utils: Contains utility functions and helpers.
  - `__init__.py`: Makes the directory a package.
  - `helpers.py`: Utility functions.
- config: Contains configuration files and constants.
  - `__init__.py`: Makes the directory a package.
  - `constants.py`: Application constants.
- `designer/`: Contains UI design files.
  - `add.ui`: UI design for adding car plate information.
  - `new_again.ui`: Main window UI design.
- .vscode: Contains VS Code configuration files.
  - `settings.json`: VS Code settings.
  - `tasks.json`: VS Code tasks.
- start.py: Entry point for the application.
- `requirements.txt`: List of required packages.
- .gitignore: Git ignore file.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Author

Sukio Lin

## Acknowledgements

- PyQt5 Documentation
- SQLite Documentation
- Python Logging Documentation
- GitHub Copilot for assistance in code generation
- All contributors and users
