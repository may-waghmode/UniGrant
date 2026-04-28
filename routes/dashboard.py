# ============================================================
#  UniGrant — routes/dashboard.py
#  Login, page serving, and all API endpoints
# ============================================================

from flask import Blueprint, render_template, jsonify, request
from db import query, execute

dashboard_bp = Blueprint('dashboard', __name__)


# ── Page Routes ──────────────────────────────────────────────

@dashboard_bp.route('/')
def index():
    return render_template('login.html')

@dashboard_bp.route('/professor')
def professor_dashboard():
    return render_template('professor.html')

@dashboard_bp.route('/reviewer')
def reviewer_dashboard():
    return render_template('reviewer.html')

@dashboard_bp.route('/analytics-dashboard')
def analytics_dashboard():
    return render_template('analytics.html')


# ── Login ────────────────────────────────────────────────────

@dashboard_bp.route('/login', methods=['POST'])
def login():
    data    = request.get_json()
    role    = data.get('role')
    user_id = data.get('user_id')

    # ── Professor Google Login ───────────────────────────────
    if role == 'professor_google':
        email = data.get('email', '')
        name  = data.get('name', 'Professor')

        # Check if professor already exists
        user = query(
            "SELECT * FROM Professors WHERE email = %s",
            (email,), fetchone=True
        )

        if user:
            return jsonify({
                'success': True, 'role': 'professor',
                'name': user['full_name'], 'id': user['professor_id']
            })

        # New professor — find a valid dept and create
        dept = query("SELECT dept_id FROM Departments LIMIT 1", fetchone=True)
        if not dept:
            execute("INSERT INTO Departments (dept_name) VALUES ('General')")
            dept = query("SELECT dept_id FROM Departments LIMIT 1", fetchone=True)

        pid = execute(
            "INSERT INTO Professors (full_name, dept_id, email) VALUES (%s, %s, %s)",
            (name, dept['dept_id'], email)
        )
        return jsonify({
            'success': True, 'role': 'professor',
            'name': name, 'id': pid
        })

    # ── Reviewer Login ───────────────────────────────────────
    if role == 'reviewer':
        if user_id is None:
            return jsonify({'success': False, 'error': 'No reviewer selected'}), 400
        user = query(
            "SELECT * FROM Reviewers WHERE reviewer_id = %s",
            (int(user_id),), fetchone=True
        )
        if not user:
            return jsonify({'success': False, 'error': 'Reviewer not found'}), 404
        return jsonify({
            'success': True, 'role': 'reviewer',
            'name': user['full_name'], 'id': user['reviewer_id']
        })

    return jsonify({'success': False, 'error': 'Invalid role'}), 400


# ── API: Professor's own proposals ──────────────────────────

@dashboard_bp.route('/api/professor/<int:pid>/proposals')
def professor_proposals(pid):
    rows = query("""
        SELECT p.proposal_id, p.title, p.status, p.budget_requested,
               p.submission_date, p.pdf_filename,
               fa.amount_allocated, fa.amount_spent, fa.amount_remaining,
               a.decision, a.remarks, a.decision_date,
               r.full_name AS reviewer_name
        FROM   Proposals p
        LEFT JOIN FundAllocations fa ON p.proposal_id = fa.proposal_id
        LEFT JOIN Approvals       a  ON p.proposal_id = a.proposal_id
        LEFT JOIN Reviewers       r  ON a.reviewer_id = r.reviewer_id
        WHERE  p.professor_id = %s
        ORDER  BY p.submission_date DESC
    """, (pid,))
    for r in rows:
        r['submission_date']  = str(r['submission_date'])
        r['decision_date']    = str(r['decision_date']) if r.get('decision_date') else None
        r['budget_requested'] = float(r['budget_requested'])
        r['amount_allocated'] = float(r['amount_allocated']) if r.get('amount_allocated') else None
        r['amount_spent']     = float(r['amount_spent'])     if r.get('amount_spent')     else None
        r['amount_remaining'] = float(r['amount_remaining']) if r.get('amount_remaining') else None
    return jsonify(rows)


# ── API: Pending proposals for a specific reviewer ──────────

@dashboard_bp.route('/api/reviewer/pending')
def reviewer_pending():
    reviewer_id = request.args.get('reviewer_id')
    sql = """
        SELECT p.proposal_id, p.title, p.status, p.budget_requested,
               p.submission_date, p.description, p.pdf_filename,
               pr.full_name AS professor_name, d.dept_name AS department
        FROM   Proposals p
        JOIN   Professors  pr ON p.professor_id = pr.professor_id
        JOIN   Departments d  ON p.dept_id = d.dept_id
        WHERE  p.status IN ('Pending', 'Under Review')
    """
    params = []
    if reviewer_id:
        sql += " AND p.reviewer_id = %s"
        params.append(int(reviewer_id))

    rows = query(sql, params)
    for r in rows:
        r['submission_date']  = str(r['submission_date'])
        r['budget_requested'] = float(r['budget_requested'])
    return jsonify(rows)


# ── API: Reviewer decision history ──────────────────────────

@dashboard_bp.route('/api/reviewer/<int:rid>/history')
def reviewer_history(rid):
    rows = query("""
        SELECT a.approval_id, a.decision, a.remarks, a.decision_date,
               p.proposal_id, p.title, p.budget_requested,
               pr.full_name AS professor_name, d.dept_name AS department
        FROM   Approvals   a
        JOIN   Proposals   p  ON a.proposal_id  = p.proposal_id
        JOIN   Professors  pr ON p.professor_id = pr.professor_id
        JOIN   Departments d  ON p.dept_id      = d.dept_id
        WHERE  a.reviewer_id = %s
        ORDER  BY a.decision_date DESC
    """, (rid,))
    for r in rows:
        r['decision_date']    = str(r['decision_date'])
        r['budget_requested'] = float(r['budget_requested'])
    return jsonify(rows)


# ── API: Audit log ──────────────────────────────────────────

@dashboard_bp.route('/api/audit-log')
def audit_log():
    rows = query("""
        SELECT log_id, table_name, action, record_id,
               old_value, new_value, changed_at
        FROM   AuditLog ORDER BY changed_at DESC LIMIT 15
    """)
    for r in rows:
        r['changed_at'] = str(r['changed_at'])
    return jsonify(rows)


# ── API: Departments list ───────────────────────────────────

@dashboard_bp.route('/api/departments')
def departments():
    return jsonify(query("SELECT dept_id, dept_name FROM Departments"))


# ── API: Department summary ─────────────────────────────────

@dashboard_bp.route('/api/department-summary')
def department_summary():
    rows = query("SELECT * FROM department_summary")
    for r in rows:
        r['total_funding'] = float(r['total_funding'])
        r['total_spent']   = float(r['total_spent'])
    return jsonify(rows)


# ── API: Stats ──────────────────────────────────────────────

@dashboard_bp.route('/api/stats')
def stats():
    data = query("""
        SELECT COUNT(*) AS total_proposals,
               SUM(status='Approved') AS approved,
               SUM(status='Pending')  AS pending,
               SUM(status='Rejected') AS rejected
        FROM Proposals
    """, fetchone=True)
    budget = query(
        "SELECT COALESCE(SUM(amount_allocated),0) AS total_budget FROM FundAllocations",
        fetchone=True
    )
    return jsonify({**data, 'total_budget': float(budget['total_budget'])})