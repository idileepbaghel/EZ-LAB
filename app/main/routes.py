from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager

main_bp = Blueprint("main", __name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Staff(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(60), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(40), default="Front Desk")

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mrn = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(160), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.String(255))
    blood_group = db.Column(db.String(6))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship("Appointment", backref="patient", lazy=True, cascade="all, delete-orphan")
    lab_orders = db.relationship("LabOrder", backref="patient", lazy=True, cascade="all, delete-orphan")
    invoices = db.relationship("Invoice", backref="patient", lazy=True, cascade="all, delete-orphan")

    def age(self):
        today = date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    department = db.Column(db.String(80), nullable=False)
    doctor = db.Column(db.String(120), nullable=False)
    appt_date = db.Column(db.Date, nullable=False)
    appt_time = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default="Scheduled")  # Scheduled / Checked In / Completed / Cancelled
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LabTestCatalog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    sample_type = db.Column(db.String(40), nullable=False)
    turnaround_hours = db.Column(db.Integer, default=24)
    price = db.Column(db.Float, nullable=False)


class LabOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    ordered_by = db.Column(db.String(120), nullable=False)
    priority = db.Column(db.String(10), default="Routine")  # Routine / Urgent / STAT
    status = db.Column(db.String(20), default="Sample Pending")  # Sample Pending / In Progress / Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("LabOrderItem", backref="order", lazy=True, cascade="all, delete-orphan")


class LabOrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("lab_order.id"), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey("lab_test_catalog.id"), nullable=False)
    status = db.Column(db.String(20), default="Pending")  # Pending / Collected / Resulted
    result_value = db.Column(db.String(255))
    result_flag = db.Column(db.String(20))  # Normal / High / Low / Critical
    result_notes = db.Column(db.String(255))
    resulted_at = db.Column(db.DateTime)

    test = db.relationship("LabTestCatalog")


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    status = db.Column(db.String(20), default="Unpaid")  # Unpaid / Partially Paid / Paid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("InvoiceItem", backref="invoice", lazy=True, cascade="all, delete-orphan")
    payments = db.relationship("Payment", backref="invoice", lazy=True, cascade="all, delete-orphan")

    def total(self):
        return sum(i.amount() for i in self.items)

    def paid(self):
        return sum(p.amount for p in self.payments)

    def balance(self):
        return round(self.total() - self.paid(), 2)


class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    description = db.Column(db.String(160), nullable=False)
    qty = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, nullable=False)

    def amount(self):
        return round(self.qty * self.unit_price, 2)


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(30), default="Cash")
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return Staff.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def next_code(prefix, model, field):
    count = model.query.count() + 1
    return f"{prefix}{count:05d}"


def dashboard_stats():
    return {
        "patients_total": Patient.query.count(),
        "appointments_today": Appointment.query.filter_by(appt_date=date.today()).count(),
        "lab_pending": LabOrder.query.filter(LabOrder.status != "Completed").count(),
        "invoices_unpaid": Invoice.query.filter(Invoice.status != "Paid").count(),
    }


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@main_bp.route("/")
def index():
    return redirect(url_for("main.dashboard") if current_user.is_authenticated else url_for("main.login"))


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        staff = Staff.query.filter_by(username=username).first()
        if staff and staff.check_password(password):
            login_user(staff)
            return redirect(url_for("main.dashboard"))
        flash("Incorrect username or password.", "error")
    return render_template("login.html")


@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@main_bp.route("/dashboard")
@login_required
def dashboard():
    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()
    today_appts = Appointment.query.filter_by(appt_date=date.today()).order_by(Appointment.appt_time).all()
    pending_orders = LabOrder.query.filter(LabOrder.status != "Completed").order_by(LabOrder.created_at.desc()).limit(5).all()
    return render_template(
        "dashboard.html",
        stats=dashboard_stats(),
        recent_patients=recent_patients,
        today_appts=today_appts,
        pending_orders=pending_orders,
    )


# ---------------------------------------------------------------------------
# Patients (Registration)
# ---------------------------------------------------------------------------

@main_bp.route("/patients")
@login_required
def patients_list():
    q = request.args.get("q", "").strip()
    query = Patient.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Patient.full_name.ilike(like), Patient.mrn.ilike(like), Patient.phone.ilike(like)))
    patients = query.order_by(Patient.created_at.desc()).all()
    return render_template("patients/list.html", patients=patients, q=q)


@main_bp.route("/patients/new", methods=["GET", "POST"])
@login_required
def patient_new():
    if request.method == "POST":
        p = Patient(
            mrn=next_code("MRN", Patient, "mrn"),
            full_name=request.form["full_name"].strip(),
            dob=datetime.strptime(request.form["dob"], "%Y-%m-%d").date(),
            gender=request.form["gender"],
            phone=request.form["phone"].strip(),
            email=request.form.get("email", "").strip(),
            address=request.form.get("address", "").strip(),
            blood_group=request.form.get("blood_group", ""),
        )
        db.session.add(p)
        db.session.commit()
        flash(f"Patient {p.full_name} registered with MRN {p.mrn}.", "success")
        return redirect(url_for("main.patient_view", patient_id=p.id))
    return render_template("patients/form.html", patient=None)


@main_bp.route("/patients/<int:patient_id>")
@login_required
def patient_view(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template("patients/view.html", patient=patient)


@main_bp.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"])
@login_required
def patient_edit(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if request.method == "POST":
        patient.full_name = request.form["full_name"].strip()
        patient.dob = datetime.strptime(request.form["dob"], "%Y-%m-%d").date()
        patient.gender = request.form["gender"]
        patient.phone = request.form["phone"].strip()
        patient.email = request.form.get("email", "").strip()
        patient.address = request.form.get("address", "").strip()
        patient.blood_group = request.form.get("blood_group", "")
        db.session.commit()
        flash("Patient details updated.", "success")
        return redirect(url_for("main.patient_view", patient_id=patient.id))
    return render_template("patients/form.html", patient=patient)


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------

@main_bp.route("/appointments")
@login_required
def appointments_list():
    filter_date = request.args.get("date", date.today().isoformat())
    appts = Appointment.query.filter_by(appt_date=datetime.strptime(filter_date, "%Y-%m-%d").date()).order_by(Appointment.appt_time).all()
    return render_template("appointments/list.html", appointments=appts, filter_date=filter_date)


@main_bp.route("/appointments/new", methods=["GET", "POST"])
@login_required
def appointment_new():
    patients = Patient.query.order_by(Patient.full_name).all()
    if request.method == "POST":
        a = Appointment(
            patient_id=int(request.form["patient_id"]),
            department=request.form["department"],
            doctor=request.form["doctor"].strip(),
            appt_date=datetime.strptime(request.form["appt_date"], "%Y-%m-%d").date(),
            appt_time=request.form["appt_time"],
            notes=request.form.get("notes", "").strip(),
        )
        db.session.add(a)
        db.session.commit()
        flash("Appointment scheduled.", "success")
        return redirect(url_for("main.appointments_list", date=a.appt_date.isoformat()))
    preselect = request.args.get("patient_id", type=int)
    return render_template("appointments/form.html", patients=patients, preselect=preselect)


@main_bp.route("/appointments/<int:appt_id>/status", methods=["POST"])
@login_required
def appointment_status(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = request.form["status"]
    db.session.commit()
    return jsonify({"ok": True, "status": appt.status})


# ---------------------------------------------------------------------------
# Lab
# ---------------------------------------------------------------------------

@main_bp.route("/lab/orders")
@login_required
def lab_orders_list():
    status = request.args.get("status", "")
    query = LabOrder.query
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(LabOrder.created_at.desc()).all()
    return render_template("lab/orders.html", orders=orders, status=status)


@main_bp.route("/lab/orders/new", methods=["GET", "POST"])
@login_required
def lab_order_new():
    patients = Patient.query.order_by(Patient.full_name).all()
    tests = LabTestCatalog.query.order_by(LabTestCatalog.category, LabTestCatalog.name).all()
    if request.method == "POST":
        test_ids = request.form.getlist("test_ids")
        if not test_ids:
            flash("Select at least one test.", "error")
            return render_template("lab/order_form.html", patients=patients, tests=tests, preselect=request.form.get("patient_id", type=int))
        order = LabOrder(
            order_no=next_code("LAB", LabOrder, "order_no"),
            patient_id=int(request.form["patient_id"]),
            ordered_by=request.form["ordered_by"].strip(),
            priority=request.form.get("priority", "Routine"),
        )
        db.session.add(order)
        db.session.flush()
        for tid in test_ids:
            db.session.add(LabOrderItem(order_id=order.id, test_id=int(tid)))
        db.session.commit()
        flash(f"Lab order {order.order_no} created.", "success")
        return redirect(url_for("main.lab_order_view", order_id=order.id))
    preselect = request.args.get("patient_id", type=int)
    return render_template("lab/order_form.html", patients=patients, tests=tests, preselect=preselect)


@main_bp.route("/lab/orders/<int:order_id>")
@login_required
def lab_order_view(order_id):
    order = LabOrder.query.get_or_404(order_id)
    return render_template("lab/report.html", order=order)


@main_bp.route("/lab/orders/<int:order_id>/item/<int:item_id>", methods=["POST"])
@login_required
def lab_item_update(order_id, item_id):
    item = LabOrderItem.query.get_or_404(item_id)
    action = request.form["action"]
    if action == "collect":
        item.status = "Collected"
    elif action == "result":
        item.result_value = request.form.get("result_value", "").strip()
        item.result_flag = request.form.get("result_flag", "Normal")
        item.result_notes = request.form.get("result_notes", "").strip()
        item.status = "Resulted"
        item.resulted_at = datetime.utcnow()
    db.session.commit()

    order = item.order
    if order.items and all(i.status == "Resulted" for i in order.items):
        order.status = "Completed"
    elif any(i.status in ("Collected", "Resulted") for i in order.items):
        order.status = "In Progress"
    db.session.commit()
    flash("Lab item updated.", "success")
    return redirect(url_for("main.lab_order_view", order_id=order_id))


# ---------------------------------------------------------------------------
# Billing
# ---------------------------------------------------------------------------

@main_bp.route("/billing/invoices")
@login_required
def invoices_list():
    status = request.args.get("status", "")
    query = Invoice.query
    if status:
        query = query.filter_by(status=status)
    invoices = query.order_by(Invoice.created_at.desc()).all()
    return render_template("billing/invoices.html", invoices=invoices, status=status)


@main_bp.route("/billing/invoices/new", methods=["GET", "POST"])
@login_required
def invoice_new():
    patients = Patient.query.order_by(Patient.full_name).all()
    if request.method == "POST":
        descriptions = request.form.getlist("description")
        qtys = request.form.getlist("qty")
        prices = request.form.getlist("unit_price")
        invoice = Invoice(
            invoice_no=next_code("INV", Invoice, "invoice_no"),
            patient_id=int(request.form["patient_id"]),
        )
        db.session.add(invoice)
        db.session.flush()
        for desc, qty, price in zip(descriptions, qtys, prices):
            if not desc.strip():
                continue
            db.session.add(InvoiceItem(
                invoice_id=invoice.id,
                description=desc.strip(),
                qty=int(qty or 1),
                unit_price=float(price or 0),
            ))
        db.session.commit()
        flash(f"Invoice {invoice.invoice_no} created.", "success")
        return redirect(url_for("main.invoice_view", invoice_id=invoice.id))
    preselect = request.args.get("patient_id", type=int)
    return render_template("billing/invoice_form.html", patients=patients, preselect=preselect)


@main_bp.route("/billing/invoices/<int:invoice_id>")
@login_required
def invoice_view(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template("billing/invoice_view.html", invoice=invoice)


@main_bp.route("/billing/invoices/<int:invoice_id>/payment", methods=["POST"])
@login_required
def invoice_payment(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    amount = float(request.form["amount"])
    method = request.form.get("method", "Cash")
    db.session.add(Payment(invoice_id=invoice.id, amount=amount, method=method))
    db.session.flush()
    if invoice.balance() - amount <= 0.001:
        invoice.status = "Paid"
    else:
        invoice.status = "Partially Paid"
    db.session.commit()
    flash("Payment recorded.", "success")
    return redirect(url_for("main.invoice_view", invoice_id=invoice.id))


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

def seed_if_empty():
    db.create_all()
    if Staff.query.count() == 0:
        admin = Staff(name="Ultra Demo", username="ultrademo", role="Administrator")
        admin.set_password("Demo@2026")
        db.session.add(admin)

    if LabTestCatalog.query.count() == 0:
        catalog = [
            ("CBC001", "Complete Blood Count", "Hematology", "Whole Blood (EDTA)", 6, 350),
            ("LFT001", "Liver Function Test", "Biochemistry", "Serum", 12, 650),
            ("KFT001", "Kidney Function Test", "Biochemistry", "Serum", 12, 600),
            ("TSH001", "Thyroid Stimulating Hormone", "Endocrinology", "Serum", 24, 450),
            ("GLU001", "Fasting Blood Glucose", "Biochemistry", "Plasma", 4, 150),
            ("LIPID1", "Lipid Profile", "Biochemistry", "Serum", 12, 700),
            ("URN001", "Urine Routine & Microscopy", "Pathology", "Urine", 6, 200),
            ("COVID1", "COVID-19 RT-PCR", "Microbiology", "Nasopharyngeal Swab", 24, 1200),
        ]
        for code, name, cat, sample, tat, price in catalog:
            db.session.add(LabTestCatalog(code=code, name=name, category=cat, sample_type=sample, turnaround_hours=tat, price=price))

    if Patient.query.count() == 0:
        sample_patients = [
            ("Ananya Sharma", date(1994, 3, 12), "Female", "9876500001", "ananya.sharma@example.com", "Indiranagar, Bengaluru", "O+"),
            ("Rohit Verma", date(1988, 7, 25), "Male", "9876500002", "rohit.verma@example.com", "Koramangala, Bengaluru", "B+"),
            ("Fatima Khan", date(2001, 11, 2), "Female", "9876500003", "fatima.khan@example.com", "Whitefield, Bengaluru", "A-"),
        ]
        for name, dob, gender, phone, email, address, bg in sample_patients:
            db.session.add(Patient(
                mrn=next_code("MRN", Patient, "mrn"),
                full_name=name, dob=dob, gender=gender, phone=phone,
                email=email, address=address, blood_group=bg,
            ))

    db.session.commit()


