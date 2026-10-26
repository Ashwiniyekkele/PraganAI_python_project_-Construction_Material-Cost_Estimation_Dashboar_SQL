"""
db_manager.py
Database management, schema creation, sample data seeding,
and SQL query execution for the Construction Material Inventory &
Structural Cost Estimation System.
"""

import os
import sqlite3
import pandas as pd
from typing import Optional, List, Tuple, Dict, Any

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(CURRENT_DIR, "construction_cost_estimator.db")

def get_connection(db_path: str = DB_NAME) -> sqlite3.Connection:
    """Creates and returns an SQLite connection with Foreign Keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_database(db_path: str = DB_NAME) -> None:
    """Creates the 6 relational tables if they do not exist with all constraints."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # TABLE 1: materials
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            material_id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit TEXT NOT NULL,
            quantity_required REAL NOT NULL DEFAULT 0 CHECK(quantity_required >= 0),
            estimated_unit_cost REAL NOT NULL DEFAULT 0 CHECK(estimated_unit_cost >= 0),
            minimum_stock REAL NOT NULL DEFAULT 10 CHECK(minimum_stock >= 0),
            description TEXT
        );
        """)

        # TABLE 2: suppliers
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT NOT NULL,
            contact_person TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            rating REAL CHECK(rating >= 0 AND rating <= 5)
        );
        """)

        # TABLE 5: projects (Created before labor and project_materials due to FK dependencies)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            client_name TEXT,
            location TEXT,
            start_date TEXT,
            expected_end_date TEXT,
            estimated_budget REAL NOT NULL CHECK(estimated_budget >= 0),
            project_status TEXT NOT NULL CHECK(project_status IN ('Planning', 'In Progress', 'Completed', 'On Hold'))
        );
        """)

        # TABLE 3: material_deliveries
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS material_deliveries (
            delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER NOT NULL,
            supplier_id INTEGER NOT NULL,
            delivery_date TEXT NOT NULL,
            quantity_received REAL NOT NULL CHECK(quantity_received >= 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0),
            total_cost REAL NOT NULL CHECK(total_cost >= 0),
            status TEXT NOT NULL CHECK(status IN ('Delivered', 'Pending', 'Partially Delivered')),
            FOREIGN KEY (material_id) REFERENCES materials(material_id) ON DELETE RESTRICT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE RESTRICT
        );
        """)

        # TABLE 4: labor
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS labor (
            labor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            worker_category TEXT NOT NULL,
            worker_count INTEGER NOT NULL CHECK(worker_count > 0),
            hours_worked REAL NOT NULL CHECK(hours_worked >= 0),
            hourly_rate REAL NOT NULL CHECK(hourly_rate >= 0),
            labor_date TEXT NOT NULL,
            total_cost REAL NOT NULL CHECK(total_cost >= 0),
            description TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE RESTRICT
        );
        """)

        # TABLE 6: project_materials
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_materials (
            project_material_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            material_id INTEGER NOT NULL,
            planned_quantity REAL NOT NULL CHECK(planned_quantity >= 0),
            actual_quantity REAL NOT NULL DEFAULT 0 CHECK(actual_quantity >= 0),
            estimated_cost REAL NOT NULL CHECK(estimated_cost >= 0),
            actual_cost REAL NOT NULL DEFAULT 0 CHECK(actual_cost >= 0),
            UNIQUE(project_id, material_id),
            FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
            FOREIGN KEY (material_id) REFERENCES materials(material_id) ON DELETE RESTRICT
        );
        """)

        conn.commit()
    print("Database tables initialized successfully.")

def seed_sample_data(db_path: str = DB_NAME) -> None:
    """Inserts sample data safely (idempotent, avoids duplicates)."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Check if already seeded
        cursor.execute("SELECT COUNT(*) FROM materials;")
        if cursor.fetchone()[0] > 0:
            print("Sample data already exists. Skipping seeding.")
            return

        print("Seeding database with realistic Indian construction records...")

        # 1. MATERIALS (12 materials)
        materials_data = [
            (1, "UltraTech Cement 53 Grade", "Cement", "Bag", 1200, 420.0, 50, "Standard Portland Cement for structural RCC"),
            (2, "Tata Tiscon 500D TMT Steel Bars", "Steel", "Kg", 8500, 72.0, 500, "High strength thermo-mechanically treated rebar"),
            (3, "Standard Red Clay Bricks", "Bricks", "Piece", 30000, 9.0, 2000, "Kiln-burnt solid red bricks for masonry"),
            (4, "Coarse River Sand", "Sand", "Ton", 250, 1800.0, 20, "Screened river sand for plastering and concrete mix"),
            (5, "M20 Ready-Mix Concrete", "Concrete", "Cu.m", 150, 4500.0, 15, "Standard grade transit mixer RMC"),
            (6, "Kajaria Vitrified Floor Tiles 2x2", "Tiles", "Sq.ft", 3500, 60.0, 200, "Double-charged vitrified polished tiles"),
            (7, "Treated Teak Wood Battens", "Wood", "Cu.ft", 180, 2400.0, 15, "Seasoned CP teak wood for door frames & trims"),
            (8, "Asian Paints Apex Exterior Emulsion", "Paint", "Litre", 450, 250.0, 30, "Weatherproof exterior acrylic emulsion"),
            (9, "Havells FRLS Copper Wiring 2.5 sq mm", "Electrical", "Coil (90m)", 80, 1950.0, 10, "Flame retardant low smoke insulated electrical wire"),
            (10, "Astral Schedule 40 CPVC Pipes 1 inch", "Plumbing", "Piece (3m)", 160, 480.0, 20, "Chlorinated polyvinyl chloride hot/cold water pipes"),
            (11, "Black Galaxy Granite Slabs", "Tiles", "Sq.ft", 800, 180.0, 50, "Premium polished kitchen countertop granite"),
            (12, "Birla White Wall Care Putty", "Paint", "Bag (40kg)", 200, 750.0, 25, "Water resistant polymer modified wall putty")
        ]
        cursor.executemany("""
            INSERT INTO materials (material_id, material_name, category, unit, quantity_required, estimated_unit_cost, minimum_stock, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, materials_data)

        # 2. SUPPLIERS (6 suppliers - one with no deliveries for SQL query demonstration)
        suppliers_data = [
            (1, "Bharat Buildcon Materials Ltd", "Rajesh Sharma", "+91-9823011223", "sales@bharatbuildcon.in", "Plot 42, Industrial Area, Bangalore", 4.7),
            (2, "Krishna Steel & Hardware Mart", "Suresh Patel", "+91-9712044556", "orders@krishnasteel.com", "Shop 12, Loha Mandi, Pune", 4.5),
            (3, "Ganga Mining & Aggregates Co", "Anil Verma", "+91-9456077889", "ganga_sand@rediffmail.com", "Riverbank Yard, Noida Expressway, Greater Noida", 4.2),
            (4, "Deccan Clay Products & Bricks", "Manoj Gowda", "+91-9988011234", "deccanbricks@gmail.com", "Hosur Main Road, Bangalore", 4.6),
            (5, "Apex Electro & Paint Solutions", "Vikas Gupta", "+91-9311022344", "contact@apexsolutions.org", "Chandni Chowk Market, New Delhi", 4.8),
            (6, "National Heavy Tools & Scaffolding", "Pooja Hegde", "+91-9844055667", "info@nationaltools.in", "Peenya 2nd Stage, Bangalore", 3.9)
        ]
        cursor.executemany("""
            INSERT INTO suppliers (supplier_id, supplier_name, contact_person, phone, email, address, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, suppliers_data)

        # 3. PROJECTS (3 projects with different budget statuses)
        projects_data = [
            (1, "Greenfield Luxury Villas", "Brigade Estates Ltd", "Whitefield, Bangalore", "2024-01-15", "2024-11-30", 2500000.0, "In Progress"),
            (2, "Metro City Commercial Complex", "Apex Infra Corp", "Sector 62, Noida", "2024-02-01", "2024-12-15", 1800000.0, "In Progress"),
            (3, "Sunrise Residential Towers", "Kumar Urban Developers", "Kharadi, Pune", "2024-03-01", "2024-09-30", 600000.0, "In Progress")
        ]
        cursor.executemany("""
            INSERT INTO projects (project_id, project_name, client_name, location, start_date, expected_end_date, estimated_budget, project_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, projects_data)

        # 4. PROJECT_MATERIALS (18 planning records across the 3 projects)
        # (project_id, material_id, planned_qty, actual_qty, estimated_cost, actual_cost)
        project_materials_data = [
            # Project 1: Greenfield Luxury Villas (Budget: 25 Lakhs) -> Well within budget (~14.4 Lakhs material + 1.2 Lakhs labour = 15.6 Lakhs ~ 62%)
            (1, 1, 400, 350, 168000.0, 147000.0),   # Cement
            (1, 2, 3000, 2800, 216000.0, 201600.0), # Steel
            (1, 3, 10000, 9500, 90000.0, 85500.0),  # Bricks
            (1, 4, 80, 75, 144000.0, 135000.0),     # Sand
            (1, 5, 50, 48, 225000.0, 216000.0),     # Concrete RMC
            (1, 6, 1200, 1100, 72000.0, 66000.0),   # Tiles
            (1, 7, 60, 55, 144000.0, 132000.0),     # Teak Wood
            (1, 9, 30, 28, 58500.0, 54600.0),       # Wiring

            # Project 2: Metro City Commercial (Budget: 40 Lakhs) -> Approaching limit (~32.6 Lakhs material + 2.8 Lakhs labour = 35.4 Lakhs ~ 88.5%)
            (2, 1, 500, 520, 210000.0, 218400.0),   # Cement
            (2, 2, 4000, 4200, 288000.0, 302400.0), # Steel
            (2, 3, 12000, 12500, 108000.0, 112500.0),# Bricks
            (2, 4, 110, 115, 198000.0, 207000.0),   # Sand
            (2, 5, 70, 75, 315000.0, 337500.0),     # Concrete
            (2, 6, 1600, 1650, 96000.0, 99000.0),   # Tiles
            (2, 8, 250, 260, 62500.0, 65000.0),     # Paint

            # Project 3: Sunrise Residential (Budget: 18 Lakhs) -> Over budget (~17.5 Lakhs material + 2.2 Lakhs labour = 19.7 Lakhs ~ 109.4%)
            (3, 1, 300, 350, 126000.0, 147000.0),   # Cement
            (3, 2, 2500, 2900, 180000.0, 208800.0), # Steel
            (3, 3, 8000, 9200, 72000.0, 82800.0),   # Bricks
            (3, 4, 60, 70, 108000.0, 126000.0)      # Sand
        ]
        cursor.executemany("""
            INSERT INTO project_materials (project_id, material_id, planned_quantity, actual_quantity, estimated_cost, actual_cost)
            VALUES (?, ?, ?, ?, ?, ?);
        """, project_materials_data)

        # 5. MATERIAL DELIVERIES (22 records: Delivered, Pending, Partially Delivered)
        # (material_id, supplier_id, delivery_date, qty_received, unit_price, total_cost, status)
        deliveries_data = [
            (1, 1, "2024-01-20", 450, 420.0, 189000.0, "Delivered"),
            (1, 1, "2024-02-15", 450, 425.0, 191250.0, "Delivered"),
            (1, 1, "2024-03-10", 400, 420.0, 168000.0, "Delivered"),
            (1, 1, "2024-04-05", 200, 420.0, 84000.0, "Pending"),
            (2, 2, "2024-01-25", 3500, 72.0, 252000.0, "Delivered"),
            (2, 2, "2024-02-28", 3500, 73.0, 255500.0, "Delivered"),
            (2, 2, "2024-03-25", 3200, 72.0, 230400.0, "Delivered"),
            (2, 2, "2024-04-12", 1500, 72.5, 108750.0, "Partially Delivered"),
            (3, 4, "2024-01-22", 12000, 9.0, 108000.0, "Delivered"),
            (3, 4, "2024-02-18", 10000, 9.0, 90000.0, "Delivered"),
            (3, 4, "2024-03-15", 10000, 9.2, 92000.0, "Delivered"),
            (4, 3, "2024-01-28", 100, 1800.0, 180000.0, "Delivered"),
            (4, 3, "2024-02-22", 100, 1850.0, 185000.0, "Delivered"),
            (4, 3, "2024-03-20", 80, 1800.0, 144000.0, "Delivered"),
            (5, 1, "2024-02-05", 60, 4500.0, 270000.0, "Delivered"),
            (5, 1, "2024-03-02", 65, 4550.0, 295750.0, "Delivered"),
            (6, 5, "2024-02-12", 1500, 60.0, 90000.0, "Delivered"),
            (6, 5, "2024-03-18", 1500, 62.0, 93000.0, "Delivered"),
            (7, 2, "2024-02-25", 60, 2400.0, 144000.0, "Delivered"),
            (8, 5, "2024-03-05", 280, 250.0, 70000.0, "Delivered"),
            (9, 5, "2024-03-12", 35, 1950.0, 68250.0, "Delivered"),
            (10, 5, "2024-04-02", 40, 480.0, 19200.0, "Pending"),
            (12, 5, "2024-03-15", 100, 750.0, 75000.0, "Delivered")
        ]
        cursor.executemany("""
            INSERT INTO material_deliveries (material_id, supplier_id, delivery_date, quantity_received, unit_price, total_cost, status)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, deliveries_data)

        # 6. LABOUR RECORDS (14 records across 3 projects)
        # (project_id, worker_category, worker_count, hours_worked, hourly_rate, labor_date, total_cost, description)
        # total_cost = worker_count * hours_worked * hourly_rate
        labor_data = [
            # Project 1: Greenfield Luxury Villas
            (1, "Mason", 6, 40.0, 120.0, "2024-02-05", 6 * 40 * 120.0, "Foundation and brick masonry work"),
            (1, "Bar Bender", 4, 35.0, 130.0, "2024-02-12", 4 * 35 * 130.0, "Steel cutting and slab rebar bending"),
            (1, "Carpenter", 3, 40.0, 140.0, "2024-02-20", 3 * 40 * 140.0, "Centering and shuttering for ground floor roof"),
            (1, "General Helper", 8, 48.0, 80.0, "2024-02-26", 8 * 48 * 80.0, "Site clearance, material handling and curing"),
            (1, "Plumber", 2, 30.0, 150.0, "2024-03-10", 2 * 30 * 150.0, "Concealed sanitary piping layout"),

            # Project 2: Metro City Commercial Complex
            (2, "Mason", 10, 50.0, 125.0, "2024-02-15", 10 * 50 * 125.0, "Basement retaining wall construction"),
            (2, "Bar Bender", 8, 45.0, 135.0, "2024-02-22", 8 * 45 * 135.0, "Column cages and footing rebar binding"),
            (2, "Carpenter", 6, 50.0, 145.0, "2024-03-01", 6 * 50 * 145.0, "Slab framework and formwork erection"),
            (2, "Electrician", 4, 40.0, 150.0, "2024-03-15", 4 * 40 * 150.0, "Internal conduit laying and DB setting"),
            (2, "General Helper", 12, 50.0, 80.0, "2024-03-22", 12 * 50 * 80.0, "Heavy concrete batching and de-shuttering support"),

            # Project 3: Sunrise Residential Towers
            (3, "Mason", 8, 45.0, 120.0, "2024-03-10", 8 * 45 * 120.0, "Tower 1 1st floor brick partition walls"),
            (3, "Bar Bender", 6, 40.0, 130.0, "2024-03-18", 6 * 40 * 130.0, "Roof beam reinforcement tying"),
            (3, "Painter", 4, 35.0, 110.0, "2024-03-25", 4 * 35 * 110.0, "Undercoat wall primer and putty application"),
            (3, "General Helper", 10, 40.0, 80.0, "2024-03-30", 10 * 40 * 80.0, "Material transit and scaffold moving")
        ]
        cursor.executemany("""
            INSERT INTO labor (project_id, worker_category, worker_count, hours_worked, hourly_rate, labor_date, total_cost, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, labor_data)

        conn.commit()
    print("Sample data seeded successfully!")

def run_query(sql: str, params: tuple = (), db_path: str = DB_NAME) -> pd.DataFrame:
    """Executes a SQL query and returns the results as a Pandas DataFrame."""
    with get_connection(db_path) as conn:
        return pd.read_sql_query(sql, conn, params=params)

def execute_non_query(sql: str, params: tuple = (), db_path: str = DB_NAME) -> int:
    """Executes an INSERT, UPDATE, or DELETE query and returns rows affected."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount

if __name__ == "__main__":
    init_database()
    seed_sample_data()
    print("Database verification:")
    for tbl in ["materials", "suppliers", "projects", "material_deliveries", "labor", "project_materials"]:
        df = run_query(f"SELECT COUNT(*) as count FROM {tbl}")
        print(f" - {tbl}: {df['count'][0]} rows")
