# ============================================================
#  UniGrant — routes/proposals.py
#  Proposal CRUD + approval/rejection + PDF upload
# ============================================================

from flask import Blueprint, jsonify, request, send_file
from db import query, execute, call_procedure
import io

proposals_bp = Blueprint('proposals', __name__)


@proposals_bp.route('/', methods=['GET'])
def get_proposals():
    """Return all proposals with optional status filter."""
    status = request.args.get('status')
    if status and status != 'All':
        rows = query("""
            SELECT p.proposal_id, p.title, p.status, p.budget_requested,
                   p.submission_date, pr.full_name AS professor_name,
                   d.dept_name AS department
            FROM   Proposals p
            JOIN   Professors  pr ON p.professor_id = pr.professor_id
            JOIN   Departments d  ON p.dept_id      = d.dept_id
            WHERE  p.status = %s
            ORDER  BY p.submission_date DESC
        """, (status,))
    else:
        rows = query("""
            SELECT p.proposal_id, p.title, p.status, p.budget_requested,
                   p.submission_date, pr.full_name AS professor_name,
                   d.dept_name AS department
            FROM   Proposals p
            JOIN   Professors  pr ON p.professor_id = pr.professor_id
            JOIN   Departments d  ON p.dept_id      = d.dept_id
            ORDER  BY p.submission_date DESC
        """)
    for r in rows:
        r['submission_date']  = str(r['submission_date'])
        r['budget_requested'] = float(r['budget_requested'])
    return jsonify(rows)


@proposals_bp.route('/submit', methods=['POST'])
def submit():
    """Submit a new proposal with optional PDF attachment."""
    # Handle both JSON and multipart form data
    if request.content_type and 'multipart' in request.content_type:
        title        = request.form.get('title', '')
        description  = request.form.get('description', '')
        budget       = float(request.form.get('budget', 0))
        professor_id = int(request.form.get('professor_id', 0))
        dept_id      = int(request.form.get('dept_id', 0))
        reviewer_id  = request.form.get('reviewer_id')
        pdf_file     = request.files.get('pdf_file')
    else:
        data         = request.get_json()
        title        = data.get('title', '')
        description  = data.get('description', '')
        budget       = float(data.get('budget', 0))
        professor_id = int(data.get('professor_id', 0))
        dept_id      = int(data.get('dept_id', 0))
        reviewer_id  = data.get('reviewer_id')
        pdf_file     = None

    try:
        # Call stored procedure
        results = call_procedure('submit_proposal', [
            title, description, budget, professor_id, dept_id
        ])

        # Update the row with reviewer_id and PDF data
        if reviewer_id or pdf_file:
            # Get the newly inserted proposal id
            latest = query(
                "SELECT proposal_id FROM Proposals WHERE professor_id = %s ORDER BY proposal_id DESC LIMIT 1",
                (professor_id,), fetchone=True
            )
            if latest:
                pid = latest['proposal_id']

                if reviewer_id:
                    execute("UPDATE Proposals SET reviewer_id = %s WHERE proposal_id = %s",
                            (int(reviewer_id), pid))

                if pdf_file and pdf_file.filename:
                    pdf_bytes = pdf_file.read()
                    pdf_name  = pdf_file.filename
                    from db import get_connection
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE Proposals SET pdf_filename = %s, pdf_data = %s WHERE proposal_id = %s",
                        (pdf_name, pdf_bytes, pid)
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()

        msg = results[0][0]['message'] if results and results[0] else 'Proposal submitted'
        return jsonify({'success': True, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@proposals_bp.route('/pdf/<int:proposal_id>')
def download_pdf(proposal_id):
    """Download the PDF attached to a proposal."""
    row = query(
        "SELECT pdf_filename, pdf_data FROM Proposals WHERE proposal_id = %s",
        (proposal_id,), fetchone=True
    )
    if not row or not row['pdf_data']:
        return jsonify({'error': 'No PDF found for this proposal'}), 404

    return send_file(
        io.BytesIO(row['pdf_data']),
        mimetype='application/pdf',
        as_attachment=False,
        download_name=row['pdf_filename'] or f'proposal_{proposal_id}.pdf'
    )


@proposals_bp.route('/approve', methods=['POST'])
def approve():
    """Approve a proposal via stored procedure."""
    data = request.get_json()
    try:
        results = call_procedure('approve_proposal', [
            int(data['proposal_id']),
            int(data['reviewer_id']),
            float(data['amount']),
            data.get('remarks', 'Approved')
        ])
        msg = results[0][0]['message'] if results and results[0] else 'Approved'
        return jsonify({'success': True, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@proposals_bp.route('/reject', methods=['POST'])
def reject():
    """Reject a proposal via stored procedure."""
    data = request.get_json()
    try:
        results = call_procedure('reject_proposal', [
            int(data['proposal_id']),
            int(data['reviewer_id']),
            data.get('remarks', 'Rejected')
        ])
        msg = results[0][0]['message'] if results and results[0] else 'Rejected'
        return jsonify({'success': True, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@proposals_bp.route('/reviewers')
def list_reviewers():
    return jsonify(query("SELECT reviewer_id, full_name, designation FROM Reviewers"))


@proposals_bp.route('/professors')
def list_professors():
    rows = query("""
        SELECT p.professor_id, p.full_name, d.dept_name
        FROM Professors p JOIN Departments d ON p.dept_id = d.dept_id
    """)
    return jsonify(rows)