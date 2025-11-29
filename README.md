# Grundschutz++ Compliance Dashboard

A Streamlit-based dashboard for managing and tracking compliance with the BSI Grundschutz++ framework. This tool helps organizations implement and monitor their IT security measures according to the BSI Grundschutz methodology.

## ✨ Features

- **Interactive Dashboard**: Real-time status tracking and visual progress monitoring
- **Advanced Filtering**:
  - Filter by group, class, and status
  - Search functionality across all control details
  - Effort level filtering for better resource planning
- **Dark Mode**: Eye-friendly dark theme with optimized contrast for better readability
- **Data Management**:
  - SQLite database for persistent storage
  - Reset functionality for database management
  - CSV export with all control details
- **Comprehensive Control View**:
  - Detailed control information with parameter replacement
  - Status tracking (Erfüllt, Nicht erfüllt, Entbehrlich, Ohne Status)
  - Notes and justification fields for each control
  - Responsible person and deadline tracking

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Modern web browser (Chrome, Firefox, Edge, or Safari)

## Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/yourusername/grundschutz-dashboard.git](https://github.com/yourusername/grundschutz-dashboard.git)
   cd grundschutz-dashboard

2.  Install the required packages:
    ```bash
    pip install -r requirements.txt

## 🖥️ Usage

1. Run the dashboard:
    ```bash
    streamlit run Dashboard.py
    ```

2. Access the dashboard in your web browser at:
    ```
    http://localhost:8501
    ```

### Key Features in Action

- **Dark Mode Toggle**: Switch between light and dark themes using the toggle in the sidebar
- **CSV Export**: Export filtered results to a CSV file with all control details
- **Status Management**: Update the status of controls and add notes directly in the interface
- **Responsive Design**: Works on both desktop and tablet devices

## 📂 Data Files

Place the following files in the project root:
- `Grundschutz++-Kompendium.json` - The main data file (required)
- `grundschutz_status.db` - SQLite database (will be created automatically)

## 🛠️ Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/grundschutz-dashboard.git
    cd grundschutz-dashboard
    ```

2. Create a virtual environment (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## 📊 Features in Detail

### Dashboard
- Real-time compliance status overview
- Visual progress indicators
- Quick access to filtered views

### Filters & Search
- **Group/Subgroup Filtering**: Navigate through the control hierarchy
- **Class Filtering**: Filter by control classes
- **Status Filtering**: View controls by their implementation status
- **Effort Level**: Filter by implementation effort
- **Full-text Search**: Search across all control fields

### Control Management
- **Status Updates**: Mark controls as complete, incomplete, or not applicable
- **Detailed Notes**: Add and track notes for each control
- **Responsible Person**: Assign team members to controls
- **Deadline Tracking**: Set and monitor implementation deadlines

### Data Management
- **CSV Export**: Export filtered results for reporting
- **Database Reset**: Reset the database when needed
- **Dark Mode**: Toggle between light and dark themes

## Data Source

This project uses data from the [BSI Stand der Technik Bibliothek](https://www.bsi.bund.de/EN/Topics/ITGrundschutz/ITGrundschutzStandards/Stand_der_Technik_Bibliothek/stand_der_technik_node.html) by the German Federal Office for Information Security (BSI).

### Original Data
- **Source**: [Grundschutz++-Kompendium.json](https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek/blob/main/Kompendien/Grundschutz%2B%2B-Kompendium/Grundschutz%2B%2B-Kompendium.json)
- **License**: [BSI Open Data License](https://www.bsi.bund.de/EN/Service/OpenData/OpenData_License/open_data_license_node.html)
- **Copyright**: © Bundesamt für Sicherheit in der Informationstechnik

### Data Usage
The data is used in accordance with the BSI's open data policy. Please refer to the [BSI Open Data](https://www.bsi.bund.de/EN/Service/OpenData/open_data_node.html) page for more information about usage rights and restrictions.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

1. **Report Bugs**: Use the [issue tracker](https://github.com/yourusername/grundschutz-dashboard/issues) to report bugs or suggest features
2. **Submit Fixes**: Submit pull requests for any issues you'd like to address
3. **Improve Documentation**: Help us improve the documentation and add examples
4. **Spread the Word**: Star the repository and tell others about this project

### Development Setup

1. Fork and clone the repository
2. Set up a virtual environment
3. Install development dependencies:
    ```bash
    pip install -r requirements-dev.txt
    ```
4. Make your changes and run tests
5. Submit a pull request with a clear description of your changes

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- BSI (Bundesamt für Sicherheit in der Informationstechnik) for the Grundschutz framework
- The Streamlit team for the amazing dashboard framework
- All contributors who have helped improve this project
