import pymysql
from app.db import get_db_connection

# * Existing Checks

# to check if a department exists
def exists_department(name, code):
    if not name or not code:
        return False

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM departments
            WHERE name = %s OR code = %s
            """,
            (name,code))

        rows = cur.fetchone()
        if rows is not None:
            return True # exists

    except Exception as e:
        print('Exception occurred at exists_department', e)

    finally:
        cur.close()
        conn.close()

    return False # does not exist




