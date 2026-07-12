from flask import Blueprint, render_template, redirect, url_for, flash,request
from flask_login import login_required
from models import db, User, Trek, Booking
from utils.decorators import role_required
from datetime import datetime,date

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


@admin_bp.route('/treks/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_trek():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        difficulty = request.form.get('difficulty')
        duration_days = request.form.get('duration_days')
        available_slots = request.form.get('available_slots')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        if not name or not location:
            flash('Name and location cannot be empty.', 'danger')
            return redirect(url_for('admin.create_trek'))

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

        if start_date and end_date:
            actual_days = (end_date - start_date).days + 1
            if actual_days != duration_days:
                flash(f'Duration ({duration_days} days) does not match the date range ({actual_days} days).', 'danger')
                return redirect(url_for('admin.create_trek'))

        # --- Duplicate check: same name + location (case/whitespace-insensitive), overlapping dates ---
        same_name_location_treks = Trek.query.filter(
            db.func.lower(db.func.trim(Trek.name)) == name.lower(),
            db.func.lower(db.func.trim(Trek.location)) == location.lower(),
        ).all()

        for existing in same_name_location_treks:
            if start_date and end_date and existing.start_date and existing.end_date:
                if existing.start_date <= end_date and existing.end_date >= start_date:
                    flash(f'A trek named "{name}" in {location} already exists with overlapping dates '
                          f'({existing.start_date} to {existing.end_date}).', 'danger')
                    return redirect(url_for('admin.create_trek'))
            elif not start_date or not end_date or not existing.start_date or not existing.end_date:
                # If either trek lacks dates, fall back to exact name+location match as duplicate
                flash(f'A trek named "{name}" in {location} already exists.', 'danger')
                return redirect(url_for('admin.create_trek'))

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

    if trek.assigned_staff_id is None:
        flash('Assign a staff member before approving this trek.', 'danger')
        return redirect(url_for('admin.list_treks'))

    if trek.end_date and date.today() > trek.end_date:
        flash('Cannot approve a trek whose end date has already passed.', 'danger')
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

        if trek.start_date and trek.end_date:
            overlapping = Trek.query.filter(
                Trek.assigned_staff_id == staff.id,
                Trek.start_date <= trek.end_date,
                Trek.end_date >= trek.start_date,
                Trek.id != trek.id
            ).first()

            if overlapping:
                flash(f'{staff.name} is already assigned to "{overlapping.name}" during overlapping dates.', 'danger')
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

@admin_bp.route('/users')
@login_required
@role_required('admin')
def list_users():
    search = request.args.get('search', '').strip()

    query = User.query.filter(User.role.in_(['user', 'staff']))

    if search:
        if search.isdigit():
            query = query.filter(User.id == int(search))
        else:
            query = query.filter(User.name.ilike(f'%{search}%'))

    users = query.all()
    return render_template('admin/users.html', users=users, search=search)


@admin_bp.route('/user/<int:user_id>/toggle-blacklist', methods=['POST'])
@login_required
@role_required('admin')
def toggle_blacklist(user_id):
    user = User.query.get_or_404(user_id)

    if user.role == 'admin':
        flash('Cannot blacklist an admin account.', 'danger')
        return redirect(url_for('admin.list_users'))

    user.is_blacklisted = not user.is_blacklisted
    db.session.commit()

    action = 'blacklisted' if user.is_blacklisted else 'unblacklisted'
    flash(f'{user.name} has been {action}.', 'success')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/treks')
@login_required
@role_required('admin')
def list_treks():
    search = request.args.get('search', '').strip()

    query = Trek.query

    if search:
        if search.isdigit():
            query = query.filter(Trek.id == int(search))
        else:
            query = query.filter(Trek.name.ilike(f'%{search}%'))

    treks = query.all()
    return render_template('admin/treks.html', treks=treks, search=search)

@admin_bp.route('/bookings')
@login_required
@role_required('admin')
def list_bookings():
    bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings)


@admin_bp.route('/trek/<int:trek_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        difficulty = request.form.get('difficulty')
        duration_days = request.form.get('duration_days')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        if not name or not location:
            flash('Name and location cannot be empty.', 'danger')
            return redirect(url_for('admin.edit_trek', trek_id=trek.id))

        if difficulty not in ('Easy', 'Moderate', 'Hard'):
            flash('Invalid difficulty selected.', 'danger')
            return redirect(url_for('admin.edit_trek', trek_id=trek.id))

        try:
            duration_days = int(duration_days)
            if duration_days <= 0:
                raise ValueError
        except (ValueError, TypeError):
            flash('Duration must be a valid positive number.', 'danger')
            return redirect(url_for('admin.edit_trek', trek_id=trek.id))

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None

        if start_date and end_date:
            actual_days = (end_date - start_date).days + 1
            if actual_days != duration_days:
                flash(f'Duration ({duration_days} days) does not match the date range ({actual_days} days).', 'danger')
                return redirect(url_for('admin.edit_trek', trek_id=trek.id))

        trek.name = name
        trek.location = location
        trek.difficulty = difficulty
        trek.duration_days = duration_days
        trek.start_date = start_date
        trek.end_date = end_date

        db.session.commit()
        flash(f'Trek "{trek.name}" updated.', 'success')
        return redirect(url_for('admin.list_treks'))

    return render_template('admin/edit_trek.html', trek=trek)