from flask import Blueprint, render_template, redirect, url_for, flash,request
from flask_login import login_required
from models import db, User, Trek, Booking
from utils.decorators import role_required
from datetime import datetime
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




@admin_bp.route('/treks')
@login_required
@role_required('admin')
def list_treks():
    treks = Trek.query.all()
    return render_template('admin/treks.html', treks=treks)


@admin_bp.route('/treks/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_trek():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        difficulty = request.form.get('difficulty')
        duration_days = request.form.get('duration_days')
        available_slots = request.form.get('available_slots')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        if difficulty not in ('Easy', 'Moderate', 'Hard'):
            flash('Invalid difficulty selected.', 'danger')
            return redirect(url_for('admin.create_trek'))

        try:
            duration_days = int(duration_days)
            available_slots = int(available_slots)
            if duration_days <= 0 or available_slots < 0:
                raise ValueError
        except (ValueError, TypeError):
            flash('Duration and slots must be valid positive numbers.', 'danger')
            return redirect(url_for('admin.create_trek'))

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None

        new_trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration_days=duration_days,
            available_slots=available_slots,
            start_date=start_date,
            end_date=end_date,
        )
        db.session.add(new_trek)
        db.session.commit()

        flash(f'Trek "{name}" created with status Pending.', 'success')
        return redirect(url_for('admin.list_treks'))

    return render_template('admin/create_trek.html')


@admin_bp.route('/trek/<int:trek_id>/approve', methods=['POST'])
@login_required
@role_required('admin')
def approve_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.status != 'Pending':
        flash('Only pending treks can be approved.', 'danger')
        return redirect(url_for('admin.list_treks'))

    trek.status = 'Approved'
    db.session.commit()
    flash(f'Trek "{trek.name}" approved.', 'success')
    return redirect(url_for('admin.list_treks'))

@admin_bp.route('/trek/<int:trek_id>/assign-staff', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def assign_staff(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if request.method == 'POST':
        staff_id = request.form.get('staff_id')
        staff = User.query.filter_by(id=staff_id, role='staff', approval_status='approved').first()

        if staff is None:
            flash('Invalid staff selection.', 'danger')
            return redirect(url_for('admin.assign_staff', trek_id=trek.id))

        trek.assigned_staff_id = staff.id
        db.session.commit()
        flash(f'{staff.name} assigned to "{trek.name}".', 'success')
        return redirect(url_for('admin.list_treks'))

    available_staff = User.query.filter_by(role='staff', approval_status='approved').all()
    return render_template('admin/assign_staff.html', trek=trek, available_staff=available_staff)


@admin_bp.route('/trek/<int:trek_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    active_bookings = Booking.query.filter_by(trek_id=trek.id, status='Booked').count()
    if active_bookings > 0:
        flash(f'Cannot delete "{trek.name}" — it has {active_bookings} active booking(s).', 'danger')
        return redirect(url_for('admin.list_treks'))

    db.session.delete(trek)
    db.session.commit()
    flash(f'Trek "{trek.name}" deleted.', 'success')
    return redirect(url_for('admin.list_treks'))