# Grundschutz++ Compliance Dashboard

A Streamlit-based dashboard for managing and tracking compliance with the BSI Grundschutz++ framework.

## Features

- Interactive dashboard with status tracking
- Filter controls by group, class, and status
- Visual progress tracking
- SQLite database for persistent storage
- Reset functionality for database management

## Prerequisites

- Python 3.8+
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/yourusername/grundschutz-dashboard.git](https://github.com/yourusername/grundschutz-dashboard.git)
   cd grundschutz-dashboard

2.  Install the required packages:
    ```bash
    pip install -r requirements.txt

## Usage
1. Run the dashboard:
    ```bash
    streamlit run Dashboard.py

2. Access the dashboard in your web browser at:
    http://localhost:8501

## Data Files
Place the following files in the project root:
- Grundschutz++-Kompendium.json - The main data file
- grundschutz_status.db - SQLite database (will be created automatically)

## Features

- Dashboard: Overview of compliance status
- Filters: Filter controls by group, class, and status
- Search: Search for specific controls
- Status Tracking: Mark controls as "Erfüllt", "Nicht erfüllt", or "Entbehrlich"
- Notes: Add notes to controls
- Reset: Option to reset the database

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Reporting Issues

If you find any issues, please report them using the [issue tracker](https://github.com/yourusername/grundschutz-dashboard/issues).
