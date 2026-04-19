# ============================================================
#  UniGrant — routes/grants.py
#  Active grants + expense recording
# ============================================================

from flask import Blueprint, jsonify, request
from db import query, call_procedure

grants_bp = Blueprint('grants', __name__)


@grants_bp.route('/active')
def active_grants():
    """Fetch from active_grants view."""
    rows = query("SELECT * FROM active_grants")
    for r in rows:
        r['amount_allocated']  = float(r['amount_allocated'])
        r['amount_spent']      = float(r['amount_spent'])
        r['amount_remaining']  = float(r['amount_remaining'])
        r['utilization_pct']   = float(r['utilization_pct'])
        r['allocation_date']   = str(r['allocation_date'])
    return jsonify(rows)


@grants_bp.route('/expense', methods=['POST'])
def record_expense():
    """Record an expense — triggers auto-update the budget."""
    data = request.get_json()
    try:
        results = call_procedure('record_expense', [
            data['allocation_id'],
            data['amount'],
            data['category'],
            data['description']
        ])
        return jsonify({'success': True, 'message': results[0][0]['message'] if results else 'Recorded'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@grants_bp.route('/transactions/<int:allocation_id>')
def get_transactions(allocation_id):
    """All expenses for a given allocation."""
    rows = query("""
        SELECT txn_id, amount, category, description, txn_date
        FROM   Transactions
        WHERE  allocation_id = %s
        ORDER  BY txn_date DESC
    """, (allocation_id,))
    for r in rows:
        r['amount']   = float(r['amount'])
        r['txn_date'] = str(r['txn_date'])
    return jsonify(rows)