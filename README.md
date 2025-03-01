<br />
<p align="center">
  <h3 align="center">Nginx Log Analyzer</h3>
  <p align="center">
    A Python-based tool for parsing and analyzing Nginx access logs.
    <br />
    <a href="https://github.com/therealalexmois/nginx-log-analyzer"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/therealalexmois/nginx-log-analyzer/issues">Report Bug</a>
    ·
    <a href="https://github.com/therealalexmois/nginx-log-analyzer/issues">Request Feature</a>
  </p>
</p>

---

<!-- TABLE OF CONTENTS -->
## 📖 Table of Contents

- [About the Project](#about-the-project)
  - [Features](#features)
  - [Built With](#built-with)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Configuration](#configuration)
- [Testing](#testing)
- [Development Guidelines](#development-guidelines)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

<!-- ABOUT THE PROJECT -->
## About The Project

Nginx Log Analyzer is a Python tool that parses, analyzes, and generates reports from Nginx access logs. It helps in monitoring request statistics and performance.

### Features

- ✅ Parses and processes Nginx access logs.
- ✅ Supports `.gz` compressed log files.
- ✅ Handles error thresholds for log parsing.
- ✅ Generates structured logs using `structlog`.
- ✅ Creates HTML reports from parsed log data.
- ✅ Configurable via a TOML file.

### Built With

- **Python 3.12**
- **Structlog** - For logging
- **pytest** - For testing
- **Ruff** - For linting
- **Make** - For automation

---

<!-- GETTING STARTED -->
## Getting Started

### Installation

1. **Clone the repository**:

```sh
  git clone https://github.com/your-username/nginx-log-analyzer.git
  cd nginx-log-analyzer
```

2. Create a virtual environment and install dependencies:

```sh
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
pip install -r requirements.txt
```

---

## Usage

Running the analyzer
To analyze logs and generate a report:

```sh
python -m src.nginx_log_analyzer.main --config=config.toml
```

Alternatively, using make:

```sh
make start --config=config.toml
```

---

## Configuration

The tool uses a TOML configuration file. Example:

```toml
log_dir = "logs"
report_dir = "reports"
report_size = 1000
error_threshold = 0.1
log_file = "nginx_log_analyzer.log"
```

📝 Example Log Format

This tool expects logs in the Nginx access.log format:

```sh
1.1.1.1 - - [01/Jan/2024:10:00:00 +0000] "GET /api/data HTTP/1.1" 200 123 "-" "-" "-" "-" "-" 0.150
```

---

<!-- TESTING -->

## Testing
Run the tests using pytest:

```sh
pytest
```

To check for linting and formatting issues:

```sh
ruff check
```

---

<!-- DEVELOPMENT -->

## Development Guidelines

- Use conventional commits for structured commit messages.
- Keep sys.exit() calls only in main.py for testability.
- Parsing functions should be generators for better efficiency.
- Use structlog for logging instead of print().
- **Error Handling**: Ensure error rates are checked only once at the end of parsing.

---

<!-- CONTRIBUTING -->
## Contributing
Contributions are welcome! If you have suggestions for improvements, please:

1. Fork the project.
2. Create a feature branch (git checkout -b feature/AmazingFeature).
3. Commit your changes (git commit -m 'feat: Add some AmazingFeature').
4. Push to the branch (git push origin feature/AmazingFeature).
5. Open a Pull Request.

---

<!-- LICENSE -->

## License

Distributed under the MIT License. See LICENSE for more information.

<!-- CONTACT -->
## Contact
GitHub: therealalexmois
Email: alex.mois.developer@gmail.com
