from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from models import db, User, Trek, Booking
from utils.decorators import role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()
    pending_staff = User.query.filter_by(role='staff', approval_status='pending').all()

    return render_template(
        'admin/dashboard.html',
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
        pending_staff=pending_staff,
    )


@admin_bp.route('/staff/approve/<int:staff_id>', methods=['POST'])
@login_required
@role_required('admin')
def approve_staff(staff_id):
    staff = User.query.get_or_404(staff_id)

    if staff.role != 'staff':
        flash('Invalid operation.', 'danger')
        return redirect(url_for('admin.dashboard'))

    staff.approval_status = 'approved'
    db.session.commit()
    flash(f'{staff.name} has been approved.', 'success')
    return redirect(url_for('admin.dashboard'))