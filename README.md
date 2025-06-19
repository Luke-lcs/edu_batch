# Agenda Edu Batch Handout Sender

A command-line tool designed to automate sending personalized handouts with multiple attachments to students via the Agenda Edu API. This script is ideal for schools or educational institutions that need to distribute individualized reports, grades, or other documents efficiently.

## Key Features

- **Bulk Sending**: Sends handouts to a list of students identified by their attachment filenames.
- **Personalized Attachments**: Each student receives a unique attachment named with their specific student ID (e.g., `12345.pdf`).
- **Common Attachments**: Include one or more common files (from an `additional_files` directory) with every handout sent.
- **Optional Cover Image**: Add a cover image to make your handouts more engaging.
- **Interactive CLI**: An easy-to-use command-line interface guides the user through providing credentials, handout titles, descriptions, and other settings.
- **Robust Token Management**: Automatically handles OAuth 2.0 authentication (`client_credentials` grant type) and proactively renews the access token before it expires.
- **Detailed Logging**: Logs all successful and failed operations into easily readable `.csv` files (`Comunicados Enviados.csv` and `Erros.csv`).
- **Modular and Extensible**: The project is structured into logical modules (API client, services, file management, user interaction) for better maintainability and future expansion.

## Prerequisites

- Python 3.8+
- `requests` library

## Setup & Installation

1.  **Clone the repository**

2.  **Install dependencies:**
    This project requires the `requests` library. You can install it using pip.


3.  **Create the required directory structure:**
    The script requires a specific directory structure in the project's root folder. The script will create these directories if they don't exist, but you will need to populate them with your files.

    ```
    .
    ├── attachment_files/
    ├── cover_image/
    ├── additional_files/
    ├── api_auth.py
    ├── api_client.py
    ├── config.py
    ├── file_manager.py
    ├── handout_service.py
    ├── main.py
    └── user_interaction.py
    ```

## Usage

1.  **Populate Directories**:
    - **`attachment_files/`**: Place all student-specific attachments here. Each file **must be named** with the corresponding student's ID (e.g., `12345.pdf`, `54321.jpg`). The student list is generated from the files in this directory.
    - **`cover_image/`**: Place **one** cover image file here (e.g., `.jpg`, `.png`). If multiple images are present, the script will use the first one it finds. This is optional; if the directory is empty, no cover image will be sent.
    - **`additional_files/`**: Place any files that should be attached to **every** handout (e.g., a school calendar, a general newsletter). This is also optional.

2.  **Run the script**:
    Execute the main script from your terminal:
    ```bash
    python main.py
    ```

3.  **Follow the On-Screen Prompts**:
    The script will interactively ask for:
    - Your Agenda Edu API credentials (`Client ID`, `Client Secret`, `X-School-Token`).
    - The title and description for the handout.
    - The handout category.
    - The target audience (students, responsibles, or both).
    - Final confirmation before starting the sending process.

4.  **Check the Logs**:
    After the script runs, two files will be created or updated in the root directory:
    - **`Comunicados Enviados.csv`**: Logs all successfully created and approved handouts, including Student ID, Student Name, and Handout ID.
    - **`Erros.csv`**: Logs any errors encountered for a specific student, such as "student not found", "failed to approve handout", or network errors.

## Configuration

The `config.py` file contains several constants that you can modify to change the script's behavior:

- `MAX_FILE_SIZE_BYTES`: Sets the maximum size for individual attachment files (defaults to 100MB).
- `API_RETRY_DELAY_SECONDS`: The delay (in seconds) between creating a handout and attempting to approve it. This can be increased if you encounter `404 Not Found` errors during approval, which may indicate a replication delay in the API's backend.
- `REQUEST_TIMEOUT_SECONDS`: The timeout (in seconds) for API requests. Can be increased if you face `Read timed out` errors on a slow network or with very large files.
- `VALID_ATTACHMENT_EXTENSIONS` / `VALID_COVER_IMAGE_EXTENSIONS`: Tuples of allowed file extensions.

## Contributing

Contributions are welcome! If you have suggestions for improvements or find a bug, please feel free to open an issue or submit a pull request.

**Copyright (C) 2025 Lucas Monteiro**
