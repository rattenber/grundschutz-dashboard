import streamlit as st
import json
import sqlite3
import os
import pandas as pd
import plotly.express as px
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('grundschutz_status.db')
    c = conn.cursor()
    
    # Create control_status table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS control_status (
            control_id TEXT PRIMARY KEY,
            status TEXT,
            notes TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if changed_by column exists, if not add it
    c.execute("PRAGMA table_info(control_status)")
    columns = [column[1] for column in c.fetchall()]
    if 'changed_by' not in columns:
        c.execute('ALTER TABLE control_status ADD COLUMN changed_by TEXT')
    
    # Create users table for name suggestions
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Enable foreign key constraints
    c.execute('PRAGMA foreign_keys = ON')
    conn.commit()
    return conn

def reset_database():
    """Reset all entries in the database"""
    c = db_conn.cursor()
    c.execute('DELETE FROM control_status')
    db_conn.commit()
    st.sidebar.success("Datenbank wurde zurückgesetzt!")
    st.rerun()

# Initialize database
db_conn = init_db()

# Now set page config
st.set_page_config(
    page_title="Grundschutz++ Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set theme configuration
st.session_state.setdefault('dark_mode', False)

# Custom CSS
st.markdown("""
    <style>
        .control-card {
            background-color: #ffffff;
            border-radius: 0.5rem;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            border: 1px solid #e9ecef;
        }
        .status-card {
            background-color: #f8f9fa;
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
            border-left: 4px solid #6c757d;
        }
        .status-erfuellt {
            border-left-color: #28a745 !important;
            background-color: #e8f5e9 !important;
        }
        .status-nicht-erfuellt {
            border-left-color: #dc3545 !important;
            background-color: #ffebee !important;
        }
        .status-entbehrlich {
            border-left-color: #ffc107 !important;
            background-color: #fff8e1 !important;
        }
        .status-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        .status-badge {
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .erfuellt-badge {
            background-color: #28a745;
            color: white;
        }
        .nicht-erfuellt-badge {
            background-color: #dc3545;
            color: white;
        }
        .entbehrlich-badge {
            background-color: #ffc107;
            color: #212529;
        }
        .notes-field {
            margin-top: 0.5rem;
            width: 100%;
        }
        .stRadio > div {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        .stRadio > div > label {
            margin: 0;
            padding: 0.5rem 1rem;
            border: 1px solid #dee2e6;
            border-radius: 0.25rem;
            background-color: #f8f9fa;
            cursor: pointer;
        }
        .stRadio > div > label:hover {
            background-color: #e9ecef;
        }
        .stRadio > div > label[data-baseweb="radio"] {
            margin: 0;
        }
        .stButton>button {
    background-color: #dc3545;
    color: white;
    border: 1px solid #dc3545;
    margin: 5px 0;
}
.stButton>button:hover {
    background-color: #c82333;
    border-color: #bd2130;
}
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        with open('Grundschutz++-Kompendium.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def get_control_status(control_id: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Get the status, notes, and name of the person who last changed the control
    Returns: (status, notes, changed_by)
    """
    c = db_conn.cursor()
    c.execute('SELECT status, notes, changed_by FROM control_status WHERE control_id = ?', (control_id,))
    result = c.fetchone()
    if result:
        # Handle potential None values in the database
        return (result[0] if result[0] else None, 
                result[1] if result[1] else None,
                result[2] if len(result) > 2 and result[2] else None)
    return (None, None, None)

def get_previous_users() -> List[str]:
    """Get a list of previously used user names, most recent first"""
    c = db_conn.cursor()
    c.execute('''
        SELECT name FROM users 
        ORDER BY last_used DESC
        LIMIT 10
    ''')
    return [row[0] for row in c.fetchall()]

def save_user_name(name: str) -> None:
    """Save or update a user name with current timestamp"""
    c = db_conn.cursor()
    c.execute('''
        INSERT INTO users (name, last_used) 
        VALUES (?, CURRENT_TIMESTAMP)
        ON CONFLICT(name) DO UPDATE SET last_used = CURRENT_TIMESTAMP
    ''', (name,))
    db_conn.commit()

def save_control_status(control_id: str, status: str, notes: str = "", changed_by: str = "") -> None:
    """Save control status with the name of the person making the change"""
    c = db_conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO control_status 
        (control_id, status, notes, changed_by, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (control_id, status, notes, changed_by))
    db_conn.commit()
    
    # Save the user name for future suggestions
    if changed_by:
        save_user_name(changed_by)

def process_data(data: Dict) -> Dict:
    if not data:
        return {}
    
    catalog = data.get('catalog', {})
    groups = catalog.get('groups', [])
    all_controls = []
    
    # Create a dictionary to store all parameters by ID
    parameters = {}
    
    # First pass: collect all parameters
    def collect_params(control):
        for param in control.get('params', []):
            param_id = param.get('id')
            if param_id and 'label' in param:
                parameters[param_id] = param['label']
    
    # Collect parameters from all controls
    for group in groups:
        # Process group-level controls
        for control in group.get('controls', []):
            collect_params(control)
            
        # Process subgroup controls
        for subgroup in group.get('groups', []):
            for control in subgroup.get('controls', []):
                collect_params(control)
    
    # Function to process a single control with parameter replacement
    def process_control(control, group_data, subgroup_data=None):
        statement = next((part for part in control.get('parts', []) 
                        if part.get('name') == 'statement'), {})
        guidance = next((part for part in control.get('parts', []) 
                       if part.get('name') == 'guidance'), {})
        
        # Process statement to replace parameter placeholders
        statement_text = statement.get('prose', '')
        if '{{' in statement_text and '}}' in statement_text:
            import re
            param_pattern = r'\{\{\s*insert:\s*param,\s*([^}]+)\s*\}\}'
            
            def replace_param(match):
                param_id = match.group(1).strip()
                # If parameter not found, show the ID in brackets
                return parameters.get(param_id, f'[{param_id}]')
            
            statement_text = re.sub(param_pattern, replace_param, statement_text)
        
        control_data = {
            'id': control.get('id', ''),
            'class': control.get('class', ''),
            'title': control.get('title', ''),
            'effort_level': next((prop['value'] for prop in control.get('props', []) 
                                if prop.get('name') == 'effort_level'), 'N/A'),
            'statement': statement_text,
            'guidance': guidance.get('prose', ''),
            'group_id': group_data.get('id', ''),
            'group_title': group_data.get('title', ''),
            'type': 'group_control'
        }
        
        if subgroup_data:
            control_data.update({
                'subgroup_id': subgroup_data.get('id', ''),
                'subgroup_title': subgroup_data.get('title', ''),
                'type': 'subgroup_control'
            })
            
        return control_data
    
    # Process all controls with parameter replacement
    for group in groups:
        # Process group-level controls
        for control in group.get('controls', []):
            control_data = process_control(control, group)
            all_controls.append(control_data)
            
        # Process subgroup controls
        for subgroup in group.get('groups', []):
            for control in subgroup.get('controls', []):
                control_data = process_control(control, group, subgroup)
                all_controls.append(control_data)
    
    return {
        'groups': groups,
        'all_controls': all_controls,
        'total_controls': len(all_controls),
        'total_groups': len(groups),
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def display_control_status(control_id: str) -> None:
    # Get current status, notes, and who last changed it
    status, notes, last_changed_by = get_control_status(control_id)
    
    # Create a form to handle the submission
    with st.form(key=f'form_{control_id}'):
        # Show who last changed this control (if any)
        if last_changed_by:
            st.info(f"👤 Zuletzt geändert von: {last_changed_by}")
        
        # Name input section - make it very visible
        st.markdown("### 👤 Verantwortliche Person")
        
        # Get previous users for suggestions
        previous_users = get_previous_users()
        
        # If we have a last_changed_by, put it at the top of the suggestions
        if last_changed_by and last_changed_by not in previous_users:
            previous_users.insert(0, last_changed_by)
        
        # Create a selectbox with previous users as suggestions
        if previous_users:
            selected_name = st.selectbox(
                "Aus vorherigen Namen auswählen",
                options=[""] + previous_users,
                format_func=lambda x: x if x else "-- Bitte auswählen --",
                key=f"{control_id}_name_select"
            )
        else:
            selected_name = ""
        
        # Text input for new names - use the selected name as the default value
        user_name = st.text_input(
            "Name der verantwortlichen Person",
            value=selected_name,
            key=f"{control_id}_name_input",
            placeholder="Vorname Nachname"
        )
        
        # If a name is selected from the dropdown, use it as the user_name
        if selected_name and selected_name.strip():
            user_name = selected_name
        
        st.markdown("---")
        
        # Notes section - always visible
        st.markdown("### 📝 Bemerkungen")
        
        # Show different placeholder based on status
        if status in ["erfuellt", "entbehrlich"]:
            placeholder = "Bitte machen Sie Angaben zum Speicherort der Unterlagen, z.B. Links, Pfade usw."
            notes_text = st.text_area(
                "Bemerkungen (erforderlich)",
                value=notes or "",
                key=f"{control_id}_notes",
                placeholder=placeholder,
                help="Pflichtfeld für 'Erfüllt' und 'Entbehrlich'"
            )
        else:
            placeholder = "Optionale Notizen..."
            notes_text = st.text_area(
                "Bemerkungen (optional)",
                value=notes or "",
                key=f"{control_id}_notes",
                placeholder=placeholder
            )
            
        st.markdown("---")
        
        # Status selection section
        st.markdown("### 📊 Status auswählen")
        
        # Default to empty string if no status is set
        status_index = 0  # Default to first option
        if status == "erfuellt":
            status_index = 1
        elif status == "nicht_erfuellt":
            status_index = 2
        elif status == "entbehrlich":
            status_index = 3
        
        # Use radio button for status selection
        status_options = ["Keine Auswahl", "Erfüllt", "Nicht erfüllt", "Entbehrlich"]
        selected_status = st.radio(
            "Status:",
            options=status_options,
            index=status_index,
            key=f"{control_id}_status",
            horizontal=True
        )
        
        # Map the selected status to our internal values
        new_status = None
        if selected_status == "Erfüllt":
            new_status = "erfuellt"
        elif selected_status == "Nicht erfüllt":
            new_status = "nicht_erfuellt"
        elif selected_status == "Entbehrlich":
            new_status = "entbehrlich"
        
        # Submit button
        submit_button = st.form_submit_button(
            "Speichern",
            type="primary" if new_status and user_name.strip() else "secondary"
        )
        
        # Handle form submission
        if submit_button and new_status:
            if not user_name.strip():
                st.error("Bitte geben Sie Ihren Namen an.")
            elif new_status in ["erfuellt", "entbehrlich"] and not notes_text.strip():
                st.error("Bitte geben Sie eine Begründung an.")
            else:
                save_control_status(control_id, new_status, notes_text, user_name.strip())
                st.success("Status erfolgreich gespeichert!"
                           f"\n\n**Status:** {selected_status}"
                           f"\n**Verantwortlich:** {user_name.strip()}")
                st.rerun()
    
    # This section was removed as it was a duplicate of the notes section inside the form
    
    # Save button
    save_button = st.button(
        "Speichern",
        key=f"{control_id}_save_button",
        type="primary" if new_status else "secondary",
        disabled=not new_status or (new_status in ["erfuellt", "entbehrlich"] and not notes_text.strip())
    )
    
    # Save the status and notes if the save button is clicked
    if save_button and new_status:
        if not user_name.strip():
            st.error("Bitte geben Sie Ihren Namen an.")
        else:
            save_control_status(control_id, new_status, notes_text, user_name.strip())
            # Show success message
            st.success("Status erfolgreich gespeichert!")
            # Force a rerun to update the UI
            st.rerun()

def get_status_badge(status: Optional[str]) -> str:
    if status == "erfuellt":
        return '<span class="status-badge erfuellt-badge">Erfüllt</span>'
    elif status == "nicht_erfuellt":
        return '<span class="status-badge nicht-erfuellt-badge">Nicht erfüllt</span>'
    elif status == "entbehrlich":
        return '<span class="status-badge entbehrlich-badge">Entbehrlich</span>'
    return ""

def display_control(control: Dict) -> None:
    status, _, _ = get_control_status(control['id'])
    status_class = f"status-{status.replace('_', '-')}" if status else ""
    
    # Create a card for the control
    with st.container():
        st.markdown("---")
        st.subheader(f"{control.get('id', '')} - {control.get('title', '')}")
        
        # Create columns for the metadata
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption("Gruppe")
            st.text(control.get('group_title', 'N/A'))
            
        with col2:
            st.caption("Klasse")
            st.text(control.get('class', 'N/A'))
            
        with col3:
            st.caption("Aufwand")
            st.text(control.get('effort_level', 'N/A'))
        
        # Add subgroup if it exists
        if control.get('subgroup_title'):
            st.caption("Untergruppe")
            st.text(control.get('subgroup_title', 'N/A'))
        
        st.markdown("---")
    
    # Display content in two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Anforderung")
        statement = control.get('statement', 'Keine Anforderung vorhanden.')
        
        # Process parameter placeholders
        if '{{' in statement and '}}' in statement:
            # Extract all parameter placeholders
            import re
            param_pattern = r'\{\{\s*insert:\s*param,\s*([^}]+)\s*\}\}'
            
            # Replace each parameter with a styled version
            def replace_param(match):
                param_name = match.group(1).strip()
                return f'<span style="background-color: #f0f0f0; padding: 0.2em 0.4em; border-radius: 4px; font-family: monospace;">[{param_name}]</span>'
            
            # Apply the replacement
            statement = re.sub(param_pattern, replace_param, statement)
        
        st.markdown(statement, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Hinweise")
        st.markdown(control.get('guidance', 'Keine Hinweise vorhanden.'))
    
    # Status selection
    with st.expander("Status setzen", expanded=status is not None):
        display_control_status(control['id'])
    
    st.markdown("---")

def show_status_dashboard():
    st.header("Compliance Status Dashboard")
    
    # Debug info
    st.sidebar.write("Debug Info:")
    st.sidebar.write(f"Database file exists: {os.path.exists('grundschutz_status.db')}")
    
    # Check if table exists
    c = db_conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='control_status'")
    table_exists = c.fetchone() is not None
    st.sidebar.write(f"Table exists: {table_exists}")
    
    if not table_exists:
        st.warning("No status data available. Please set status for some controls first.")
        return
    
    # Get status counts
    c.execute('''
        SELECT 
            status,
            COUNT(*) as count
        FROM control_status
        GROUP BY status
    ''')
    status_data = c.fetchall()
    
    # Display metrics
    if status_data:
        total = sum(count for _, count in status_data)
        cols = st.columns(5)
        
        with cols[0]:
            st.metric("Total", total)
        
        status_map = {
            'erfuellt': ('Erfüllt', 1),
            'nicht_erfuellt': ('Nicht erfüllt', 2),
            'entbehrlich': ('Entbehrlich', 3)
        }
        
        for status, count in status_data:
            if status in status_map:
                label, idx = status_map[status]
                with cols[idx]:
                    st.metric(label, f"{count} ({count/total*100:.1f}%)" if total > 0 else "0")
    
    # Create pie chart
    if status_data:
        df = pd.DataFrame(status_data, columns=['Status', 'Count'])
        df['Status'] = df['Status'].map({
            'erfuellt': 'Erfüllt',
            'nicht_erfuellt': 'Nicht erfüllt',
            'entbehrlich': 'Entbehrlich'
        })
        
        fig = px.pie(
            df,
            values='Count',
            names='Status',
            title='Verteilung der Kontrollen nach Status',
            color='Status',
            color_discrete_map={
                'Erfüllt': '#28a745',
                'Nicht erfüllt': '#dc3545',
                'Entbehrlich': '#ffc107'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Show recent updates
    st.subheader("Letzte Aktualisierungen")
    c.execute('''
        SELECT 
            control_id,
            status,
            notes,
            updated_at
        FROM control_status
        ORDER BY updated_at DESC
        LIMIT 10
    ''')
    
    recent_updates = c.fetchall()
    
    if recent_updates:
        for update in recent_updates:
            control_id, status, notes, updated_at = update
            with st.expander(f"Kontrolle {control_id} - {status}"):
                st.write(f"**Status:** {status}")
                st.write(f"**Aktualisiert am:** {updated_at}")
                if notes:
                    st.write("**Notizen:**")
                    st.write(notes)
    else:
        st.info("Keine Status-Updates gefunden.")

def main():
    st.title("Grundschutz++ Compliance Dashboard")
    
    # Load data
    with st.spinner("Lade Daten..."):
        data = load_data()
    
    if not data:
        st.error("""
        Fehler beim Laden der Daten. Bitte überprüfen Sie:
        1. Die Datei 'Grundschutz++-Kompendium.json' existiert im gleichen Verzeichnis
        2. Die Datei ist eine gültige JSON-Datei
        3. Sie haben Leseberechtigungen für die Datei
        """)
        return
    
    # Process data
    try:
        processed_data = process_data(data)
    except Exception as e:
        st.error(f"Fehler bei der Datenverarbeitung: {str(e)}")
        return
    
    # Dark mode toggle
    dark_mode = st.sidebar.toggle('Dark Mode', value=st.session_state.get('dark_mode', False))
    st.session_state['dark_mode'] = dark_mode
    
    # Apply dark mode if enabled
    if dark_mode:
        st.markdown("""
            <style>
                /* Base dark theme */
                .stApp {
                    background-color: #0E1117;
                    color: #E0E0E0;
                }
                
                /* Text colors */
                .st-bw, .st-ck, .st-cm, .st-dl, .st-bh, .st-bj, .st-bk, .st-bl, .st-bm {
                    color: #E0E0E0 !important;
                }
                
                /* Radio buttons */
                .stRadio > div > div {
                    background-color: #2A2D35;
                    border-radius: 6px;
                    padding: 8px;
                    border: 1px solid #444;
                }
                .stRadio > div > label > div {
                    padding: 8px 16px;
                    border-radius: 4px;
                    transition: all 0.2s;
                    margin: 4px 0;
                }
                .stRadio > div > label > div:hover {
                    background-color: #3A3D45;
                }
                .stRadio > div > label > div[data-testid="stMarkdownContainer"] > p {
                    color: #FFFFFF !important;
                    font-weight: 500;
                    margin: 0;
                }
                /* Selected radio button */
                .stRadio > div > label > div[data-baseweb="radio"] {
                    background-color: #3A3D45;
                }
                /* Checked state */
                .stRadio > div > label > div[data-baseweb="radio"]:has(input:checked) {
                    background-color: #3A3D45;
                    border-left: 3px solid #4CAF50;
                }
                
                /* Cards and containers */
                .st-emotion-cache-1v0mbdj, .control-card, .status-card {
                    background-color: #1E1E1E !important;
                    border-color: #333842 !important;
                    color: #E0E0E0 !important;
                }
                
                /* Status badges */
                .status-erfuellt { border-left-color: #4CAF50 !important; background-color: #1B5E20 !important; }
                .status-nicht-erfuellt { border-left-color: #F44336 !important; background-color: #B71C1C !important; }
                .status-entbehrlich { border-left-color: #FFC107 !important; background-color: #FF8F00 !important; color: #212121 !important; }
                
                /* Input fields */
                .stTextInput > div > div > input, 
                .stSelectbox > div > div > div > div {
                    background-color: #1E1E1E !important;
                    color: #E0E0E0 !important;
                    border-color: #555 !important;
                }
                
                /* Sidebar */
                section[data-testid="stSidebar"] {
                    background-color: #1A1A1A !important;
                }
                section[data-testid="stSidebar"] * {
                    color: #E0E0E0 !important;
                }
                section[data-testid="stSidebar"] .stSelectbox > div > div > div,
                section[data-testid="stSidebar"] .stTextInput > div > div > input,
                section[data-testid="stSidebar"] .stRadio > div > div,
                section[data-testid="stSidebar"] .stCheckbox > div > div,
                section[data-testid="stSidebar"] .stButton > button {
                    background-color: #2A2D35 !important;
                    border-color: #444 !important;
                }
                
                /* Tabs */
                .stTabs [data-baseweb="tab"] {
                    background-color: #1E1E1E;
                    color: #E0E0E0;
                }
                .stTabs [aria-selected="true"] {
                    background-color: #2A2D35;
                    color: #4CAF50 !important;
                    border-bottom: 2px solid #4CAF50;
                }
            </style>
        """, unsafe_allow_html=True)
    
    # Sidebar filters
    st.sidebar.header("Filter")
    
    # Group filter
    group_titles = sorted(list(set(c.get('group_title', '') for c in processed_data['all_controls'] if c.get('group_title'))))
    selected_group = st.sidebar.selectbox(
        "Nach Gruppe filtern",
        options=["Alle"] + group_titles
    )
    
    # Class filter
    classes = sorted(list(set(c.get('class', '') for c in processed_data['all_controls'] if c.get('class'))))
    selected_class = st.sidebar.multiselect(
        "Nach Klasse filtern",
        options=classes,
        default=[]
    )
    
    # Status filter
    status_options = ["Alle", "Erfüllt", "Nicht erfüllt", "Entbehrlich", "Ohne Status"]
    selected_status = st.sidebar.selectbox(
        "Nach Status filtern",
        options=status_options
    )
    
    # Effort level filter
    effort_levels = sorted(list(set(
        c.get('effort_level') 
        for c in processed_data['all_controls'] 
        if c.get('effort_level')
    )))
    
    if effort_levels:
        selected_efforts = st.sidebar.multiselect(
            "Nach Aufwand filtern",
            options=effort_levels,
            default=[]
        )
    else:
        selected_efforts = []
    
    # Search
    search_term = st.sidebar.text_input("Suche", "", key="search_input").lower()

    # Apply filters
    filtered_controls = processed_data['all_controls']
    
    if selected_group != "Alle":
        filtered_controls = [c for c in filtered_controls if c.get('group_title') == selected_group]
    
    if selected_class:
        filtered_controls = [c for c in filtered_controls if c.get('class') in selected_class]
    
    if selected_efforts:
        filtered_controls = [c for c in filtered_controls if c.get('effort_level') in selected_efforts]
    
    if search_term:
        filtered_controls = [
            c for c in filtered_controls
            if (search_term in c.get('title', '').lower() or
                search_term in c.get('id', '').lower() or
                search_term in c.get('statement', '').lower() or
                search_term in c.get('guidance', '').lower())
        ]
    
    # Add export button after filters are applied
    st.sidebar.markdown("---")
    if st.sidebar.button("📊 Als CSV exportieren", key="export_button"):
        if filtered_controls:
            import pandas as pd
            from io import StringIO
            
            # Convert filtered controls to DataFrame
            df = pd.DataFrame(filtered_controls)
            
            # Get status and notes for each control
            status_notes = df['id'].apply(lambda x: get_control_status(x))
            
            # Add status and notes to the DataFrame
            df['status'] = status_notes.apply(lambda x: x[0] or 'Ohne Status')
            df['notes'] = status_notes.apply(lambda x: x[1] or '')
            
            # Add empty columns for additional fields
            df['Verantwortlich'] = ''
            df['Termin'] = ''
            df['Begründung'] = ''
            
            # Select and reorder columns for export with German headers
            column_mapping = {
                'id': 'ID',
                'title': 'Titel',
                'group_title': 'Gruppe',
                'subgroup_title': 'Untergruppe',
                'effort_level': 'Aufwand',
                'statement': 'Anforderung',
                'guidance': 'Hinweise',
                'class': 'Klasse',
                'status': 'Status',
                'Begründung': 'Begründung',
                'notes': 'Notizen',
                'Verantwortlich': 'Verantwortlich',
                'Termin': 'Termin'
            }
            
            # Ensure all required columns exist
            for col in column_mapping.keys():
                if col not in df.columns and col not in ['Begründung', 'Verantwortlich', 'Termin']:
                    df[col] = ''
            
            # Reorder and rename columns
            df = df[list(column_mapping.keys())].rename(columns=column_mapping)
            
            # Ensure all string columns are properly encoded
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.encode('utf-8').str.decode('utf-8')
            
            # Convert to CSV with proper encoding
            csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig', quotechar='"', quoting=1)
            
            # Create download button with explicit encoding
            st.sidebar.download_button(
                label="⬇️ CSV herunterladen",
                data=csv.encode('utf-8-sig'),
                file_name=f'grundschutz_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv; charset=utf-8-sig',
                key="download_button"
            )
        else:
            st.sidebar.warning("Keine Daten zum Exportieren vorhanden.")
    
    # Add reset button at the bottom
    st.sidebar.markdown("---")
    if st.sidebar.checkbox("Datenbank zurücksetzen", key="reset_checkbox"):
        if st.sidebar.button("⚠️ Bestätigen: Alle Daten löschen", 
                           key="reset_confirm_button",
                           type="primary", 
                           help="Klicken Sie hier, um alle Einträge zu löschen"):
            reset_database()
    
    # Apply status filter
    if selected_status != "Alle":
        status_map = {
            "Erfüllt": "erfuellt",
            "Nicht erfüllt": "nicht_erfuellt",
            "Entbehrlich": "entbehrlich"
        }
        if selected_status == "Ohne Status":
            filtered_controls = [c for c in filtered_controls if not get_control_status(c['id'])[0]]
        else:
            filtered_controls = [c for c in filtered_controls if get_control_status(c['id'])[0] == status_map[selected_status]]
    
    # Create tabs
    tab1, tab2 = st.tabs(["Übersicht", "Kontrollen"])
    
    with tab1:
        show_status_dashboard()
    
    with tab2:
        # Display metrics
        st.markdown("### Übersicht")
        total = len(processed_data['all_controls'])
        # Get all statuses in a single query for better performance
        statuses = {}
        for c in processed_data['all_controls']:
            status, _, _ = get_control_status(c['id'])
            statuses[c['id']] = status
        
        # Count statuses
        erfuellt = sum(1 for status in statuses.values() if status == "erfuellt")
        nicht_erfuellt = sum(1 for status in statuses.values() if status == "nicht_erfuellt")
        entbehrlich = sum(1 for status in statuses.values() if status == "entbehrlich")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Gesamt", total)
        with col2:
            st.metric("Erfüllt", f"{erfuellt} ({erfuellt/total*100:.1f}%)" if total > 0 else "0")
        with col3:
            st.metric("Nicht erfüllt", f"{nicht_erfuellt} ({nicht_erfuellt/total*100:.1f}%)" if total > 0 else "0")
        with col4:
            st.metric("Entbehrlich", f"{entbehrlich} ({entbehrlich/total*100:.1f}%)" if total > 0 else "0")
        
        # Display progress
        progress = (erfuellt + entbehrlich) / total if total > 0 else 0
        st.progress(progress)
        st.caption(f"Fortschritt: {progress*100:.1f}% abgeschlossen")
        
        # Display controls
        st.markdown(f"### Kontrollen ({len(filtered_controls)} von {len(processed_data['all_controls'])} angezeigt)")
        
        if not filtered_controls:
            st.warning("Keine Kontrollen gefunden, die den ausgewählten Filtern entsprechen.")
        else:
            for control in filtered_controls:
                display_control(control)

if __name__ == "__main__":
    main()