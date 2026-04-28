# ============================================================
#  UniGrant — routes/progress.py
#  Progress tracking & spending updates for approved proposals
# ============================================================

from flask import Blueprint, jsonify, request, send_file
from db import query, execute, call_procedure, get_connection
import io

progress_bp = Blueprint('progress', __name__)


@progress_bp.route('/submit', methods=['POST'])
def submit_progress():
    """Submit a progress update with optional document proof."""
    if request.content_type and 'multipart' in request.content_type:
        proposal_id   = int(request.form.get('proposal_id', 0))
        professor_id  = int(request.form.get('professor_id', 0))
        update_title  = request.form.get('update_title', '')
        description   = request.form.get('description', '')
        amount_spent  = float(request.form.get('amount_spent', 0))
        category      = request.form.get('category', 'Other')
        doc_file      = request.files.get('doc_file')
    else:
        data          = request.get_json()
        proposal_id   = int(data.get('proposal_id', 0))
        professor_id  = int(data.get('professor_id', 0))
        update_title  = data.get('update_title', '')
        description   = data.get('description', '')
        amount_spent  = float(data.get('amount_spent', 0))
        category      = data.get('category', 'Other')
        doc_file      = None

    if not proposal_id or not update_title or amount_spent <= 0:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    try:
        # Call the stored procedure to record progress + auto-update spending
        results = call_procedure('record_progress', [
            proposal_id, professor_id, update_title,
            description, amount_spent, category
        ])

        # If a document was uploaded, attach it to the progress update
        if doc_file and doc_file.filename:
            # Get the newly inserted progress update id
            latest = query(
                "SELECT update_id FROM ProgressUpdates WHERE proposal_id = %s AND professor_id = %s ORDER BY update_id DESC LIMIT 1",
                (proposal_id, professor_id), fetchone=True
            )
            if latest:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE ProgressUpdates SET doc_filename = %s, doc_data = %s WHERE update_id = %s",
                    (doc_file.filename, doc_file.read(), latest['update_id'])
                )
                conn.commit()
                cursor.close()
                conn.close()

        msg = results[0][0]['message'] if results and results[0] else 'Progress recorded'
        return jsonify({'success': True, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@progress_bp.route('/list/<int:proposal_id>')
def get_progress(proposal_id):
    """Get all progress updates for a proposal."""
    rows = query("""
        SELECT pu.update_id, pu.update_title, pu.description,
               pu.amount_spent, pu.spending_category, pu.doc_filename,
               pu.update_date, pr.full_name AS professor_name
        FROM   ProgressUpdates pu
        JOIN   Professors pr ON pu.professor_id = pr.professor_id
        WHERE  pu.proposal_id = %s
        ORDER  BY pu.update_date DESC
    """, (proposal_id,))
    for r in rows:
        r['amount_spent'] = float(r['amount_spent'])
        r['update_date']  = str(r['update_date'])
    return jsonify(rows)


@progress_bp.route('/spending-summary/<int:proposal_id>')
def spending_summary(proposal_id):
    """Get spending summary with category breakdown for a proposal."""
    # Overall spending
    overall = query("""
        SELECT fa.amount_allocated, fa.amount_spent, fa.amount_remaining,
               ROUND((fa.amount_spent / fa.amount_allocated) * 100, 1) AS utilization_pct,
               COUNT(pu.update_id) AS total_updates
        FROM   FundAllocations fa
        LEFT JOIN ProgressUpdates pu ON fa.proposal_id = pu.proposal_id
        WHERE  fa.proposal_id = %s
        GROUP BY fa.allocation_id
    """, (proposal_id,), fetchone=True)

    if not overall:
        return jsonify({'error': 'No allocation found'}), 404

    overall['amount_allocated'] = float(overall['amount_allocated'])
    overall['amount_spent']     = float(overall['amount_spent'])
    overall['amount_remaining'] = float(overall['amount_remaining'])
    overall['utilization_pct']  = float(overall['utilization_pct']) if overall['utilization_pct'] else 0

    # Category breakdown
    categories = query("""
        SELECT spending_category, SUM(amount_spent) AS total, COUNT(*) AS entries
        FROM   ProgressUpdates
        WHERE  proposal_id = %s
        GROUP BY spending_category
        ORDER BY total DESC
    """, (proposal_id,))
    for c in categories:
        c['total'] = float(c['total'])

    return jsonify({
        'overall': overall,
        'categories': categories
    })


@progress_bp.route('/doc/<int:update_id>')
def download_doc(update_id):
    """Download the proof document attached to a progress update."""
    row = query(
        "SELECT doc_filename, doc_data FROM ProgressUpdates WHERE update_id = %s",
        (update_id,), fetchone=True
    )
    if not row or not row['doc_data']:
        return jsonify({'error': 'No document found'}), 404

    return send_file(
        io.BytesIO(row['doc_data']),
        mimetype='application/octet-stream',
        as_attachment=True,
        download_name=row['doc_filename'] or f'proof_{update_id}.pdf'
    )
