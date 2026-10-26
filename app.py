"""
app.py
Construction Material Inventory & Structural Cost Estimation System
Streamlit Interactive Dashboard Application
"""

import os
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configure Streamlit page
st.set_page_config(
    page_title="Construction Material & Cost Estimator",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database path resolution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, "construction_cost_estimator.db")

# Ensure database exists
if not os.path.exists(DB_PATH):
    import db_manager
    db_manager.init_database(DB_PATH)
    db_manager.seed_sample_data(DB_PATH)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def run_query(sql, params=()):
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)

def execute_dml(sql, params=()):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount, None
    except sqlite3.Error as e:
        return 0, str(e)

# Helper for Indian Rupee Formatting
def format_inr(val):
    if pd.isna(val) or val is None:
        return "₹0.00"
    return f"₹{val:,.2f}"

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .status-within {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .status-near {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .status-over {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/fluency/96/construction.png", width=70)
st.sidebar.title("Navigation")
menu_options = [
    "Dashboard",
    "Projects",
    "Materials",
    "Suppliers",
    "Deliveries",
    "Labour",
    "Inventory",
    "Cost Analysis",
    "Budget Forecast",
    "SQL Reports",
    "About"
]
choice = st.sidebar.radio("Select Module", menu_options)
st.sidebar.markdown("---")
st.sidebar.caption("🏗️ **Construction Cost Estimator v2.0**")
st.sidebar.caption("Database: SQLite (`construction_cost_estimator.db`)")

# ==============================================================================
# 1. DASHBOARD
# ==============================================================================
if choice == "Dashboard":
    st.markdown('<div class="main-header">🏗️ Construction Material & Cost Estimation Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Live monitoring of projects, inventories, vendor spending, and structural cost variance.</div>', unsafe_allow_html=True)

    # Fetch KPI metrics
    kpi_projects = run_query("SELECT COUNT(*) AS count FROM projects;")['count'][0]
    kpi_materials = run_query("SELECT COUNT(*) AS count FROM materials;")['count'][0]
    kpi_suppliers = run_query("SELECT COUNT(*) AS count FROM suppliers;")['count'][0]
    
    kpi_mat_spending = run_query("""
        SELECT COALESCE(SUM(total_cost), 0) AS total 
        FROM material_deliveries 
        WHERE status = 'Delivered';
    """)['total'][0]
    
    kpi_labor_exp = run_query("SELECT COALESCE(SUM(total_cost), 0) AS total FROM labor;")['total'][0]
    
    # Total actual project cost = project_materials + labor
    kpi_proj_actual = run_query("""
        SELECT 
            COALESCE((SELECT SUM(actual_cost) FROM project_materials), 0) +
            COALESCE((SELECT SUM(total_cost) FROM labor), 0) AS total;
    """)['total'][0]

    # Projects over budget
    kpi_over_budget = run_query("""
        WITH ProjTotals AS (
            SELECT p.project_id, p.estimated_budget,
                COALESCE((SELECT SUM(actual_cost) FROM project_materials WHERE project_id = p.project_id), 0) +
                COALESCE((SELECT SUM(total_cost) FROM labor WHERE project_id = p.project_id), 0) AS actual_cost
            FROM projects p
        )
        SELECT COUNT(*) AS count FROM ProjTotals WHERE actual_cost > estimated_budget;
    """)['count'][0]

    # Render KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Projects", f"{kpi_projects}")
    c2.metric("Catalog Materials", f"{kpi_materials}")
    c3.metric("Registered Suppliers", f"{kpi_suppliers}")
    c4.metric("Projects Over Budget", f"{kpi_over_budget}", delta_color="inverse", delta=f"{kpi_over_budget} Overrun" if kpi_over_budget > 0 else "0")

    c5, c6, c7 = st.columns(3)
    c5.metric("Total Material Delivered Spend", format_inr(kpi_mat_spending))
    c6.metric("Total Site Labour Spend", format_inr(kpi_labor_exp))
    c7.metric("Total Project Actual Expense", format_inr(kpi_proj_actual))

    st.markdown("---")

    # Visualizations row 1
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("📊 Material Spending by Category")
        df_cat = run_query("""
            SELECT m.category, ROUND(SUM(d.total_cost), 2) AS total_spent
            FROM materials m
            JOIN material_deliveries d ON m.material_id = d.material_id
            WHERE d.status = 'Delivered'
            GROUP BY m.category
            ORDER BY total_spent DESC;
        """)
        if not df_cat.empty:
            fig1 = px.pie(df_cat, names="category", values="total_spent", hole=0.4,
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            fig1.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No delivery records available.")

    with col_chart2:
        st.subheader("🏢 Supplier-wise Purchase Spending")
        df_supp = run_query("""
            SELECT s.supplier_name, ROUND(SUM(d.total_cost), 2) AS total_spending
            FROM suppliers s
            JOIN material_deliveries d ON s.supplier_id = d.supplier_id
            GROUP BY s.supplier_name
            ORDER BY total_spending DESC;
        """)
        if not df_supp.empty:
            fig2 = px.bar(df_supp, x="total_spending", y="supplier_name", orientation='h',
                          labels={"total_spending": "Spending (INR)", "supplier_name": "Supplier"},
                          color="total_spending", color_continuous_scale="Blues")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No supplier records available.")

    # Visualizations row 2
    col_chart3, col_chart4 = st.columns(2)
    with col_chart3:
        st.subheader("📈 Estimated vs Actual Project Cost")
        df_evsa = run_query("""
            WITH Mat AS (
                SELECT project_id, SUM(actual_cost) AS mat_act 
                FROM project_materials GROUP BY project_id
            ),
            Lab AS (
                SELECT project_id, SUM(total_cost) AS lab_act 
                FROM labor GROUP BY project_id
            )
            SELECT 
                p.project_name, 
                p.estimated_budget, 
                (COALESCE(Mat.mat_act, 0) + COALESCE(Lab.lab_act, 0)) AS actual_cost
            FROM projects p
            LEFT JOIN Mat ON p.project_id = Mat.project_id
            LEFT JOIN Lab ON p.project_id = Lab.project_id;
        """)
        if not df_evsa.empty:
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(name='Estimated Budget', x=df_evsa['project_name'], y=df_evsa['estimated_budget'], marker_color='#3B82F6'))
            fig3.add_trace(go.Bar(name='Actual Expense', x=df_evsa['project_name'], y=df_evsa['actual_cost'], marker_color='#EF4444'))
            fig3.update_layout(barmode='group', xaxis_title="Project", yaxis_title="Amount (INR)")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No project records available.")

    with col_chart4:
        st.subheader("👷 Labour Cost by Worker Category")
        df_labor_cat = run_query("""
            SELECT worker_category, ROUND(SUM(total_cost), 2) AS total_cost
            FROM labor
            GROUP BY worker_category
            ORDER BY total_cost DESC;
        """)
        if not df_labor_cat.empty:
            fig4 = px.bar(df_labor_cat, x="worker_category", y="total_cost",
                          color="total_cost", color_continuous_scale="Viridis",
                          labels={"worker_category": "Trade", "total_cost": "Expense (INR)"})
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No labour records available.")

# ==============================================================================
# 2. PROJECTS
# ==============================================================================
elif choice == "Projects":
    st.title("📁 Construction Projects Management")
    tab1, tab2, tab3 = st.tabs(["View Projects", "Add Project", "Update Project"])

    with tab1:
        st.subheader("Active Projects Overview")
        df_proj = run_query("SELECT * FROM projects ORDER BY project_id;")
        st.dataframe(df_proj, use_container_width=True)

    with tab2:
        st.subheader("Add New Construction Project")
        with st.form("add_project_form"):
            p_name = st.text_input("Project Name *")
            p_client = st.text_input("Client Name")
            p_loc = st.text_input("Location")
            col_d1, col_d2 = st.columns(2)
            p_start = col_d1.date_input("Start Date")
            p_end = col_d2.date_input("Expected End Date")
            p_budget = st.number_input("Estimated Budget (INR) *", min_value=0.0, step=50000.0, value=1000000.0)
            p_status = st.selectbox("Project Status", ["Planning", "In Progress", "Completed", "On Hold"])
            submit_proj = st.form_submit_button("Create Project")

            if submit_proj:
                if not p_name.strip():
                    st.error("Project Name is mandatory.")
                elif p_end < p_start:
                    st.error("Expected End Date cannot precede Start Date.")
                else:
                    sql = """
                    INSERT INTO projects (project_name, client_name, location, start_date, expected_end_date, estimated_budget, project_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                    """
                    rows, err = execute_dml(sql, (p_name, p_client, p_loc, str(p_start), str(p_end), p_budget, p_status))
                    if err:
                        st.error(f"Error creating project: {err}")
                    else:
                        st.success(f"Project '{p_name}' created successfully!")
                        st.rerun()

    with tab3:
        st.subheader("Update Project Details")
        df_all_p = run_query("SELECT project_id, project_name FROM projects;")
        if not df_all_p.empty:
            proj_dict = dict(zip(df_all_p['project_name'], df_all_p['project_id']))
            sel_proj_name = st.selectbox("Select Project to Update", list(proj_dict.keys()))
            sel_pid = proj_dict[sel_proj_name]
            p_record = run_query("SELECT * FROM projects WHERE project_id = ?;", (sel_pid,)).iloc[0]

            with st.form("edit_project_form"):
                u_name = st.text_input("Project Name", value=p_record['project_name'])
                u_client = st.text_input("Client Name", value=p_record['client_name'] or "")
                u_loc = st.text_input("Location", value=p_record['location'] or "")
                u_budget = st.number_input("Estimated Budget (INR)", min_value=0.0, step=50000.0, value=float(p_record['estimated_budget']))
                statuses = ["Planning", "In Progress", "Completed", "On Hold"]
                curr_idx = statuses.index(p_record['project_status']) if p_record['project_status'] in statuses else 0
                u_status = st.selectbox("Status", statuses, index=curr_idx)
                update_btn = st.form_submit_button("Save Changes")

                if update_btn:
                    if not u_name.strip():
                        st.error("Project Name cannot be empty.")
                    else:
                        u_sql = """
                        UPDATE projects 
                        SET project_name = ?, client_name = ?, location = ?, estimated_budget = ?, project_status = ?
                        WHERE project_id = ?;
                        """
                        rows, err = execute_dml(u_sql, (u_name, u_client, u_loc, u_budget, u_status, sel_pid))
                        if err:
                            st.error(f"Update failed: {err}")
                        else:
                            st.success("Project updated successfully!")
                            st.rerun()

# ==============================================================================
# 3. MATERIALS
# ==============================================================================
elif choice == "Materials":
    st.title("🧱 Construction Materials Catalog")
    tab1, tab2, tab3, tab4 = st.tabs(["Browse Materials", "Add Material", "Update Material", "Delete Material"])

    with tab1:
        st.subheader("Materials Directory")
        c_search, c_filter = st.columns([2, 1])
        search_kw = c_search.text_input("Search Material Name", "")
        cats = ["All"] + list(run_query("SELECT DISTINCT category FROM materials ORDER BY category;")['category'])
        sel_cat = c_filter.selectbox("Filter Category", cats)

        query = "SELECT * FROM materials WHERE 1=1"
        params = []
        if search_kw.strip():
            query += " AND material_name LIKE ?"
            params.append(f"%{search_kw.strip()}%")
        if sel_cat != "All":
            query += " AND category = ?"
            params.append(sel_cat)
        query += " ORDER BY material_id;"

        df_m = run_query(query, tuple(params))
        st.dataframe(df_m, use_container_width=True)

    with tab2:
        st.subheader("Add Material to Catalog")
        with st.form("add_mat_form"):
            m_name = st.text_input("Material Name *")
            m_cat = st.selectbox("Category", ["Cement", "Steel", "Bricks", "Sand", "Concrete", "Tiles", "Wood", "Paint", "Electrical", "Plumbing", "Hardware"])
            m_unit = st.text_input("Unit of Measure (e.g., Bag, Kg, Ton, Piece) *")
            m_qty_req = st.number_input("Quantity Required for Active Works", min_value=0.0, step=10.0, value=100.0)
            m_cost = st.number_input("Estimated Unit Cost (INR) *", min_value=0.0, step=1.0, value=100.0)
            m_min = st.number_input("Minimum Stock Threshold", min_value=0.0, step=5.0, value=20.0)
            m_desc = st.text_area("Description")
            sub_mat = st.form_submit_button("Add Material")

            if sub_mat:
                if not m_name.strip() or not m_unit.strip():
                    st.error("Material Name and Unit are required fields.")
                else:
                    sql = """
                    INSERT INTO materials (material_name, category, unit, quantity_required, estimated_unit_cost, minimum_stock, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                    """
                    rows, err = execute_dml(sql, (m_name, m_cat, m_unit, m_qty_req, m_cost, m_min, m_desc))
                    if err:
                        st.error(f"Error adding material: {err}")
                    else:
                        st.success(f"Material '{m_name}' added successfully!")
                        st.rerun()

    with tab3:
        st.subheader("Update Material")
        df_mat_list = run_query("SELECT material_id, material_name FROM materials;")
        if not df_mat_list.empty:
            m_dict = dict(zip(df_mat_list['material_name'], df_mat_list['material_id']))
            sel_m_name = st.selectbox("Select Material to Update", list(m_dict.keys()))
            sel_mid = m_dict[sel_m_name]
            rec = run_query("SELECT * FROM materials WHERE material_id = ?;", (sel_mid,)).iloc[0]

            with st.form("edit_mat_form"):
                um_name = st.text_input("Material Name", value=rec['material_name'])
                um_cat = st.text_input("Category", value=rec['category'])
                um_unit = st.text_input("Unit", value=rec['unit'])
                um_cost = st.number_input("Estimated Unit Cost (INR)", min_value=0.0, value=float(rec['estimated_unit_cost']))
                um_min = st.number_input("Minimum Stock", min_value=0.0, value=float(rec['minimum_stock']))
                um_desc = st.text_area("Description", value=rec['description'] or "")
                um_btn = st.form_submit_button("Update Material")

                if um_btn:
                    sql_u = """
                    UPDATE materials 
                    SET material_name = ?, category = ?, unit = ?, estimated_unit_cost = ?, minimum_stock = ?, description = ?
                    WHERE material_id = ?;
                    """
                    rows, err = execute_dml(sql_u, (um_name, um_cat, um_unit, um_cost, um_min, um_desc, sel_mid))
                    if err:
                        st.error(f"Failed to update material: {err}")
                    else:
                        st.success("Material record updated successfully!")
                        st.rerun()

    with tab4:
        st.subheader("Delete Material")
        df_m_del = run_query("SELECT material_id, material_name FROM materials;")
        if not df_m_del.empty:
            del_dict = dict(zip(df_m_del['material_name'], df_m_del['material_id']))
            sel_del_name = st.selectbox("Select Material to Delete", list(del_dict.keys()), key="del_mat_sel")
            del_mid = del_dict[sel_del_name]

            # Dependency check
            del_count = run_query("SELECT COUNT(*) AS c FROM material_deliveries WHERE material_id = ?;", (del_mid,))['c'][0]
            pm_count = run_query("SELECT COUNT(*) AS c FROM project_materials WHERE material_id = ?;", (del_mid,))['c'][0]

            if del_count > 0 or pm_count > 0:
                st.warning(f"⚠️ Cannot delete '{sel_del_name}'. It is referenced by {del_count} delivery records and {pm_count} project-material records (Foreign Key RESTRICT).")
            else:
                st.info("This material has no active dependencies and can be safely removed.")
                if st.button(f"Confirm Permanent Deletion of '{sel_del_name}'"):
                    rows, err = execute_dml("DELETE FROM materials WHERE material_id = ?;", (del_mid,))
                    if err:
                        st.error(f"Deletion failed: {err}")
                    else:
                        st.success("Material deleted successfully!")
                        st.rerun()

# ==============================================================================
# 4. SUPPLIERS
# ==============================================================================
elif choice == "Suppliers":
    st.title("🚚 Supplier Directory & Relations")
    tab1, tab2, tab3 = st.tabs(["Supplier Directory", "Add Supplier", "Update / Delete"])

    with tab1:
        st.subheader("Registered Suppliers")
        df_supp = run_query("""
            SELECT 
                s.supplier_id,
                s.supplier_name,
                s.contact_person,
                s.phone,
                s.email,
                s.rating,
                COUNT(d.delivery_id) AS total_deliveries,
                ROUND(COALESCE(SUM(d.total_cost), 0), 2) AS total_spending
            FROM suppliers s
            LEFT JOIN material_deliveries d ON s.supplier_id = d.supplier_id
            GROUP BY s.supplier_id, s.supplier_name, s.contact_person, s.phone, s.email, s.rating
            ORDER BY total_spending DESC;
        """)
        st.dataframe(df_supp, use_container_width=True)

    with tab2:
        st.subheader("Add New Vendor / Supplier")
        with st.form("add_supplier_form"):
            s_name = st.text_input("Supplier / Business Name *")
            s_contact = st.text_input("Contact Person")
            s_phone = st.text_input("Phone Number")
            s_email = st.text_input("Email Address")
            s_address = st.text_area("Address / Yard Location")
            s_rating = st.slider("Rating (0.0 to 5.0)", min_value=0.0, max_value=5.0, value=4.5, step=0.1)
            sub_supp = st.form_submit_button("Register Supplier")

            if sub_supp:
                if not s_name.strip():
                    st.error("Supplier Name is required.")
                elif s_email.strip() and "@" not in s_email:
                    st.error("Please provide a valid email address.")
                else:
                    sql_s = """
                    INSERT INTO suppliers (supplier_name, contact_person, phone, email, address, rating)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """
                    rows, err = execute_dml(sql_s, (s_name, s_contact, s_phone, s_email, s_address, s_rating))
                    if err:
                        st.error(f"Error registering supplier: {err}")
                    else:
                        st.success(f"Supplier '{s_name}' registered successfully!")
                        st.rerun()

    with tab3:
        st.subheader("Manage Supplier Records")
        df_s_all = run_query("SELECT supplier_id, supplier_name FROM suppliers;")
        if not df_s_all.empty:
            s_map = dict(zip(df_s_all['supplier_name'], df_s_all['supplier_id']))
            sel_s = st.selectbox("Select Supplier", list(s_map.keys()))
            sid = s_map[sel_s]
            s_row = run_query("SELECT * FROM suppliers WHERE supplier_id = ?;", (sid,)).iloc[0]

            with st.expander("Update Supplier Information", expanded=True):
                with st.form("edit_supplier_form"):
                    es_name = st.text_input("Supplier Name", value=s_row['supplier_name'])
                    es_contact = st.text_input("Contact Person", value=s_row['contact_person'] or "")
                    es_phone = st.text_input("Phone", value=s_row['phone'] or "")
                    es_email = st.text_input("Email", value=s_row['email'] or "")
                    es_address = st.text_area("Address", value=s_row['address'] or "")
                    es_rating = st.slider("Rating", min_value=0.0, max_value=5.0, value=float(s_row['rating'] or 4.0), step=0.1)
                    btn_upd = st.form_submit_button("Save Supplier Changes")

                    if btn_upd:
                        u_sql = """
                        UPDATE suppliers 
                        SET supplier_name = ?, contact_person = ?, phone = ?, email = ?, address = ?, rating = ?
                        WHERE supplier_id = ?;
                        """
                        rows, err = execute_dml(u_sql, (es_name, es_contact, es_phone, es_email, es_address, es_rating, sid))
                        if err:
                            st.error(f"Update failed: {err}")
                        else:
                            st.success("Supplier details updated!")
                            st.rerun()

            with st.expander("Delete Supplier"):
                dep_count = run_query("SELECT COUNT(*) AS c FROM material_deliveries WHERE supplier_id = ?;", (sid,))['c'][0]
                if dep_count > 0:
                    st.warning(f"⚠️ Cannot delete '{sel_s}'. Associated with {dep_count} delivery orders.")
                else:
                    if st.button(f"Confirm Delete Supplier '{sel_s}'"):
                        rows, err = execute_dml("DELETE FROM suppliers WHERE supplier_id = ?;", (sid,))
                        if err:
                            st.error(f"Deletion error: {err}")
                        else:
                            st.success("Supplier deleted successfully!")
                            st.rerun()

# ==============================================================================
# 5. DELIVERIES
# ==============================================================================
elif choice == "Deliveries":
    st.title("📦 Material Purchases & Deliveries")
    tab1, tab2 = st.tabs(["Delivery Log", "Record New Delivery"])

    with tab1:
        st.subheader("Procurement & Delivery Log")
        c1, c2 = st.columns(2)
        status_filter = c1.selectbox("Filter Status", ["All", "Delivered", "Pending", "Partially Delivered"])
        
        del_sql = """
        SELECT 
            d.delivery_id,
            m.material_name,
            s.supplier_name,
            d.delivery_date,
            d.quantity_received,
            m.unit,
            d.unit_price,
            d.total_cost,
            d.status
        FROM material_deliveries d
        JOIN materials m ON d.material_id = m.material_id
        JOIN suppliers s ON d.supplier_id = s.supplier_id
        WHERE 1=1
        """
        params = []
        if status_filter != "All":
            del_sql += " AND d.status = ?"
            params.append(status_filter)
        del_sql += " ORDER BY d.delivery_date DESC;"
        
        df_del = run_query(del_sql, tuple(params))
        st.dataframe(df_del, use_container_width=True)

    with tab2:
        st.subheader("Record Material Delivery")
        df_m = run_query("SELECT material_id, material_name, unit, estimated_unit_cost FROM materials;")
        df_s = run_query("SELECT supplier_id, supplier_name FROM suppliers;")

        if df_m.empty or df_s.empty:
            st.warning("Please ensure at least one Material and one Supplier exist before adding a delivery.")
        else:
            m_opts = dict(zip(df_m['material_name'], df_m['material_id']))
            s_opts = dict(zip(df_s['supplier_name'], df_s['supplier_id']))

            with st.form("add_delivery_form"):
                sel_m_d = st.selectbox("Material *", list(m_opts.keys()))
                sel_s_d = st.selectbox("Supplier *", list(s_opts.keys()))
                d_date = st.date_input("Delivery Date")
                d_qty = st.number_input("Quantity *", min_value=0.1, step=1.0, value=10.0)
                
                # Fetch default price
                def_price = float(df_m[df_m['material_id'] == m_opts[sel_m_d]]['estimated_unit_cost'].values[0])
                d_price = st.number_input("Unit Price (INR) *", min_value=0.1, step=1.0, value=def_price)
                
                calc_total = round(d_qty * d_price, 2)
                st.info(f"Calculated Total Cost: **{format_inr(calc_total)}**")
                
                d_status = st.selectbox("Delivery Status", ["Delivered", "Pending", "Partially Delivered"])
                sub_del = st.form_submit_button("Record Delivery")

                if sub_del:
                    ins_del = """
                    INSERT INTO material_deliveries (material_id, supplier_id, delivery_date, quantity_received, unit_price, total_cost, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                    """
                    rows, err = execute_dml(ins_del, (m_opts[sel_m_d], s_opts[sel_s_d], str(d_date), d_qty, d_price, calc_total, d_status))
                    if err:
                        st.error(f"Failed to record delivery: {err}")
                    else:
                        st.success("Delivery recorded successfully!")
                        st.rerun()

# ==============================================================================
# 6. LABOUR
# ==============================================================================
elif choice == "Labour":
    st.title("👷 Construction Site Labour Expenses")
    tab1, tab2 = st.tabs(["Labour Shifts Log", "Log Labour Work"])

    with tab1:
        st.subheader("Direct Labour Logs")
        df_p = run_query("SELECT project_id, project_name FROM projects;")
        p_filter = st.selectbox("Filter Project", ["All"] + list(df_p['project_name']))

        sql_lab = """
        SELECT 
            l.labor_id,
            p.project_name,
            l.worker_category,
            l.worker_count,
            l.hours_worked,
            l.hourly_rate,
            l.labor_date,
            l.total_cost,
            l.description
        FROM labor l
        JOIN projects p ON l.project_id = p.project_id
        WHERE 1=1
        """
        params = []
        if p_filter != "All":
            sql_lab += " AND p.project_name = ?"
            params.append(p_filter)
        sql_lab += " ORDER BY l.labor_date DESC;"

        df_lab_res = run_query(sql_lab, tuple(params))
        st.dataframe(df_lab_res, use_container_width=True)

    with tab2:
        st.subheader("Record Labour Work Shift")
        df_proj_lab = run_query("SELECT project_id, project_name FROM projects;")
        if df_proj_lab.empty:
            st.warning("Please create at least one project before logging labour expenses.")
        else:
            p_map_lab = dict(zip(df_proj_lab['project_name'], df_proj_lab['project_id']))
            with st.form("log_labor_form"):
                sel_p = st.selectbox("Project *", list(p_map_lab.keys()))
                w_cat = st.selectbox("Worker Category *", [
                    "Mason", "Bar Bender", "Carpenter", "Electrician", "Plumber", "Painter", "General Helper"
                ])
                w_count = st.number_input("Worker Count *", min_value=1, step=1, value=5)
                w_hours = st.number_input("Hours Worked per Worker *", min_value=0.5, step=0.5, value=8.0)
                w_rate = st.number_input("Hourly Wage Rate per Worker (INR) *", min_value=10.0, step=5.0, value=120.0)
                w_date = st.date_input("Shift Date")
                w_desc = st.text_input("Work Description / Location on Site")
                
                computed_labor = round(w_count * w_hours * w_rate, 2)
                st.info(f"Total Labour Shift Cost: **{format_inr(computed_labor)}** (`{w_count} workers * {w_hours} hrs * ₹{w_rate}/hr`)")
                
                sub_lab = st.form_submit_button("Record Labour Expense")

                if sub_lab:
                    ins_lab = """
                    INSERT INTO labor (project_id, worker_category, worker_count, hours_worked, hourly_rate, labor_date, total_cost, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """
                    rows, err = execute_dml(ins_lab, (p_map_lab[sel_p], w_cat, w_count, w_hours, w_rate, str(w_date), computed_labor, w_desc))
                    if err:
                        st.error(f"Error logging labour: {err}")
                    else:
                        st.success("Labour expense logged successfully!")
                        st.rerun()

# ==============================================================================
# 7. INVENTORY
# ==============================================================================
elif choice == "Inventory":
    st.title("📦 Material Inventory & Stock Analysis")
    st.markdown(r"""
    **Inventory Model Logic**:
    * **Quantity Required**: Total estimated requirements for planned project baselines.
    * **Total Received**: Sum of physical shipments marked as `Delivered`.
    * **Total Consumed**: Actual quantity consumed on active project sites.
    * **Current Physical Stock**: `Total Received - Total Consumed`.
    * **Status Rules**:
      * `Out of Stock`: Current Stock $\le 0$
      * `Low Stock`: Current Stock $<$ Minimum Stock Threshold
      * `Requirement Completed`: Total Received $\ge$ Quantity Required
      * `Available`: Normal operating buffer
    """)

    # Query inventory data
    sql_inv = """
    SELECT 
        m.material_id,
        m.material_name,
        m.category,
        m.unit,
        m.quantity_required,
        COALESCE((SELECT SUM(d.quantity_received) FROM material_deliveries d WHERE d.material_id = m.material_id AND d.status = 'Delivered'), 0) AS total_received,
        COALESCE((SELECT SUM(pm.actual_quantity) FROM project_materials pm WHERE pm.material_id = m.material_id), 0) AS total_consumed,
        COALESCE((SELECT SUM(d.quantity_received) FROM material_deliveries d WHERE d.material_id = m.material_id AND d.status = 'Delivered'), 0) -
        COALESCE((SELECT SUM(pm.actual_quantity) FROM project_materials pm WHERE pm.material_id = m.material_id), 0) AS current_stock,
        m.minimum_stock,
        CASE 
            WHEN (COALESCE((SELECT SUM(d.quantity_received) FROM material_deliveries d WHERE d.material_id = m.material_id AND d.status = 'Delivered'), 0) -
                  COALESCE((SELECT SUM(pm.actual_quantity) FROM project_materials pm WHERE pm.material_id = m.material_id), 0)) <= 0 THEN 'Out of Stock'
            WHEN (COALESCE((SELECT SUM(d.quantity_received) FROM material_deliveries d WHERE d.material_id = m.material_id AND d.status = 'Delivered'), 0) -
                  COALESCE((SELECT SUM(pm.actual_quantity) FROM project_materials pm WHERE pm.material_id = m.material_id), 0)) < m.minimum_stock THEN 'Low Stock'
            WHEN COALESCE((SELECT SUM(d.quantity_received) FROM material_deliveries d WHERE d.material_id = m.material_id AND d.status = 'Delivered'), 0) >= m.quantity_required THEN 'Requirement Completed'
            ELSE 'Available'
        END AS stock_status
    FROM materials m
    ORDER BY m.material_id;
    """
    df_inv = run_query(sql_inv)

    # Filtering
    c_f1, c_f2 = st.columns(2)
    cat_filter = c_f1.selectbox("Filter Category", ["All"] + sorted(list(df_inv['category'].unique())))
    status_filter = c_f2.selectbox("Filter Stock Status", ["All", "Available", "Low Stock", "Out of Stock", "Requirement Completed"])

    df_filtered_inv = df_inv.copy()
    if cat_filter != "All":
        df_filtered_inv = df_filtered_inv[df_filtered_inv['category'] == cat_filter]
    if status_filter != "All":
        df_filtered_inv = df_filtered_inv[df_filtered_inv['stock_status'] == status_filter]

    st.dataframe(df_filtered_inv, use_container_width=True)

    # Low stock alerts banner
    low_stock_items = df_inv[df_inv['stock_status'].isin(['Low Stock', 'Out of Stock'])]
    if not low_stock_items.empty:
        st.error(f"⚠️ **Attention Required**: {len(low_stock_items)} material(s) are critically low or out of stock: {', '.join(low_stock_items['material_name'].tolist())}")

    # Visualizations
    c_c1, c_c2 = st.columns(2)
    with c_c1:
        st.subheader("Stock Status Distribution")
        fig_inv = px.pie(df_inv, names="stock_status", hole=0.35,
                         color="stock_status",
                         color_discrete_map={
                             "Available": "#10B981",
                             "Low Stock": "#F59E0B",
                             "Out of Stock": "#EF4444",
                             "Requirement Completed": "#3B82F6"
                         })
        st.plotly_chart(fig_inv, use_container_width=True)

    with c_c2:
        st.subheader("Physical Stock vs Minimum Threshold")
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name='Current Stock', x=df_inv['material_name'], y=df_inv['current_stock'], marker_color='#10B981'))
        fig_bar.add_trace(go.Bar(name='Min Stock Threshold', x=df_inv['material_name'], y=df_inv['minimum_stock'], marker_color='#F59E0B'))
        fig_bar.update_layout(barmode='group', xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)

# ==============================================================================
# 8. COST ANALYSIS
# ==============================================================================
elif choice == "Cost Analysis":
    st.title("💰 Comprehensive Structural Cost Analysis")
    
    # Combined project expense query
    sql_combined = """
    WITH MatExp AS (
        SELECT project_id, SUM(estimated_cost) AS est_mat, SUM(actual_cost) AS act_mat 
        FROM project_materials 
        GROUP BY project_id
    ),
    LabExp AS (
        SELECT project_id, SUM(total_cost) AS act_lab 
        FROM labor 
        GROUP BY project_id
    )
    SELECT 
        p.project_id,
        p.project_name,
        p.client_name,
        p.location,
        p.estimated_budget,
        COALESCE(MatExp.est_mat, 0) AS planned_material_cost,
        COALESCE(MatExp.act_mat, 0) AS actual_material_cost,
        COALESCE(LabExp.act_lab, 0) AS actual_labor_cost,
        (COALESCE(MatExp.act_mat, 0) + COALESCE(LabExp.act_lab, 0)) AS total_actual_cost,
        (p.estimated_budget - (COALESCE(MatExp.act_mat, 0) + COALESCE(LabExp.act_lab, 0))) AS remaining_budget,
        ((COALESCE(MatExp.act_mat, 0) + COALESCE(LabExp.act_lab, 0)) - p.estimated_budget) AS variance,
        ROUND(((COALESCE(MatExp.act_mat, 0) + COALESCE(LabExp.act_lab, 0)) / CASE WHEN p.estimated_budget = 0 THEN 1 ELSE p.estimated_budget END) * 100, 2) AS budget_utilization_pct,
        CASE 
            WHEN ((COALESCE(MatExp.act_mat, 0) + COALESCE(LabExp.act_lab, 0)) / CASE WHEN p.estimated_budget = 0 THEN 1 ELSE p.estimated_budget END) * 100 < 80 THEN 'Within Budget'
            WHEN ((COALESCE(MatExp.act_mat, 0) + COALESCE(LabExp.act_lab, 0)) / CASE WHEN p.estimated_budget = 0 THEN 1 ELSE p.estimated_budget END) * 100 <= 100 THEN 'Near Budget Limit'
            ELSE 'Over Budget'
        END AS budget_status
    FROM projects p
    LEFT JOIN MatExp ON p.project_id = MatExp.project_id
    LEFT JOIN LabExp ON p.project_id = LabExp.project_id
    ORDER BY p.project_id;
    """
    df_comb = run_query(sql_combined)
    st.subheader("Project-wise Financial Summary")
    st.dataframe(df_comb, use_container_width=True)

    # Cost breakdown chart
    st.subheader("Structural Expense Breakdown: Material vs Labour")
    fig_stack = go.Figure()
    fig_stack.add_trace(go.Bar(name='Actual Material Cost', x=df_comb['project_name'], y=df_comb['actual_material_cost'], marker_color='#3B82F6'))
    fig_stack.add_trace(go.Bar(name='Actual Labour Cost', x=df_comb['project_name'], y=df_comb['actual_labor_cost'], marker_color='#F59E0B'))
    fig_stack.update_layout(barmode='stack', yaxis_title="Cost in INR")
    st.plotly_chart(fig_stack, use_container_width=True)

# ==============================================================================
# 9. BUDGET FORECAST
# ==============================================================================
elif choice == "Budget Forecast":
    st.title("🎯 Project Budget Forecasting & Health Module")
    st.markdown("""
    Select a construction project below to evaluate structural budget health, cost variances, and forecast overruns.
    """)

    df_p = run_query("SELECT project_id, project_name FROM projects;")
    if df_p.empty:
        st.info("No projects registered.")
    else:
        p_map = dict(zip(df_p['project_name'], df_p['project_id']))
        sel_proj_name = st.selectbox("Select Project for Evaluation", list(p_map.keys()))
        pid = p_map[sel_proj_name]

        # Calculate project specific financials
        sql_proj_detail = """
        WITH MatExp AS (
            SELECT SUM(estimated_cost) AS est_mat, SUM(actual_cost) AS act_mat 
            FROM project_materials WHERE project_id = ?
        ),
        LabExp AS (
            SELECT SUM(total_cost) AS act_lab 
            FROM labor WHERE project_id = ?
        )
        SELECT 
            p.project_id,
            p.project_name,
            p.client_name,
            p.location,
            p.start_date,
            p.expected_end_date,
            p.estimated_budget,
            p.project_status,
            COALESCE(MatExp.est_mat, 0) AS estimated_material_cost,
            COALESCE(MatExp.act_mat, 0) AS actual_material_cost,
            COALESCE(LabExp.act_lab, 0) AS actual_labor_cost,
            (COALESCE(MatExp.act_mat, 0) + COALESCE(LabExp.act_lab, 0)) AS total_actual_cost,
            (p.estimated_budget - (COALESCE(MatExp.act_mat, 0) + COALESCE(LabExp.act_lab, 0))) AS remaining_budget,
            ((COALESCE(MatExp.act_mat, 0) + COALESCE(LabExp.act_lab, 0)) - p.estimated_budget) AS variance,
            ROUND(((COALESCE(MatExp.act_mat, 0) + COALESCE(LabExp.act_lab, 0)) / CASE WHEN p.estimated_budget = 0 THEN 1 ELSE p.estimated_budget END) * 100, 2) AS utilization_pct
        FROM projects p
        LEFT JOIN MatExp ON 1=1
        LEFT JOIN LabExp ON 1=1
        WHERE p.project_id = ?;
        """
        row = run_query(sql_proj_detail, (pid, pid, pid)).iloc[0]

        budget = float(row['estimated_budget'])
        act_cost = float(row['total_actual_cost'])
        rem_budget = float(row['remaining_budget'])
        var_cost = float(row['variance'])
        util_pct = float(row['utilization_pct'])

        # Determine budget health status
        if util_pct < 80.0:
            status_text = "Within Budget"
            badge_html = f'<span class="status-within">🟢 WITHIN BUDGET ({util_pct}%)</span>'
        elif util_pct <= 100.0:
            status_text = "Near Budget Limit"
            badge_html = f'<span class="status-near">🟡 NEAR BUDGET LIMIT ({util_pct}%)</span>'
        else:
            status_text = "Over Budget"
            badge_html = f'<span class="status-over">🔴 OVER BUDGET ({util_pct}%)</span>'

        st.markdown(f"### Project Health: {badge_html}", unsafe_allow_html=True)
        st.write("")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sanctioned Budget", format_inr(budget))
        c2.metric("Total Actual Incurred", format_inr(act_cost))
        c3.metric("Remaining Balance", format_inr(rem_budget))
        c4.metric("Cost Variance", format_inr(var_cost), delta=f"{'+' if var_cost>0 else ''}{format_inr(var_cost)}", delta_color="inverse")

        st.markdown("---")

        col_g, col_pie = st.columns(2)
        with col_g:
            st.subheader("Budget Gauge")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=util_pct,
                title={'text': "Budget Utilization %"},
                gauge={
                    'axis': {'range': [0, 150]},
                    'bar': {'color': "#EF4444" if util_pct > 100 else ("#F59E0B" if util_pct >= 80 else "#10B981")},
                    'steps': [
                        {'range': [0, 80], 'color': "#D1FAE5"},
                        {'range': [80, 100], 'color': "#FEF3C7"},
                        {'range': [100, 150], 'color': "#FEE2E2"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 100
                    }
                }
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_pie:
            st.subheader("Incurred Cost Distribution")
            df_pie_cost = pd.DataFrame({
                "Expense Type": ["Materials", "Direct Labour"],
                "Amount": [row['actual_material_cost'], row['actual_labor_cost']]
            })
            fig_p = px.pie(df_pie_cost, names="Expense Type", values="Amount", color_discrete_sequence=['#3B82F6', '#F59E0B'])
            st.plotly_chart(fig_p, use_container_width=True)

# ==============================================================================
# 10. SQL REPORTS
# ==============================================================================
elif choice == "SQL Reports":
    st.title("🔍 SQL Query Execution & Academic Demonstration")
    st.markdown("Execute all 44 predefined academic SQL queries directly against the live database.")

    from queries import SQL_QUERIES, get_all_categories, get_queries_by_category

    categories = ["All Categories"] + get_all_categories()
    sel_cat = st.selectbox("Filter Query by Category", categories)

    if sel_cat == "All Categories":
        available_queries = SQL_QUERIES
    else:
        available_queries = get_queries_by_category(sel_cat)

    q_options = [f"Query {q['id']:02d}: {q['title']} [{q['category']}]" for q in available_queries]
    sel_q_str = st.selectbox("Select SQL Query to Execute", q_options)

    # Find chosen query
    q_id = int(sel_q_str.split(":")[0].replace("Query ", ""))
    curr_q = next(q for q in SQL_QUERIES if q['id'] == q_id)

    st.markdown(f"### {curr_q['title']}")
    st.info(f"**Explanation:** {curr_q['description']}")
    st.code(curr_q['sql'], language="sql")

    if st.button("▶️ Execute SQL Query"):
        try:
            res_df = run_query(curr_q['sql'])
            st.success(f"Execution Successful! ({len(res_df)} rows returned)")
            st.dataframe(res_df, use_container_width=True)

            # Export button
            csv_data = res_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv_data,
                file_name=f"query_{curr_q['id']:02d}_results.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"SQL Execution Error: {e}")

# ==============================================================================
# 11. ABOUT
# ==============================================================================
elif choice == "About":
    st.title("ℹ️ About the Project")
    st.markdown(r"""
    ### Construction Material Inventory & Structural Cost Estimation System
    * **Student Academic SQL Database Project**
    * **Technology Stack**: Python, SQLite, Pandas, Plotly, Streamlit
    * **Environment**: Google Colab / Local Machine
    
    ---
    ### Relational Schema Architecture (6 Core Tables):
    1. **`materials`**: Material specifications, category, units, threshold stock limits.
    2. **`suppliers`**: Supplier profiles, ratings, and contact points.
    3. **`projects`**: Structural projects, client details, sanctioned budgets, schedules.
    4. **`project_materials`**: Project-specific material requirements and actual bills.
    5. **`material_deliveries`**: Procurement logs, delivery dates, received amounts.
    6. **`labor`**: Daily site workforce shifts, trades, hours, and labour overheads.

    ---
    ### Cost Calculation Formulas:
    * **Material Delivery Cost**: $\text{Quantity Received} \times \text{Unit Price}$
    * **Labour Shift Cost**: $\text{Worker Count} \times \text{Hours Worked} \times \text{Hourly Rate}$
    * **Actual Project Cost**: $\sum \text{Actual Material Cost} + \sum \text{Actual Labour Cost}$
    * **Remaining Budget**: $\text{Estimated Budget} - \text{Actual Project Cost}$
    * **Budget Utilization %**: $\left(\frac{\text{Actual Project Cost}}{\text{Estimated Budget}}\right) \times 100$
    * **Cost Variance**: $\text{Actual Project Cost} - \text{Estimated Budget}$
    """)

    st.subheader("📥 Export Complete Academic Reports")
    rep_files = [
        ("Material Inventory Report", "material_report.csv"),
        ("Supplier Spending Report", "supplier_report.csv"),
        ("Delivery Records Report", "delivery_records.csv"),
        ("Labour Expenses Report", "labor_expenses.csv"),
        ("Project Cost Summary Report", "project_cost_report.csv"),
        ("Budget Utilization Report", "budget_utilization.csv")
    ]
    
    col_a, col_b = st.columns(2)
    for idx, (title, fname) in enumerate(rep_files):
        fpath = os.path.join(CURRENT_DIR, "reports", fname)
        if os.path.exists(fpath):
            with open(fpath, "rb") as f:
                data = f.read()
            target_col = col_a if idx % 2 == 0 else col_b
            target_col.download_button(
                label=f"📄 Download {title}",
                data=data,
                file_name=fname,
                mime="text/csv",
                key=f"dl_{fname}"
            )
