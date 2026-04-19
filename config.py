# ============================================================
#  UniGrant — config.py
#  All configuration settings for the Flask app
#  !! Change DB_PASSWORD to your MySQL root password !!
# ============================================================

class Config:
    # ── MySQL Database ───────────────────────────────────────
    DB_HOST     = 'localhost'
    DB_USER     = 'root'
    DB_PASSWORD = 'MAYur@0242'   # <-- change this
    DB_NAME     = 'unigrant'
    DB_PORT     = 3306

    # ── Flask ────────────────────────────────────────────────
    SECRET_KEY  = 'unigrant-secret-key-2024'
    DEBUG       = True