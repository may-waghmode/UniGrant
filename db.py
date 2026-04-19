# ============================================================
#  UniGrant — db.py
#  Database connection helper
# ============================================================

import mysql.connector
from config import Config


def get_connection():
    """Returns a new MySQL database connection."""
    return mysql.connector.connect(
        host     = Config.DB_HOST,
        user     = Config.DB_USER,
        password = Config.DB_PASSWORD,
        database = Config.DB_NAME,
        port     = Config.DB_PORT
    )


def query(sql, params=None, fetchone=False):
    """Run a SELECT query and return results as list of dicts."""
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params or ())
    result = cursor.fetchone() if fetchone else cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def execute(sql, params=None):
    """Run INSERT / UPDATE / DELETE. Returns last inserted row ID."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params or ())
    conn.commit()
    last_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return last_id


def call_procedure(proc_name, args=()):
    """Call a stored procedure. Returns all result sets."""
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.callproc(proc_name, args)
    results = []
    for result in cursor.stored_results():
        results.append(result.fetchall())
    conn.commit()
    cursor.close()
    conn.close()
    return results