from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import NotificationLink, DegreeType, Degree, PARegistrationMst, db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

online_admission_bp = Blueprint('online_admission', __name__, url_prefix='/online')

@online_admission_bp.route('/')
def landing():
    # Fetch active notifications
    notifications = NotificationLink.query.filter_by(active=True).order_by(NotificationLink.order).all()
    # Fetch degree types
    degree_types = DegreeType.query.filter_by(is_active=True).all()
    
    return render_template('online_admission/landing.html', notifications=notifications, degree_types=degree_types)

@online_admission_bp.route('/get_degrees/<int:dtype_id>')
def get_degrees(dtype_id):
    degrees = Degree.query.filter_by(fk_dtypeid=dtype_id, active=True).all()
    return jsonify([{'id': d.id, 'name': d.name} for d in degrees])

@online_admission_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Registration logic will go here
    dtype_id = request.args.get('dtype')
    degree_id = request.args.get('degree')
    
    if request.method == 'POST':
        # Simple test registration logic
        name = request.form.get('name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        dtype_id = request.form.get('dtype_id')
        degree_id = request.form.get('degree_id')
        
        # Check if user already exists
        existing_user = PARegistrationMst.query.filter((PARegistrationMst.email == email) | (PARegistrationMst.mobileno == mobile)).first()
        if existing_user:
            flash('Email or Mobile already registered.', 'danger')
            return redirect(url_for('online_admission.register', dtype=dtype_id, degree=degree_id))
            
        new_user = PARegistrationMst(
            s_name=name,
            email=email,
            mobileno=mobile,
            pwd=generate_password_hash(password),
            fk_dtypeid=dtype_id,
            fk_degreeid=degree_id
        )
        db.session.add(new_user)
        try:
            db.session.commit()
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('online_admission.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error during registration: ' + str(e), 'danger')
            
    
    # Get selected degree type and degree details if passed via query params
    selected_dtype = DegreeType.query.get(dtype_id) if dtype_id else None
    selected_degree = Degree.query.get(degree_id) if degree_id else None
    
    return render_template('online_admission/register.html', 
                           dtype=selected_dtype, 
                           degree=selected_degree)

@online_admission_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form.get('login_id') # email or mobile
        password = request.form.get('password')
        
        user = PARegistrationMst.query.filter((PARegistrationMst.email == login_id) | (PARegistrationMst.mobileno == login_id)).first()
        
        # Depending on how the previous system stored passwords, we check hash.
        # If it was plain text, we might need a fallback.
        if user and check_password_hash(user.pwd, password):
            # login success
            flash('Logged in successfully', 'success')
            return redirect(url_for('online_admission.dashboard'))
        elif user and user.pwd == password:
            # Fallback for plain text passwords in legacy db
            flash('Logged in successfully', 'success')
            return redirect(url_for('online_admission.dashboard'))
        else:
            flash('Invalid credentials', 'danger')
            
    return render_template('online_admission/login.html')

@online_admission_bp.route('/dashboard')
def dashboard():
    return render_template('online_admission/dashboard.html')
