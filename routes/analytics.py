# ============================================================
#  UniGrant — routes/analytics.py
#  Advanced analytics using SQL Window Functions
# ============================================================

from flask import Blueprint, jsonify
from db import query

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/budget-rankings')
def budget_rankings():
    """Return proposals ranked by budget using RANK, DENSE_RANK, PERCENT_RANK."""
    rows = query("SELECT * FROM vw_budget_rankings ORDER BY overall_rank")
    for r in rows:
        r['budget_requested'] = float(r['budget_requested'])
        r['percentile']       = float(r['percentile'])
    return jsonify(rows)


@analytics_bp.route('/running-totals')
def running_totals():
    """Return cumulative fund allocation over time."""
    rows = query("SELECT * FROM vw_running_totals ORDER BY allocation_date")
    for r in rows:
        r['amount_allocated'] = float(r['amount_allocated'])
        r['cumulative_total'] = float(r['cumulative_total'])
        r['dept_cumulative']  = float(r['dept_cumulative'])
        r['moving_avg_3']     = float(r['moving_avg_3']) if r.get('moving_avg_3') else None
        r['allocation_date']  = str(r['allocation_date'])
    return jsonify(rows)


@analytics_bp.route('/professor-analytics')
def professor_analytics():
    """Professor-level analytics: submission order, quartiles, budget changes."""
    rows = query("SELECT * FROM vw_professor_analytics ORDER BY professor_name, submission_order")
    for r in rows:
        r['budget_requested'] = float(r['budget_requested'])
        r['submission_date']  = str(r['submission_date'])
        r['prev_budget']      = float(r['prev_budget']) if r.get('prev_budget') else None
        r['next_budget']      = float(r['next_budget']) if r.get('next_budget') else None
        r['budget_change']    = float(r['budget_change']) if r.get('budget_change') else 0
    return jsonify(rows)


@analytics_bp.route('/dept-window-stats')
def dept_window_stats():
    """Department-level stats with window function rankings."""
    rows = query("SELECT * FROM vw_dept_window_stats")
    for r in rows:
        r['total_requested']   = float(r['total_requested'])
        r['avg_budget']        = float(r['avg_budget'])
        r['pct_of_total_budget'] = float(r['pct_of_total_budget']) if r['pct_of_total_budget'] else 0
    return jsonify(rows)


@analytics_bp.route('/event-scheduler-status')
def event_scheduler_status():
    """Check the status of MySQL event scheduler and list events."""
    try:
        scheduler = query("SHOW VARIABLES LIKE 'event_scheduler'", fetchone=True)
        events = query("SELECT EVENT_NAME, EVENT_TYPE, INTERVAL_VALUE, INTERVAL_FIELD, STATUS, LAST_EXECUTED FROM INFORMATION_SCHEMA.EVENTS WHERE EVENT_SCHEMA = 'unigrant'")
        for e in events:
            e['LAST_EXECUTED'] = str(e['LAST_EXECUTED']) if e.get('LAST_EXECUTED') else 'Not yet'
        return jsonify({
            'scheduler_enabled': scheduler.get('Value', 'OFF') if scheduler else 'OFF',
            'events': events
        })
    except Exception as e:
        return jsonify({'scheduler_enabled': 'UNKNOWN', 'events': [], 'error': str(e)})


@analytics_bp.route('/index-info')
def index_info():
    """List all custom indexes on the unigrant database."""
    rows = query("""
        SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME, NON_UNIQUE, INDEX_TYPE
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = 'unigrant'
          AND INDEX_NAME != 'PRIMARY'
        ORDER BY TABLE_NAME, INDEX_NAME
    """)
    return jsonify(rows)


@analytics_bp.route('/user-privileges')
def user_privileges():
    """Show the GRANT/REVOKE setup for all UniGrant MySQL users."""
    users = [
        {'username': 'unigrant_professor', 'role': 'Professor', 'description': 'SELECT + INSERT on Proposals only'},
        {'username': 'unigrant_reviewer',  'role': 'Reviewer',  'description': 'SELECT + UPDATE on Proposals, INSERT Approvals'},
        {'username': 'unigrant_admin',     'role': 'Admin',     'description': 'ALL PRIVILEGES on unigrant.*'},
        {'username': 'unigrant_auditor',   'role': 'Auditor',   'description': 'SELECT only (read-only access)'},
    ]
    result = []
    for u in users:
        try:
            grants = query(f"SHOW GRANTS FOR '{u['username']}'@'localhost'")
            grant_stmts = [list(g.values())[0] for g in grants] if grants else []
        except Exception:
            grant_stmts = ['User not created yet — run workbench_setup.sql first']
        result.append({
            'username': u['username'],
            'role': u['role'],
            'description': u['description'],
            'grants': grant_stmts
        })
    return jsonify(result)
