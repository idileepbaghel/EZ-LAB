from flask import Blueprint, render_template, redirect, url_for, request, flash, session
import pymysql
from app.db import get_db_connection
from .helpers import exists_department

master_bp = Blueprint('master',__name__)

@master_bp.route('/departments', methods=['GET', 'POST'])
def departments():
    if request.method == 'POST':
        try:
            action = request.form.get('action', 'create').strip()
            if action == 'delete':
                department_id = request.form.get('department_id', '').strip()

                if not department_id:
                    flash('Invalid department.', 'error')
                    return redirect(url_for('master.departments'))

                try:
                    department_id = int(department_id)
                except ValueError:
                    flash('Invalid department.', 'error')
                    return redirect(url_for('master.departments'))

                conn = get_db_connection()
                cur = conn.cursor()

                cur.execute("""
                    SELECT id
                    FROM departments
                    WHERE id = %s
                    LIMIT 1
                """, (department_id,))

                department = cur.fetchone()

                if not department:
                    flash('Department not found.', 'error')
                    return redirect(url_for('master.departments'))

                cur.execute("""
                    DELETE FROM departments
                    WHERE id = %s
                """, (department_id,))

                conn.commit()

                flash('Department deleted successfully.', 'success')
                return redirect(url_for('master.departments'))

            
            name = request.form.get('name', '').strip()
            code = request.form.get('code', '').strip() or None
            department_type = request.form.get('type', 'laboratory').strip()
            sort_order = request.form.get('sort_order', '0').strip()
            status = request.form.get('status', 'Active').strip()

            if not name or not code:
                flash('Department name and code are required.', 'error')
                return redirect(url_for('master.departments'))

            if department_type not in ['laboratory', 'pathology', 'radiology', 'consultation']:
                flash('Invalid department type.', 'error')
                return redirect(url_for('master.departments'))

            try:
                sort_order = int(sort_order)
            except ValueError:
                flash('Sort order must be a valid number.', 'error')
                return redirect(url_for('master.departments'))

            conn = get_db_connection()
            cur = conn.cursor()

            if action == 'edit':
                department_id = request.form.get('department_id', '').strip()

                if not department_id:
                    flash('Invalid department.', 'error')
                    return redirect(url_for('master.departments'))

                try:
                    department_id = int(department_id)
                except ValueError:
                    flash('Invalid department.', 'error')
                    return redirect(url_for('master.departments'))

                cur.execute("""
                    SELECT id
                    FROM departments
                    WHERE (name = %s OR code = %s)
                      AND id != %s
                    LIMIT 1
                """, (
                    name,
                    code,
                    department_id
                ))

                existing_department = cur.fetchone()

                if existing_department:
                    flash('Department name or code already exists.', 'error')
                    return redirect(url_for('master.departments'))

                cur.execute("""
                    UPDATE departments
                    SET
                        name = %s,
                        code = %s,
                        type = %s,
                        sort_order = %s,
                        status = %s,
                        updated_by = %s
                    WHERE id = %s
                """, (
                    name,
                    code,
                    department_type,
                    sort_order,
                    status,
                    session.get('name'),
                    department_id
                ))

                conn.commit()

                flash('Department updated successfully.', 'success')
                return redirect(url_for('master.departments'))

            if exists_department(name, code):
                flash('Department name or code already exists.', 'error')
                return redirect(url_for('master.departments'))

            cur.execute("""
                INSERT INTO departments
                    (name, code, type, sort_order, status, added_by)
                VALUES
                    (%s, %s, %s, %s, %s, %s)
            """, (
                name,
                code,
                department_type,
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

            print('\nException occurred while saving department:', e)
            flash('Unable to save department.', 'error')
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
            "SELECT id, name, code, type, sort_order, status "
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
            cur.close()
            conn.close()


@master_bp.route('/units', methods=['GET', 'POST'])
def units():
    if request.method == 'POST':
        conn = None
        cur = None

        try:
            action = request.form.get('action', 'create').strip()

            conn = get_db_connection()
            cur = conn.cursor()

            if action == 'create':
                unit_name = request.form.get('unit_name', '').strip()
                status = request.form.get('status', 'Active').strip()

                if not unit_name:
                    flash('Unit name is required.', 'error')
                    return redirect(url_for('master.units'))

                if status not in ['Active', 'Inactive']:
                    flash('Invalid unit status.', 'error')
                    return redirect(url_for('master.units'))

                cur.execute("""
                    SELECT id
                    FROM ezlab_result_units
                    WHERE unit_name = %s
                    LIMIT 1
                """, (unit_name,))

                existing_unit = cur.fetchone()

                if existing_unit:
                    flash('Unit name already exists.', 'error')
                    return redirect(url_for('master.units'))

                cur.execute("""
                    INSERT INTO ezlab_result_units
                        (unit_name, status, added_by)
                    VALUES
                        (%s, %s, %s)
                """, (
                    unit_name,
                    status,
                    session.get('name')
                ))

                conn.commit()

                flash('Unit added successfully.', 'success')
                return redirect(url_for('master.units'))

            if action == 'edit':
                unit_id = request.form.get('unit_id', '').strip()
                unit_name = request.form.get('unit_name', '').strip()
                status = request.form.get('status', 'Active').strip()

                if not unit_id:
                    flash('Invalid unit.', 'error')
                    return redirect(url_for('master.units'))

                try:
                    unit_id = int(unit_id)
                except ValueError:
                    flash('Invalid unit.', 'error')
                    return redirect(url_for('master.units'))

                if not unit_name:
                    flash('Unit name is required.', 'error')
                    return redirect(url_for('master.units'))

                if status not in ['Active', 'Inactive']:
                    flash('Invalid unit status.', 'error')
                    return redirect(url_for('master.units'))

                cur.execute("""
                    SELECT id
                    FROM ezlab_result_units
                    WHERE unit_name = %s
                      AND id != %s
                    LIMIT 1
                """, (
                    unit_name,
                    unit_id
                ))

                existing_unit = cur.fetchone()

                if existing_unit:
                    flash('Unit name already exists.', 'error')
                    return redirect(url_for('master.units'))

                cur.execute("""
                    UPDATE ezlab_result_units
                    SET
                        unit_name = %s,
                        status = %s,
                        updated_by = %s
                    WHERE id = %s
                """, (
                    unit_name,
                    status,
                    session.get('name'),
                    unit_id
                ))

                conn.commit()

                flash('Unit updated successfully.', 'success')
                return redirect(url_for('master.units'))

            if action == 'delete':
                unit_id = request.form.get('unit_id', '').strip()

                if not unit_id:
                    flash('Invalid unit.', 'error')
                    return redirect(url_for('master.units'))

                try:
                    unit_id = int(unit_id)
                except ValueError:
                    flash('Invalid unit.', 'error')
                    return redirect(url_for('master.units'))

                cur.execute("""
                    SELECT id
                    FROM ezlab_result_units
                    WHERE id = %s
                    LIMIT 1
                """, (unit_id,))

                existing_unit = cur.fetchone()

                if not existing_unit:
                    flash('Unit not found.', 'error')
                    return redirect(url_for('master.units'))

                cur.execute("""
                    DELETE FROM ezlab_result_units
                    WHERE id = %s
                """, (unit_id,))

                conn.commit()

                flash('Unit deleted successfully.', 'success')
                return redirect(url_for('master.units'))

            flash('Invalid action.', 'error')
            return redirect(url_for('master.units'))

        except Exception as e:
            if conn:
                conn.rollback()

            print('\nException occurred while saving unit:', e)
            flash('Unable to save unit.', 'error')
            return redirect(url_for('master.units'))

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    conn = None
    cur = None

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                unit_name,
                status
            FROM ezlab_result_units
            ORDER BY unit_name
        """)

        units = cur.fetchall()

        return render_template(
            'units.html',
            units=units
        )

    except Exception as e:
        print('\nException at units:', e)
        flash('Unable to load units.', 'error')

        return render_template(
            'units.html',
            units=[]
        )

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@master_bp.route('/samples', methods=['GET', 'POST'])
def samples():
    if request.method == 'POST':
        try:
            action = request.form.get('action', 'create').strip()

            conn = get_db_connection()
            cur = conn.cursor()

            if action == 'create':
                sample_type = request.form.get('sample_type', '').strip()
                sample_color = request.form.get('sample_color', '').strip() or None
                status = request.form.get('status', 'Active').strip()

                if not sample_type:
                    flash('Sample type is required.', 'error')
                    return redirect(url_for('master.samples'))

                if status not in ['Active', 'Inactive']:
                    flash('Invalid sample status.', 'error')
                    return redirect(url_for('master.samples'))

                cur.execute("""
                    SELECT id
                    FROM ezlab_sample_types
                    WHERE sample_type = %s
                    LIMIT 1
                """, (sample_type,))

                existing_sample = cur.fetchone()

                if existing_sample:
                    flash('Sample type already exists.', 'error')
                    return redirect(url_for('master.samples'))

                cur.execute("""
                    INSERT INTO ezlab_sample_types
                        (sample_type, sample_color, status, added_by)
                    VALUES
                        (%s, %s, %s, %s)
                """, (
                    sample_type,
                    sample_color,
                    status,
                    session.get('name')
                ))

                conn.commit()

                flash('Sample added successfully.', 'success')
                return redirect(url_for('master.samples'))

            if action == 'edit':
                sample_id = request.form.get('sample_id', '').strip()
                sample_type = request.form.get('sample_type', '').strip()
                sample_color = request.form.get('sample_color', '').strip() or None
                status = request.form.get('status', 'Active').strip()

                if not sample_id:
                    flash('Invalid sample.', 'error')
                    return redirect(url_for('master.samples'))

                try:
                    sample_id = int(sample_id)
                except ValueError:
                    flash('Invalid sample.', 'error')
                    return redirect(url_for('master.samples'))

                if not sample_type:
                    flash('Sample type is required.', 'error')
                    return redirect(url_for('master.samples'))

                if status not in ['Active', 'Inactive']:
                    flash('Invalid sample status.', 'error')
                    return redirect(url_for('master.samples'))

                cur.execute("""
                    SELECT id
                    FROM ezlab_sample_types
                    WHERE sample_type = %s
                      AND id != %s
                    LIMIT 1
                """, (
                    sample_type,
                    sample_id
                ))

                existing_sample = cur.fetchone()

                if existing_sample:
                    flash('Sample type already exists.', 'error')
                    return redirect(url_for('master.samples'))

                cur.execute("""
                    UPDATE ezlab_sample_types
                    SET
                        sample_type = %s,
                        sample_color = %s,
                        status = %s,
                        updated_by = %s
                    WHERE id = %s
                """, (
                    sample_type,
                    sample_color,
                    status,
                    session.get('name'),
                    sample_id
                ))

                conn.commit()

                flash('Sample updated successfully.', 'success')
                return redirect(url_for('master.samples'))

            if action == 'delete':
                sample_id = request.form.get('sample_id', '').strip()

                if not sample_id:
                    flash('Invalid sample.', 'error')
                    return redirect(url_for('master.samples'))

                try:
                    sample_id = int(sample_id)
                except ValueError:
                    flash('Invalid sample.', 'error')
                    return redirect(url_for('master.samples'))

                cur.execute("""
                    SELECT id
                    FROM ezlab_sample_types
                    WHERE id = %s
                    LIMIT 1
                """, (sample_id,))

                existing_sample = cur.fetchone()

                if not existing_sample:
                    flash('Sample not found.', 'error')
                    return redirect(url_for('master.samples'))

                cur.execute("""
                    DELETE FROM ezlab_sample_types
                    WHERE id = %s
                """, (sample_id,))

                conn.commit()

                flash('Sample deleted successfully.', 'success')
                return redirect(url_for('master.samples'))

            flash('Invalid action.', 'error')
            return redirect(url_for('master.samples'))

        except Exception as e:
            if conn:
                conn.rollback()

            print('\nException occurred while saving sample:', e)
            flash('Unable to save sample.', 'error')
            return redirect(url_for('master.samples'))

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    # GET
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                sample_type,
                sample_color,
                status
            FROM ezlab_sample_types
            ORDER BY sample_type
        """)

        samples = cur.fetchall()

        return render_template(
            'samples.html',
            samples=samples
        )

    except Exception as e:
        print('\nException at samples:', e)
        flash('Unable to load samples.', 'error')

        return render_template(
            'samples.html',
            samples=[]
        )

    finally:
        cur.close()
        conn.close()


@master_bp.route('/tests', methods=['GET', 'POST'])
def tests():
    conn = None
    cur = None

    if request.method == 'POST':
        try:
            action = request.form.get('action', 'create').strip()

            conn = get_db_connection()
            cur = conn.cursor()

            if action == 'create':
                test_name = request.form.get('test_name', '').strip()
                test_code = request.form.get('test_code', '').strip()
                price = request.form.get('price', '').strip()
                department_id = request.form.get('department_id', '').strip()
                sample_id = request.form.get('sample_id', '').strip()
                status = request.form.get('status', 'Active').strip()

                if not test_name or not test_code or not price or not department_id or not sample_id:
                    flash('All test details are required.', 'error')
                    return redirect(url_for('master.tests'))

                if status not in ['Active', 'Inactive']:
                    flash('Invalid test status.', 'error')
                    return redirect(url_for('master.tests'))

                try:
                    department_id = int(department_id)
                    sample_id = int(sample_id)
                except ValueError:
                    flash('Invalid department or sample.', 'error')
                    return redirect(url_for('master.tests'))

                try:
                    price = float(price)
                except ValueError:
                    flash('Price must be a valid number.', 'error')
                    return redirect(url_for('master.tests'))

                if price < 0:
                    flash('Price cannot be negative.', 'error')
                    return redirect(url_for('master.tests'))

                cur.execute("""
                    SELECT id
                    FROM departments
                    WHERE id = %s
                    LIMIT 1
                """, (department_id,))

                department = cur.fetchone()

                if not department:
                    flash('Department not found.', 'error')
                    return redirect(url_for('master.tests'))

                cur.execute("""
                    SELECT id, sample_type
                    FROM ezlab_sample_types
                    WHERE id = %s
                    LIMIT 1
                """, (sample_id,))

                sample = cur.fetchone()

                if not sample:
                    flash('Sample not found.', 'error')
                    return redirect(url_for('master.tests'))

                cur.execute("""
                    SELECT id
                    FROM ezlab_tests
                    WHERE test_code = %s
                    LIMIT 1
                """, (test_code,))

                existing_test = cur.fetchone()

                if existing_test:
                    flash('Test code already exists.', 'error')
                    return redirect(url_for('master.tests'))

                cur.execute("""
                    INSERT INTO ezlab_tests
                        (
                            department_id,
                            test_name,
                            test_code,
                            sample_type,
                            price,
                            status,
                            added_by
                        )
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    department_id,
                    test_name,
                    test_code,
                    sample['sample_type'],
                    price,
                    status,
                    session.get('name')
                ))

                conn.commit()

                flash('Test added successfully.', 'success')
                return redirect(url_for('master.tests'))

            if action == 'edit':
                test_id = request.form.get('test_id', '').strip()
                test_name = request.form.get('test_name', '').strip()
                test_code = request.form.get('test_code', '').strip()
                price = request.form.get('price', '').strip()
                department_id = request.form.get('department_id', '').strip()
                sample_id = request.form.get('sample_id', '').strip()
                status = request.form.get('status', 'Active').strip()

                if not test_id:
                    flash('Invalid test.', 'error')
                    return redirect(url_for('master.tests'))

                try:
                    test_id = int(test_id)
                except ValueError:
                    flash('Invalid test.', 'error')
                    return redirect(url_for('master.tests'))

                if not test_name or not test_code or not price or not department_id or not sample_id:
                    flash('All test details are required.', 'error')
                    return redirect(url_for('master.tests'))

                if status not in ['Active', 'Inactive']:
                    flash('Invalid test status.', 'error')
                    return redirect(url_for('master.tests'))

                try:
                    department_id = int(department_id)
                    sample_id = int(sample_id)
                except ValueError:
                    flash('Invalid department or sample.', 'error')
                    return redirect(url_for('master.tests'))

                try:
                    price = float(price)
                except ValueError:
                    flash('Price must be a valid number.', 'error')
                    return redirect(url_for('master.tests'))

                if price < 0:
                    flash('Price cannot be negative.', 'error')
                    return redirect(url_for('master.tests'))

                cur.execute("""
                    SELECT id
                    FROM ezlab_tests
                    WHERE id = %s
                    LIMIT 1
                """, (test_id,))

                existing_test = cur.fetchone()

                if not existing_test:
                    flash('Test not found.', 'error')
                    return redirect(url_for('master.tests'))

                cur.execute("""
                    SELECT id
                    FROM ezlab_tests
                    WHERE test_code = %s
                      AND id != %s
                    LIMIT 1
                """, (
                    test_code,
                    test_id
                ))

                duplicate_test = cur.fetchone()

                if duplicate_test:
                    flash('Test code already exists.', 'error')
                    return redirect(url_for('master.tests'))

                cur.execute("""
                    SELECT id
                    FROM departments
                    WHERE id = %s
                    LIMIT 1
                """, (department_id,))

                department = cur.fetchone()

                if not department:
                    flash('Department not found.', 'error')
                    return redirect(url_for('master.tests'))

                cur.execute("""
                    SELECT id, sample_type
                    FROM ezlab_sample_types
                    WHERE id = %s
                    LIMIT 1
                """, (sample_id,))

                sample = cur.fetchone()

                if not sample:
                    flash('Sample not found.', 'error')
                    return redirect(url_for('master.tests'))

                cur.execute("""
                    UPDATE ezlab_tests
                    SET
                        department_id = %s,
                        test_name = %s,
                        test_code = %s,
                        sample_type = %s,
                        price = %s,
                        status = %s,
                        updated_by = %s
                    WHERE id = %s
                """, (
                    department_id,
                    test_name,
                    test_code,
                    sample['sample_type'],
                    price,
                    status,
                    session.get('name'),
                    test_id
                ))

                conn.commit()

                flash('Test updated successfully.', 'success')
                return redirect(url_for('master.tests'))

            if action == 'delete':
                test_id = request.form.get('test_id', '').strip()

                if not test_id:
                    flash('Invalid test.', 'error')
                    return redirect(url_for('master.tests'))

                try:
                    test_id = int(test_id)
                except ValueError:
                    flash('Invalid test.', 'error')
                    return redirect(url_for('master.tests'))

                cur.execute("""
                    SELECT id
                    FROM ezlab_tests
                    WHERE id = %s
                    LIMIT 1
                """, (test_id,))

                existing_test = cur.fetchone()

                if not existing_test:
                    flash('Test not found.', 'error')
                    return redirect(url_for('master.tests'))

                cur.execute("""
                    DELETE FROM ezlab_tests
                    WHERE id = %s
                """, (test_id,))

                conn.commit()

                flash('Test deleted successfully.', 'success')
                return redirect(url_for('master.tests'))

            flash('Invalid action.', 'error')
            return redirect(url_for('master.tests'))

        except Exception as e:
            if conn:
                conn.rollback()

            print('\nException occurred while saving test:', e)
            flash('Unable to save test.', 'error')
            return redirect(url_for('master.tests'))

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                t.id,
                t.department_id,
                t.test_name,
                t.test_code,
                t.sample_type,
                t.price,
                t.status,
                d.name AS department_name,
                s.id AS sample_id
            FROM ezlab_tests t
            LEFT JOIN departments d
                ON d.id = t.department_id
            LEFT JOIN ezlab_sample_types s
                ON s.sample_type = t.sample_type
            ORDER BY t.test_name
        """)

        tests = cur.fetchall()

        cur.execute("""
            SELECT
                id,
                name
            FROM departments
            ORDER BY name
        """)

        departments = cur.fetchall()

        cur.execute("""
            SELECT
                id,
                sample_type
            FROM ezlab_sample_types
            ORDER BY sample_type
        """)

        samples = cur.fetchall()

        return render_template(
            'tests.html',
            tests=tests,
            departments=departments,
            samples=samples
        )

    except Exception as e:
        print('\nException at tests:', e)
        flash('Unable to load tests.', 'error')

        return render_template(
            'tests.html',
            tests=[],
            departments=[],
            samples=[]
        )

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()