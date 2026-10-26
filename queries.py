"""
queries.py
Complete catalog of all 44 required SQL queries for the
Construction Material Inventory & Structural Cost Estimation System.
Each query contains category, title, description, and executable SQL string.
"""

from typing import List, Dict, Any

SQL_QUERIES: List[Dict[str, Any]] = [
    # --- MATERIALS QUERIES (1-7) ---
    {
        "id": 1,
        "category": "Materials",
        "title": "Display All Materials",
        "description": "Retrieves all material records from the materials table sorted by material ID.",
        "sql": """SELECT material_id, material_name, category, unit, quantity_required, estimated_unit_cost, minimum_stock, description
FROM materials
ORDER BY material_id;"""
    },
    {
        "id": 2,
        "category": "Materials",
        "title": "Find Materials Belonging to a Specific Category",
        "description": "Filters materials belonging to the 'Cement' category using the WHERE clause.",
        "sql": """SELECT material_id, material_name, category, unit, estimated_unit_cost
FROM materials
WHERE category = 'Cement';"""
    },
    {
        "id": 3,
        "category": "Materials",
        "title": "Find Materials Costing More Than a Specified Amount",
        "description": "Filters materials where the estimated unit cost exceeds ₹500.",
        "sql": """SELECT material_id, material_name, category, unit, estimated_unit_cost
FROM materials
WHERE estimated_unit_cost > 500
ORDER BY estimated_unit_cost DESC;"""
    },
    {
        "id": 4,
        "category": "Materials",
        "title": "Display the Five Most Expensive Materials",
        "description": "Orders materials in descending order of unit cost and limits results to top 5.",
        "sql": """SELECT material_id, material_name, category, unit, estimated_unit_cost
FROM materials
ORDER BY estimated_unit_cost DESC
LIMIT 5;"""
    },
    {
        "id": 5,
        "category": "Materials",
        "title": "Find Materials Below Their Minimum Stock Threshold",
        "description": "Calculates physical stock (delivered minus consumed) and filters where stock is below minimum_stock threshold.",
        "sql": """SELECT 
    m.material_id, 
    m.material_name, 
    m.category, 
    m.unit,
    m.minimum_stock,
    COALESCE((SELECT SUM(d.quantity_received) FROM material_deliveries d WHERE d.material_id = m.material_id AND d.status = 'Delivered'), 0) -
    COALESCE((SELECT SUM(pm.actual_quantity) FROM project_materials pm WHERE pm.material_id = m.material_id), 0) AS current_physical_stock
FROM materials m
WHERE current_physical_stock < m.minimum_stock;"""
    },
    {
        "id": 6,
        "category": "Materials",
        "title": "Calculate the Average Estimated Material Price",
        "description": "Uses the AVG() aggregate function to determine average estimated unit cost across all materials.",
        "sql": """SELECT ROUND(AVG(estimated_unit_cost), 2) AS average_estimated_unit_cost
FROM materials;"""
    },
    {
        "id": 7,
        "category": "Materials",
        "title": "Count Materials in Each Category",
        "description": "Groups materials by category and calculates item count per category using COUNT() and GROUP BY.",
        "sql": """SELECT category, COUNT(*) AS total_materials
FROM materials
GROUP BY category
ORDER BY total_materials DESC;"""
    },

    # --- SUPPLIER QUERIES (8-12) ---
    {
        "id": 8,
        "category": "Suppliers",
        "title": "Display All Suppliers",
        "description": "Retrieves all registered supplier records with contact information and ratings.",
        "sql": """SELECT supplier_id, supplier_name, contact_person, phone, email, address, rating
FROM suppliers
ORDER BY supplier_id;"""
    },
    {
        "id": 9,
        "category": "Suppliers",
        "title": "Find Suppliers with a Rating Above a Specified Value",
        "description": "Filters top-tier suppliers having quality rating greater than or equal to 4.5.",
        "sql": """SELECT supplier_id, supplier_name, contact_person, phone, rating
FROM suppliers
WHERE rating >= 4.5
ORDER BY rating DESC;"""
    },
    {
        "id": 10,
        "category": "Suppliers",
        "title": "Calculate Total Spending by Supplier",
        "description": "Uses LEFT JOIN and SUM() to calculate total delivery expenditure committed to each supplier.",
        "sql": """SELECT 
    s.supplier_id, 
    s.supplier_name, 
    s.contact_person,
    ROUND(COALESCE(SUM(d.total_cost), 0), 2) AS total_spending
FROM suppliers s
LEFT JOIN material_deliveries d ON s.supplier_id = d.supplier_id
GROUP BY s.supplier_id, s.supplier_name, s.contact_person
ORDER BY total_spending DESC;"""
    },
    {
        "id": 11,
        "category": "Suppliers",
        "title": "Identify the Supplier with the Highest Delivery Spending",
        "description": "Finds the single vendor that has received the highest total purchase billing.",
        "sql": """SELECT 
    s.supplier_id, 
    s.supplier_name, 
    ROUND(SUM(d.total_cost), 2) AS total_delivery_spending
FROM suppliers s
JOIN material_deliveries d ON s.supplier_id = d.supplier_id
GROUP BY s.supplier_id, s.supplier_name
ORDER BY total_delivery_spending DESC
LIMIT 1;"""
    },
    {
        "id": 12,
        "category": "Suppliers",
        "title": "List Suppliers That Have No Delivery Records",
        "description": "Finds registered suppliers with zero purchase orders using LEFT JOIN and IS NULL filter.",
        "sql": """SELECT 
    s.supplier_id, 
    s.supplier_name, 
    s.contact_person, 
    s.phone, 
    s.email
FROM suppliers s
LEFT JOIN material_deliveries d ON s.supplier_id = d.supplier_id
WHERE d.delivery_id IS NULL;"""
    },

    # --- DELIVERY QUERIES (13-19) ---
    {
        "id": 13,
        "category": "Deliveries",
        "title": "Display All Deliveries",
        "description": "Lists all delivery records chronologically with material name, supplier name, and status.",
        "sql": """SELECT 
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
ORDER BY d.delivery_date DESC;"""
    },
    {
        "id": 14,
        "category": "Deliveries",
        "title": "Find Pending Deliveries",
        "description": "Filters delivery records where status is 'Pending' to track pipeline orders.",
        "sql": """SELECT 
    d.delivery_id, 
    m.material_name, 
    s.supplier_name, 
    d.delivery_date, 
    d.quantity_received AS quantity_ordered, 
    m.unit, 
    d.unit_price, 
    d.total_cost, 
    d.status
FROM material_deliveries d
JOIN materials m ON d.material_id = m.material_id
JOIN suppliers s ON d.supplier_id = s.supplier_id
WHERE d.status = 'Pending'
ORDER BY d.delivery_date ASC;"""
    },
    {
        "id": 15,
        "category": "Deliveries",
        "title": "Calculate Total Delivery Spending",
        "description": "Calculates overall, delivered, and pending material purchase financial commitments.",
        "sql": """SELECT 
    ROUND(SUM(total_cost), 2) AS overall_spending,
    ROUND(SUM(CASE WHEN status = 'Delivered' THEN total_cost ELSE 0 END), 2) AS delivered_spending,
    ROUND(SUM(CASE WHEN status = 'Pending' THEN total_cost ELSE 0 END), 2) AS pending_spending
FROM material_deliveries;"""
    },
    {
        "id": 16,
        "category": "Deliveries",
        "title": "Calculate Total Spending by Delivery Status",
        "description": "Aggregates count and total cost grouped by delivery status.",
        "sql": """SELECT 
    status, 
    COUNT(*) AS total_shipments, 
    ROUND(SUM(total_cost), 2) AS total_spending
FROM material_deliveries
GROUP BY status
ORDER BY total_spending DESC;"""
    },
    {
        "id": 17,
        "category": "Deliveries",
        "title": "Calculate Spending by Material",
        "description": "Computes cumulative procurement expenditure for each material item across all deliveries.",
        "sql": """SELECT 
    m.material_id, 
    m.material_name, 
    m.category, 
    ROUND(SUM(d.total_cost), 2) AS total_delivery_spending
FROM materials m
JOIN material_deliveries d ON m.material_id = d.material_id
GROUP BY m.material_id, m.material_name, m.category
ORDER BY total_delivery_spending DESC;"""
    },
    {
        "id": 18,
        "category": "Deliveries",
        "title": "Calculate Spending by Supplier",
        "description": "Aggregates delivery quantity count and total billings per vendor.",
        "sql": """SELECT 
    s.supplier_id, 
    s.supplier_name, 
    COUNT(d.delivery_id) AS delivery_count, 
    ROUND(SUM(d.total_cost), 2) AS total_spent
FROM suppliers s
JOIN material_deliveries d ON s.supplier_id = d.supplier_id
GROUP BY s.supplier_id, s.supplier_name
ORDER BY total_spent DESC;"""
    },
    {
        "id": 19,
        "category": "Deliveries",
        "title": "Find Deliveries Within a Selected Date Range",
        "description": "Filters deliveries executed between February 1, 2024 and March 31, 2024 using BETWEEN operator.",
        "sql": """SELECT 
    d.delivery_id, 
    m.material_name, 
    s.supplier_name, 
    d.delivery_date, 
    d.quantity_received, 
    d.total_cost, 
    d.status
FROM material_deliveries d
JOIN materials m ON d.material_id = m.material_id
JOIN suppliers s ON d.supplier_id = s.supplier_id
WHERE d.delivery_date BETWEEN '2024-02-01' AND '2024-03-31'
ORDER BY d.delivery_date ASC;"""
    },

    # --- LABOUR QUERIES (20-24) ---
    {
        "id": 20,
        "category": "Labour",
        "title": "Display All Labour Records",
        "description": "Retrieves all labour shifts and site activities with worker categories, counts, and costs.",
        "sql": """SELECT 
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
ORDER BY l.labor_date DESC;"""
    },
    {
        "id": 21,
        "category": "Labour",
        "title": "Calculate Total Labour Expenditure",
        "description": "Aggregates overall site labour expenditure across all projects and shifts.",
        "sql": """SELECT ROUND(SUM(total_cost), 2) AS total_labor_expenditure
FROM labor;"""
    },
    {
        "id": 22,
        "category": "Labour",
        "title": "Calculate Labour Expenditure by Worker Category",
        "description": "Groups labour costs and total hours by trade (Mason, Bar Bender, Carpenter, etc.).",
        "sql": """SELECT 
    worker_category, 
    SUM(worker_count) AS total_workforce_count, 
    ROUND(SUM(hours_worked), 1) AS total_hours, 
    ROUND(SUM(total_cost), 2) AS total_expenditure
FROM labor
GROUP BY worker_category
ORDER BY total_expenditure DESC;"""
    },
    {
        "id": 23,
        "category": "Labour",
        "title": "Calculate Labour Expenditure by Project",
        "description": "Computes project-level labour overheads to measure human resource cost distribution.",
        "sql": """SELECT 
    p.project_id, 
    p.project_name, 
    COUNT(l.labor_id) AS logged_shifts, 
    ROUND(SUM(l.total_cost), 2) AS total_project_labor_cost
FROM projects p
JOIN labor l ON p.project_id = l.project_id
GROUP BY p.project_id, p.project_name
ORDER BY total_project_labor_cost DESC;"""
    },
    {
        "id": 24,
        "category": "Labour",
        "title": "Identify the Worker Category with the Highest Expenditure",
        "description": "Identifies the highest cost labour trade across all construction works.",
        "sql": """SELECT 
    worker_category, 
    ROUND(SUM(total_cost), 2) AS total_expenditure
FROM labor
GROUP BY worker_category
ORDER BY total_expenditure DESC
LIMIT 1;"""
    },

    # --- PROJECT QUERIES (25-33) ---
    {
        "id": 25,
        "category": "Projects",
        "title": "Display All Projects",
        "description": "Lists all construction projects with location, schedule, and allocated budget.",
        "sql": """SELECT project_id, project_name, client_name, location, start_date, expected_end_date, estimated_budget, project_status
FROM projects
ORDER BY project_id;"""
    },
    {
        "id": 26,
        "category": "Projects",
        "title": "Find Projects Above a Specified Budget",
        "description": "Filters large capital projects with estimated budget greater than ₹2,000,000.",
        "sql": """SELECT project_id, project_name, client_name, location, estimated_budget, project_status
FROM projects
WHERE estimated_budget > 2000000
ORDER BY estimated_budget DESC;"""
    },
    {
        "id": 27,
        "category": "Projects",
        "title": "Calculate Planned Material Costs by Project",
        "description": "Sums planned baseline material costs per project from project_materials table.",
        "sql": """SELECT 
    p.project_id, 
    p.project_name, 
    ROUND(SUM(pm.estimated_cost), 2) AS planned_material_cost
FROM projects p
JOIN project_materials pm ON p.project_id = pm.project_id
GROUP BY p.project_id, p.project_name
ORDER BY planned_material_cost DESC;"""
    },
    {
        "id": 28,
        "category": "Projects",
        "title": "Calculate Actual Material Costs by Project",
        "description": "Sums actual incurred material expenses per project from project_materials table.",
        "sql": """SELECT 
    p.project_id, 
    p.project_name, 
    ROUND(SUM(pm.actual_cost), 2) AS actual_material_cost
FROM projects p
JOIN project_materials pm ON p.project_id = pm.project_id
GROUP BY p.project_id, p.project_name
ORDER BY actual_material_cost DESC;"""
    },
    {
        "id": 29,
        "category": "Projects",
        "title": "Calculate Labour Costs by Project",
        "description": "Calculates total direct labour expenditure recorded for each construction project.",
        "sql": """SELECT 
    p.project_id, 
    p.project_name, 
    ROUND(COALESCE(SUM(l.total_cost), 0), 2) AS actual_labor_cost
FROM projects p
LEFT JOIN labor l ON p.project_id = l.project_id
GROUP BY p.project_id, p.project_name
ORDER BY actual_labor_cost DESC;"""
    },
    {
        "id": 30,
        "category": "Projects",
        "title": "Compare Estimated and Actual Expenses",
        "description": "Compares project estimated budget against total actual expenditure (materials + labour) and computes cost variance.",
        "sql": """SELECT 
    p.project_id, 
    p.project_name, 
    p.estimated_budget, 
    ROUND(COALESCE(mat.actual_mat_cost, 0), 2) AS actual_material_cost, 
    ROUND(COALESCE(lab.actual_lab_cost, 0), 2) AS actual_labor_cost, 
    ROUND(COALESCE(mat.actual_mat_cost, 0) + COALESCE(lab.actual_lab_cost, 0), 2) AS total_actual_cost, 
    ROUND((COALESCE(mat.actual_mat_cost, 0) + COALESCE(lab.actual_lab_cost, 0)) - p.estimated_budget, 2) AS variance
FROM projects p
LEFT JOIN (SELECT project_id, SUM(actual_cost) AS actual_mat_cost FROM project_materials GROUP BY project_id) mat ON p.project_id = mat.project_id
LEFT JOIN (SELECT project_id, SUM(total_cost) AS actual_lab_cost FROM labor GROUP BY project_id) lab ON p.project_id = lab.project_id;"""
    },
    {
        "id": 31,
        "category": "Projects",
        "title": "Calculate Remaining Project Budgets",
        "description": "Calculates remaining unspent fiscal balances per project (estimated_budget - total_actual_cost).",
        "sql": """SELECT 
    p.project_id, 
    p.project_name, 
    p.estimated_budget, 
    ROUND(COALESCE(mat.actual_mat_cost, 0) + COALESCE(lab.actual_lab_cost, 0), 2) AS total_actual_cost, 
    ROUND(p.estimated_budget - (COALESCE(mat.actual_mat_cost, 0) + COALESCE(lab.actual_lab_cost, 0)), 2) AS remaining_budget
FROM projects p
LEFT JOIN (SELECT project_id, SUM(actual_cost) AS actual_mat_cost FROM project_materials GROUP BY project_id) mat ON p.project_id = mat.project_id
LEFT JOIN (SELECT project_id, SUM(total_cost) AS actual_lab_cost FROM labor GROUP BY project_id) lab ON p.project_id = lab.project_id;"""
    },
    {
        "id": 32,
        "category": "Projects",
        "title": "Identify Projects Exceeding Their Budgets",
        "description": "Filters projects whose cumulative actual expenditure exceeds their assigned budget.",
        "sql": """SELECT 
    p.project_id, 
    p.project_name, 
    p.estimated_budget, 
    ROUND(COALESCE(mat.actual_mat_cost, 0) + COALESCE(lab.actual_lab_cost, 0), 2) AS total_actual_cost, 
    ROUND((COALESCE(mat.actual_mat_cost, 0) + COALESCE(lab.actual_lab_cost, 0)) - p.estimated_budget, 2) AS budget_overrun
FROM projects p
LEFT JOIN (SELECT project_id, SUM(actual_cost) AS actual_mat_cost FROM project_materials GROUP BY project_id) mat ON p.project_id = mat.project_id
LEFT JOIN (SELECT project_id, SUM(total_cost) AS actual_lab_cost FROM labor GROUP BY project_id) lab ON p.project_id = lab.project_id
WHERE (COALESCE(mat.actual_mat_cost, 0) + COALESCE(lab.actual_lab_cost, 0)) > p.estimated_budget;"""
    },
    {
        "id": 33,
        "category": "Projects",
        "title": "Calculate Budget Utilization Percentages",
        "description": "Computes (actual_cost / estimated_budget) * 100 with zero division safeguard.",
        "sql": """SELECT 
    p.project_id, 
    p.project_name, 
    p.estimated_budget, 
    ROUND(COALESCE(mat.actual_mat_cost, 0) + COALESCE(lab.actual_lab_cost, 0), 2) AS total_actual_cost, 
    ROUND(((COALESCE(mat.actual_mat_cost, 0) + COALESCE(lab.actual_lab_cost, 0)) / CASE WHEN p.estimated_budget = 0 THEN 1 ELSE p.estimated_budget END) * 100, 2) AS utilization_percentage
FROM projects p
LEFT JOIN (SELECT project_id, SUM(actual_cost) AS actual_mat_cost FROM project_materials GROUP BY project_id) mat ON p.project_id = mat.project_id
LEFT JOIN (SELECT project_id, SUM(total_cost) AS actual_lab_cost FROM labor GROUP BY project_id) lab ON p.project_id = lab.project_id;"""
    },

    # --- JOIN QUERIES (34-38) ---
    {
        "id": 34,
        "category": "Joins",
        "title": "Join Materials with Delivery Records",
        "description": "INNER JOIN combining material specifications with delivery history and status.",
        "sql": """SELECT 
    d.delivery_id, 
    m.material_name, 
    m.category, 
    d.quantity_received, 
    m.unit, 
    d.unit_price, 
    d.total_cost, 
    d.delivery_date, 
    d.status
FROM material_deliveries d
INNER JOIN materials m ON d.material_id = m.material_id
ORDER BY d.delivery_date DESC;"""
    },
    {
        "id": 35,
        "category": "Joins",
        "title": "Join Suppliers with Delivery Records",
        "description": "INNER JOIN linking vendors to their delivered shipments and total purchase invoices.",
        "sql": """SELECT 
    d.delivery_id, 
    s.supplier_name, 
    s.contact_person, 
    s.phone, 
    d.delivery_date, 
    d.total_cost, 
    d.status
FROM material_deliveries d
INNER JOIN suppliers s ON d.supplier_id = s.supplier_id
ORDER BY d.delivery_date DESC;"""
    },
    {
        "id": 36,
        "category": "Joins",
        "title": "Join Projects with Labour Records",
        "description": "INNER JOIN detailing worker trades, daily shifts, and hourly billings tied to specific construction sites.",
        "sql": """SELECT 
    l.labor_id, 
    p.project_name, 
    l.worker_category, 
    l.worker_count, 
    l.hours_worked, 
    l.hourly_rate, 
    l.total_cost, 
    l.labor_date
FROM labor l
INNER JOIN projects p ON l.project_id = p.project_id
ORDER BY l.labor_date DESC;"""
    },
    {
        "id": 37,
        "category": "Joins",
        "title": "Join Projects, Project Materials, and Material Information",
        "description": "Three-table join providing complete visibility into planned vs actual material usage by project.",
        "sql": """SELECT 
    pm.project_material_id, 
    p.project_name, 
    m.material_name, 
    m.category, 
    pm.planned_quantity, 
    pm.actual_quantity, 
    m.unit, 
    pm.estimated_cost, 
    pm.actual_cost
FROM project_materials pm
INNER JOIN projects p ON pm.project_id = p.project_id
INNER JOIN materials m ON pm.material_id = m.material_id
ORDER BY p.project_id, pm.project_material_id;"""
    },
    {
        "id": 38,
        "category": "Joins",
        "title": "Create a Combined Project Expense Report",
        "description": "Consolidates project budget, material costs, and labour costs using pre-aggregated subqueries to prevent row multiplication and double counting.",
        "sql": """WITH MatExp AS (
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
    p.estimated_budget, 
    COALESCE(MatExp.est_mat, 0) AS planned_material_cost, 
    COALESCE(MatExp.act_mat, 0) AS actual_material_cost, 
    COALESCE(LabExp.act_lab, 0) AS actual_labor_cost, 
    (COALESCE(MatExp.act_mat, 0) + COALESCE(LabExp.act_lab, 0)) AS total_actual_expense, 
    (p.estimated_budget - (COALESCE(MatExp.act_mat, 0) + COALESCE(LabExp.act_lab, 0))) AS remaining_budget
FROM projects p
LEFT JOIN MatExp ON p.project_id = MatExp.project_id
LEFT JOIN LabExp ON p.project_id = LabExp.project_id
ORDER BY p.project_id;"""
    },

    # --- ADVANCED QUERIES (39-44) ---
    {
        "id": 39,
        "category": "Advanced",
        "title": "Find Materials Whose Estimated Cost Exceeds Overall Average",
        "description": "Scalar subquery in WHERE clause filtering materials costing more than the global mean unit cost.",
        "sql": """SELECT 
    material_id, 
    material_name, 
    category, 
    estimated_unit_cost, 
    (SELECT ROUND(AVG(estimated_unit_cost), 2) FROM materials) AS overall_avg_cost
FROM materials
WHERE estimated_unit_cost > (SELECT AVG(estimated_unit_cost) FROM materials)
ORDER BY estimated_unit_cost DESC;"""
    },
    {
        "id": 40,
        "category": "Advanced",
        "title": "Find Projects Whose Expenditure Exceeds Average Project Expenditure",
        "description": "Uses Common Table Expressions (CTE) and subqueries to filter projects consuming above average capital.",
        "sql": """WITH ProjectTotals AS (
    SELECT 
        p.project_id, 
        p.project_name, 
        (COALESCE((SELECT SUM(actual_cost) FROM project_materials WHERE project_id = p.project_id), 0) + 
         COALESCE((SELECT SUM(total_cost) FROM labor WHERE project_id = p.project_id), 0)) AS total_expenditure
    FROM projects p
)
SELECT 
    project_id, 
    project_name, 
    total_expenditure, 
    (SELECT ROUND(AVG(total_expenditure), 2) FROM ProjectTotals) AS avg_project_expenditure
FROM ProjectTotals
WHERE total_expenditure > (SELECT AVG(total_expenditure) FROM ProjectTotals);"""
    },
    {
        "id": 41,
        "category": "Advanced",
        "title": "Use CASE to Classify Budget Status",
        "description": "Classifies projects into 'Within Budget' (<80%), 'Near Budget Limit' (80-100%), and 'Over Budget' (>100%) using CASE expressions.",
        "sql": """WITH ProjectTotals AS (
    SELECT 
        p.project_id, 
        p.project_name, 
        p.estimated_budget, 
        (COALESCE((SELECT SUM(actual_cost) FROM project_materials WHERE project_id = p.project_id), 0) + 
         COALESCE((SELECT SUM(total_cost) FROM labor WHERE project_id = p.project_id), 0)) AS total_actual_cost
    FROM projects p
)
SELECT 
    project_id, 
    project_name, 
    estimated_budget, 
    total_actual_cost, 
    ROUND((total_actual_cost / CASE WHEN estimated_budget = 0 THEN 1 ELSE estimated_budget END) * 100, 2) AS utilization_percentage, 
    CASE 
        WHEN (total_actual_cost / CASE WHEN estimated_budget = 0 THEN 1 ELSE estimated_budget END) * 100 < 80 THEN 'Within Budget' 
        WHEN (total_actual_cost / CASE WHEN estimated_budget = 0 THEN 1 ELSE estimated_budget END) * 100 <= 100 THEN 'Near Budget Limit' 
        ELSE 'Over Budget' 
    END AS budget_status
FROM ProjectTotals;"""
    },
    {
        "id": 42,
        "category": "Advanced",
        "title": "Use GROUP BY and HAVING to Find High-Spending Suppliers",
        "description": "Groups deliveries by vendor and uses HAVING clause to filter vendors with aggregate billings exceeding ₹300,000.",
        "sql": """SELECT 
    s.supplier_id, 
    s.supplier_name, 
    COUNT(d.delivery_id) AS delivery_count, 
    ROUND(SUM(d.total_cost), 2) AS total_spending
FROM suppliers s
JOIN material_deliveries d ON s.supplier_id = d.supplier_id
GROUP BY s.supplier_id, s.supplier_name
HAVING total_spending > 300000
ORDER BY total_spending DESC;"""
    },
    {
        "id": 43,
        "category": "Advanced",
        "title": "Use a Subquery to Identify the Most Expensive Material",
        "description": "Subquery finding material record matching MAX(estimated_unit_cost).",
        "sql": """SELECT material_id, material_name, category, unit, estimated_unit_cost
FROM materials
WHERE estimated_unit_cost = (SELECT MAX(estimated_unit_cost) FROM materials);"""
    },
    {
        "id": 44,
        "category": "Advanced",
        "title": "Demonstrate a Transaction for Updating Related Financial Records",
        "description": "Demonstrates an atomic financial transaction updating actual quantities and costs safely.",
        "sql": """-- Demonstrated in Python using conn.execute('BEGIN TRANSACTION;')
-- Example transaction query:
SELECT 
    pm.project_material_id, 
    p.project_name, 
    m.material_name, 
    pm.planned_quantity, 
    pm.actual_quantity, 
    pm.estimated_cost, 
    pm.actual_cost
FROM project_materials pm
JOIN projects p ON pm.project_id = p.project_id
JOIN materials m ON pm.material_id = m.material_id
WHERE pm.project_material_id = 1;"""
    }
]

def get_queries_by_category(category: str) -> List[Dict[str, Any]]:
    return [q for q in SQL_QUERIES if q["category"].lower() == category.lower()]

def get_all_categories() -> List[str]:
    cats = []
    for q in SQL_QUERIES:
        if q["category"] not in cats:
            cats.append(q["category"])
    return cats
