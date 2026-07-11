from datetime import date
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from models import db, Trek, Booking, User
from utils.decorators import role_required

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')


@staff_bp.route('/dashboard')
@login_required
@role_required('staff')
def dashboard():
    my_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).all()
    return render_template('staff/dashboard.html', my_treks=my_treks)


@staff_bp.route('/trek/<int:trek_id>/update', methods=['POST'])
@login_required
@role_required('staff')
def update_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != current_user.id:
        abort(403)

    new_status = request.form.get('status')
    new_slots = request.form.get('available_slots')

    valid_staff_transitions = {
        'Approved': ['Open'],
        'Open': ['Closed', 'Completed'],
        'Closed': ['Open'],
    }

    if new_status and new_status in valid_staff_transitions.get(trek.status, []):
        if new_status == 'Open' and trek.end_date and date.today() > trek.end_date:
            flash('Cannot open a trek whose end date has already passed.', 'danger')
            return redirect(url_for('staff.dashboard'))
        trek.status = new_status
    elif new_status:
        flash(f'Cannot change trek from {trek.status} to {new_status}.', 'danger')
        return redirect(url_for('staff.dashboard'))

    if new_slots:
        try:
            new_slots = int(new_slots)
            if new_slots < 0:
                flash('Slots cannot be negative.', 'danger')
                return redirect(url_for('staff.dashboard'))
            trek.available_slots = new_slots
        except ValueError:
            flash('Invalid slot number.', 'danger')
            return redirect(url_for('staff.dashboard'))

    db.session.commit()
    flash('Trek updated successfully.', 'success')
    return redirect(url_for('staff.dashboard'))


@staff_bp.route('/trek/<int:trek_id>/participants')
@login_required
@role_required('staff')
def view_participants(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != current_user.id:
        abort(403)

    bookings = Booking.query.filter_by(trek_id=trek.id, status='Booked').all()

    return render_template('staff/participants.html', trek=trek, bookings=bookings)