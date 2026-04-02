# ============================================================
#  UniGrant — routes/dashboard.py
# ============================================================
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from db import query

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    return render_template('login.html')


@dashboard_bp.route('/login', methods=['POST'])
def login():
    data     = request.get_json()
    role     = data.get('role')
    user_id  = int(data.get('user_id'))

    if role == 'professor':
        user = query("SELECT * FROM Professors WHERE professor_id = %s", (user_id,), fetchone=True)
        if not user:
            return jsonify({'success': False, 'error': 'Professor not found'}), 404
        return jsonify({'success': True, 'role': 'professor',
                        'name': user['full_name'], 'id': user['professor_id']})

    elif role == 'reviewer':
        user = query("SELECT * FROM Reviewers WHERE reviewer_id = %s", (user_id,), fetchone=True)
        if not user:
            return jsonify({'success': False, 'error': 'Reviewer not found'}), 404
        return jsonify({'success': True, 'role': 'reviewer',
                        'name': user['full_name'], 'id': user['reviewer_id']})

    return jsonify({'success': False, 'error': 'Invalid role'}), 400


@dashboard_bp.route('/professor')
def professor_dashboard():
    return render_template('professor.html')


@dashboard_bp.route('/reviewer')
def reviewer_dashboard():
    return render_template('reviewer.html')


# ── API: Admin overview stats ────────────────────────────────
@dashboard_bp.route('/api/stats')
def stats():
    data   = query("""
        SELECT COUNT(*) AS total_proposals,
               SUM(status='Approved') AS approved,
               SUM(status='Pending')  AS pending,
               SUM(status='Rejected') AS rejected
        FROM Proposals
    """, fetchone=True)
    budget = query("SELECT COALESCE(SUM(amount_allocated),0) AS total_budget FROM FundAllocations", fetchone=True)
    return jsonify({**data, 'total_budget': float(budget['total_budget'])})


# ── API: Professor's own proposals ──────────────────────────
@dashboard_bp.route('/api/professor/<int:pid>/proposals')
def professor_proposals(pid):
    rows = query("""
        SELECT p.proposal_id, p.title, p.status, p.budget_requested,
               p.submission_date,
               fa.amount_allocated, fa.amount_spent, fa.amount_remaining,
               ROUND((fa.amount_spent/fa.amount_allocated)*100,1) AS utilization_pct,
               a.decision, a.remarks, a.decision_date,
               r.full_name AS reviewer_name
        FROM   Proposals p
        LEFT JOIN FundAllocations fa ON p.proposal_id  = fa.proposal_id
        LEFT JOIN Approvals        a  ON p.proposal_id  = a.proposal_id
        LEFT JOIN Reviewers        r  ON a.reviewer_id  = r.reviewer_id
        WHERE  p.professor_id = %s
        ORDER  BY p.submission_date DESC
    """, (pid,))
    for r in rows:
        r['submission_date'] = str(r['submission_date'])
        r['decision_date']   = str(r['decision_date'])   if r['decision_date']   else None
        r['budget_requested']= float(r['budget_requested'])
        r['amount_allocated']= float(r['amount_allocated']) if r['amount_allocated'] else None
        r['amount_spent']    = float(r['amount_spent'])     if r['amount_spent']     else None
        r['amount_remaining']= float(r['amount_remaining']) if r['amount_remaining'] else None
    return jsonify(rows)


# ── API: Pending proposals for reviewer ─────────────────────
@dashboard_bp.route('/api/reviewer/pending')
def reviewer_pending():
    rows = query("SELECT * FROM pending_proposals")
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
        JOIN   Proposals   p  ON a.proposal_id   = p.proposal_id
        JOIN   Professors  pr ON p.professor_id  = pr.professor_id
        JOIN   Departments d  ON p.dept_id       = d.dept_id
        WHERE  a.reviewer_id = %s
        ORDER  BY a.decision_date DESC
    """, (rid,))
    for r in rows:
        r['decision_date']   = str(r['decision_date'])
        r['budget_requested']= float(r['budget_requested'])
    return jsonify(rows)


# ── API: Audit log ───────────────────────────────────────────
@dashboard_bp.route('/api/audit-log')
def audit_log():
    rows = query("""
        SELECT log_id, table_name, action, record_id, old_value, new_value, changed_at
        FROM AuditLog ORDER BY changed_at DESC LIMIT 10
    """)
    for r in rows:
        r['changed_at'] = str(r['changed_at'])
    return jsonify(rows)


# ── API: Departments list (for submit form) ──────────────────
@dashboard_bp.route('/api/departments')
def departments():
    return jsonify(query("SELECT dept_id, dept_name FROM Departments"))


# ── API: Department summary ──────────────────────────────────
@dashboard_bp.route('/api/department-summary')
def department_summary():
    rows = query("SELECT * FROM department_summary")
    for r in rows:
        r['total_funding'] = float(r['total_funding'])
        r['total_spent']   = float(r['total_spent'])
    return jsonify(rows)