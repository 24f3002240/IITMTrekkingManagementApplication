from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if role not in ('user', 'staff'):
            flash('Invalid registration type.', 'danger')
            return redirect(url_for('auth.register'))

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        new_account = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            approval_status='pending' if role == 'staff' else 'approved',
        )
        db.session.add(new_account)
        db.session.commit()

        if role == 'staff':
            flash('Registration submitted. Await admin approval before logging in.', 'info')
        else:
            flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user is None or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))

        if user.is_blacklisted:
            flash('This account has been blacklisted.', 'danger')
            return redirect(url_for('auth.login'))

        if user.role == 'staff' and user.approval_status == 'pending':
            flash('Your staff account is awaiting admin approval.', 'warning')
            return redirect(url_for('auth.login'))

        login_user(user)

        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'staff':
            return redirect(url_for('staff.dashboard'))
        else:
            print("i am in user")
            return redirect(url_for('user.dashboard'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))



