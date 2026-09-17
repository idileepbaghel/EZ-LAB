from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import pymysql
from app.db import get_db_connection

# Create the authentication blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If the user is already logged in, redirect them to the dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard')) # Update this endpoint to match your dashboard route

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password_input = request.form.get('password', '')
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Simple query-based architecture
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user:
                # 1. Retrieve the BLOB password
                stored_password_blob = user['password']
                
                # 2. Decode the raw bytes back to a string
                if isinstance(stored_password_blob, (bytes, bytearray)):
                    stored_password = stored_password_blob.decode('utf-8')
                else:
                    stored_password = str(stored_password_blob)

                # 3. Compare the unhashed input to the decoded BLOB
                if password_input == stored_password:
                    
                    # 4. Store user details in the active Flask session
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['role'] = user['role']
                    session['name'] = user['name']
                    
                    return redirect(url_for('dashboard.dashboard')) 
                else:
                    flash("Incorrect password.", "error")
            else:
                flash("User not found.", "error")
                
        except pymysql.Error as err:
            flash(f"Database connection error: {err}", "error")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    # Clear the session data to log the user out
    session.clear()
    return redirect(url_for('auth.login'))