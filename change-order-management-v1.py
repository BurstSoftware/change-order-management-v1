import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect("change_orders.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS change_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    description TEXT,
                    cost_impact REAL,
                    time_impact INTEGER,
                    status TEXT,
                    submitted_by TEXT,
                    submitted_date TEXT,
                    approved_by TEXT,
                    approved_date TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS project_budgets (
                    project_id TEXT PRIMARY KEY,
                    initial_budget REAL,
                    current_budget REAL
                )''')
    conn.commit()
    conn.close()

# Fetch change orders
def get_change_orders():
    conn = sqlite3.connect("change_orders.db")
    df = pd.read_sql_query("SELECT * FROM change_orders", conn)
    conn.close()
    return df

# Fetch project budget
def get_project_budget(project_id):
    conn = sqlite3.connect("change_orders.db")
    c = conn.cursor()
    c.execute("SELECT current_budget FROM project_budgets WHERE project_id = ?", (project_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

# Update project budget
def update_project_budget(project_id, cost_impact):
    conn = sqlite3.connect("change_orders.db")
    c = conn.cursor()
    current_budget = get_project_budget(project_id)
    new_budget = current_budget + cost_impact
    c.execute("UPDATE project_budgets SET current_budget = ? WHERE project_id = ?", (new_budget, project_id))
    conn.commit()
    conn.close()

# Add change order
def add_change_order(project_id, description, cost_impact, time_impact, submitted_by):
    conn = sqlite3.connect("change_orders.db")
    c = conn.cursor()
    submitted_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO change_orders (project_id, description, cost_impact, time_impact, status, submitted_by, submitted_date)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (project_id, description, cost_impact, time_impact, "Pending", submitted_by, submitted_date))
    conn.commit()
    conn.close()

# Approve change order
def approve_change_order(order_id, approved_by):
    conn = sqlite3.connect("change_orders.db")
    c = conn.cursor()
    approved_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''UPDATE change_orders SET status = ?, approved_by = ?, approved_date = ? WHERE id = ?''',
              ("Approved", approved_by, approved_date, order_id))
    # Update project budget
    c.execute("SELECT project_id, cost_impact FROM change_orders WHERE id = ?", (order_id,))
    project_id, cost_impact = c.fetchone()
    update_project_budget(project_id, cost_impact)
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Streamlit app
st.title("Change Order Management Tool")

# Sidebar for navigation
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Submit Change Order", "View Change Order Log", "Approve Change Orders"])

# Submit Change Order
if page == "Submit Change Order":
    st.header("Submit a Change Order")
    with st.form("change_order_form"):
        project_id = st.text_input("Project ID")
        description = st.text_area("Description of Change")
        cost_impact = st.number_input("Cost Impact ($)", min_value=0.0, step=100.0)
        time_impact = st.number_input("Time Impact (Days)", min_value=0, step=1)
        submitted_by = st.text_input("Submitted By")
        submit_button = st.form_submit_button("Submit Change Order")

        if submit_button:
            if project_id and description and submitted_by:
                add_change_order(project_id, description, cost_impact, time_impact, submitted_by)
                st.success("Change order submitted successfully!")
            else:
                st.error("Please fill in all required fields.")

# View Change Order Log
elif page == "View Change Order Log":
    st.header("Change Order Log")
    change_orders = get_change_orders()
    if not change_orders.empty:
        st.dataframe(change_orders)
        # Display current budget for a selected project
        project_id = st.selectbox("Select Project ID for Budget", change_orders["project_id"].unique())
        current_budget = get_project_budget(project_id)
        st.write(f"Current Budget for Project {project_id}: ${current_budget:,.2f}")
    else:
        st.write("No change orders found.")

# Approve Change Orders
elif page == "Approve Change Orders":
    st.header("Approve Change Orders")
    change_orders = get_change_orders()
    pending_orders = change_orders[change_orders["status"] == "Pending"]
    if not pending_orders.empty:
        order_id = st.selectbox("Select Change Order ID", pending_orders["id"])
        approved_by = st.text_input("Approved By")
        if st.button("Approve Change Order"):
            if approved_by:
                approve_change_order(order_id, approved_by)
                st.success("Change order approved successfully!")
            else:
                st.error("Please enter the approver's name.")
        st.dataframe(pending_orders)
    else:
        st.write("No pending change orders.")

# Notes for Integration
st.sidebar.markdown("""
### Integration Notes
- **Project Management Dashboard**: Budget updates can be synced by querying `project_budgets` table.
- **Client Portal**: Approvals can be exposed via a separate Streamlit app or API endpoint.
- **Reports**: Add export to PDF/Excel for logs using `pandas` or `plotly`.
""")
