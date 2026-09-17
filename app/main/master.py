from flask import Blueprint, render_template, redirect, url_for, request, flash, session
import pymysql
from app.db import get_db_connection

master_bp = Blueprint('master',__name__)

@master_bp.route('/departments', methods=['GET', 'POST'])
def departments():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            code = request.form.get('code', '').strip() or None
            sort_order = request.form.get('sort_order', '0').strip()
            status = request.form.get('status', 'Active').strip()

            if not name:
                flash('Department name is required.', 'error')
                return redirect(url_for('master.departments'))

            try:
                sort_order = int(sort_order)
            except ValueError:
                flash('Sort order must be a valid number.', 'error')
                return redirect(url_for('master.departments'))

            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO departments
                    (name, code, sort_order, status, added_by)
                VALUES
                    (%s, %s, %s, %s, %s)
            """, (
                name,
                code,
                sort_order,
                status,
                session.get('name')
            ))

            conn.commit()

            flash('Department added successfully.', 'success')
            return redirect(url_for('master.departments'))

        except Exception as e:
            if 'conn' in locals():
                conn.rollback()

            print('\nException occurred while adding department:', e)
            flash('Unable to add department.', 'error')
            return redirect(url_for('master.departments'))

        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, code, sort_order, status "
            "FROM departments "
            "ORDER BY sort_order, id"
        )
        departments = cur.fetchall()
        return render_template(
            'departments.html',
            departments=departments
        )

    except Exception as e:
        print('\nException occurred at departments', e)
        flash('Unable to load departments.', 'error')
        return render_template(
            'departments.html',
            departments=[]
        )

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()