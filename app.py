# ============================================================
#  UniGrant — app.py
#  Main Flask application entry point
# ============================================================

from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# ── Auto-migrate: ensure PDF columns exist ───────────────────
def run_migrations():
    from db import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    migrations = [
        "ALTER TABLE Proposals ADD COLUMN pdf_filename VARCHAR(255)",
        "ALTER TABLE Proposals ADD COLUMN pdf_data LONGBLOB",
        """CREATE TABLE IF NOT EXISTS ProgressUpdates (
            update_id        INT AUTO_INCREMENT PRIMARY KEY,
            proposal_id      INT NOT NULL,
            professor_id     INT NOT NULL,
            update_title     VARCHAR(200) NOT NULL,
            description      TEXT,
            amount_spent     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
            spending_category ENUM('Equipment','Travel','Personnel','Materials','Software','Other') DEFAULT 'Other',
            doc_filename     VARCHAR(255),
            doc_data         LONGBLOB,
            update_date      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proposal_id)  REFERENCES Proposals(proposal_id),
            FOREIGN KEY (professor_id) REFERENCES Professors(professor_id)
        )""",
    ]
    for sql in migrations:
        try:
            cursor.execute(sql)
        except Exception:
            pass  # Column already exists, skip
    conn.commit()
    cursor.close()
    conn.close()

try:
    run_migrations()
    print("✅ Database migrations checked.")
except Exception as e:
    print(f"⚠️ Migration warning: {e}")

# ── Register blueprints ─────────────────────────────────────
from routes.dashboard import dashboard_bp
from routes.proposals import proposals_bp
from routes.grants    import grants_bp
from routes.analytics import analytics_bp
from routes.progress  import progress_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(proposals_bp, url_prefix='/proposals')
app.register_blueprint(grants_bp,    url_prefix='/grants')
app.register_blueprint(analytics_bp, url_prefix='/analytics')
app.register_blueprint(progress_bp,  url_prefix='/progress')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)