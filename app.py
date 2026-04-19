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

app.register_blueprint(dashboard_bp)
app.register_blueprint(proposals_bp, url_prefix='/proposals')
app.register_blueprint(grants_bp,    url_prefix='/grants')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)