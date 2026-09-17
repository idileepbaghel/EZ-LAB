from flask import Blueprint, render_template, session, redirect, url_for
from datetime import date
from app.db import get_db_connection

# Create the dashboard blueprint
dashboard_bp = Blueprint('dashboard', __name__)

# The endpoint='index' explicitly names this route so url_for('dashboard.index') works
@dashboard_bp.route('/', endpoint='index')
@dashboard_bp.route('/dashboard')
def dashboard():
    # Protect the route - check if user is in session
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Initialize default empty stats so the template doesn't crash 
    # before we create the rest of the database tables.
    stats = {
        "patients_total": 0,
        "appointments_today": 0,
        "lab_pending": 0,
        "invoices_unpaid": 0,
    }
    recent_patients = []
    today_appts = []
    pending_orders = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # ---------------------------------------------------------
        # 1. Fetch Dashboard Stats
        # ---------------------------------------------------------
        try:
            cursor.execute("SELECT COUNT(*) as count FROM patient")
            stats['patients_total'] = cursor.fetchone()['count']
        except: pass  # Fails silently if 'patient' table doesn't exist yet

        try:
            cursor.execute("SELECT COUNT(*) as count FROM appointment WHERE appt_date = %s", (date.today(),))
            stats['appointments_today'] = cursor.fetchone()['count']
        except: pass

        try:
            cursor.execute("SELECT COUNT(*) as count FROM lab_order WHERE status != 'Completed'")
            stats['lab_pending'] = cursor.fetchone()['count']
        except: pass

        try:
            cursor.execute("SELECT COUNT(*) as count FROM invoice WHERE status != 'Paid'")
            stats['invoices_unpaid'] = cursor.fetchone()['count']
        except: pass

        # ---------------------------------------------------------
        # 2. Fetch Recent Data for Tables
        # ---------------------------------------------------------
        try:
            cursor.execute("SELECT * FROM patient ORDER BY created_at DESC LIMIT 5")
            recent_patients = cursor.fetchall()
        except: pass

        try:
            cursor.execute("SELECT * FROM appointment WHERE appt_date = %s ORDER BY appt_time", (date.today(),))
            today_appts = cursor.fetchall()
        except: pass

        try:
            cursor.execute("SELECT * FROM lab_order WHERE status != 'Completed' ORDER BY created_at DESC LIMIT 5")
            pending_orders = cursor.fetchall()
        except: pass

    except Exception as e:
        print(f"Database error on dashboard: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_patients=recent_patients,
        today_appts=today_appts,
        pending_orders=pending_orders
    )