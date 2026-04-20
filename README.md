# lms-cuonlineedu
Automation program built for LMS Chandigarh University

```
Website: https://lms.cuonlineedu.in
```

## Overview

This project provides a Python-based automation solution to interact with the CU Online LMS API. It allows users to:

- Authenticate with their LMS credentials
- Retrieve course subjects, modules, and content
- Fetch and display learning progress
- Automatically mark content as complete
- Interactive CLI for easy navigation through course structure

## Features

- **Authentication**: Secure login using LMS credentials via environment variables
- **Course Navigation**: Browse subjects, modules, and content interactively
- **Progress Tracking**: View current progress for all course content
- **Auto-Completion**: Mark content as complete via API integration
- **Error Handling**: Robust error handling for API failures and network issues
- **Progress Visualization**: ASCII progress bars for visual feedback

## Project Structure

```
LMS/
├── main.py    # Improved version with OOP design and CLI
├── README.md             # This file
└── requirements.txt      # Python dependencies
```

## Requirements

- Python 3.7+
- See `requirements.txt` for package dependencies

## Installation

1. **Clone or download the repository**

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**

   Create a `.env` file in the LMS directory with your credentials:
   ```
   LMS_USERNAME=your_username
   LMS_PASSWORD=your_password
   ```

   **Note**: Never commit the `.env` file to version control. Add it to `.gitignore`.

## Usage

### Running the Application

Use the improved version (v2) for better features and structure:

```bash
python main.py
```

### Interactive Menu

The CLI will guide you through:

1. **Login** - Authenticates using credentials from `.env`
2. **Select Subject** - Choose from available course subjects
3. **Select Module** - Pick a module/chapter from the subject
4. **View Content** - Display all content with progress status
5. **Mark Content** - Complete content items via the API

Example output:
```
═══════════════════════════════════════════════════
  Select a Subject
═══════════════════════════════════════════════════
  [1] Python Basics
  [2] Advanced Python
  [3] Web Development
═══════════════════════════════════════════════════
Select (1-3): 1
```

## Configuration

### Environment Variables

Required environment variables in `.env`:

```
LMS_USERNAME=your_lms_username
LMS_PASSWORD=your_lms_password
```

## Contributing

When contributing to this project:

1. Test with the v2 version for any new features
2. Follow the existing class-based architecture
3. Add error handling for new API calls
4. Update this README with new features
5. Keep credentials secure (use `.env` files)

## License

This project is part of a private scripts collection.

## Support

For issues or questions, please refer to the inline code documentation or check the error messages provided by the CLI.
