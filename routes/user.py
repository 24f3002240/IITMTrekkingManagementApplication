from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Trek, Booking
from utils.decorators import role_required

user_bp = Blueprint('user', __name__, url_prefix='/user')


@user_bp.route('/dashboard')
@login_required
@role_required('user')
def dashboard():
    my_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    preview_treks = Trek.query.filter_by(status='Open').limit(3).all()
    return render_template('user/dashboard.html', my_bookings=my_bookings, preview_treks=preview_treks)


@user_bp.route('/treks')
@login_required
@role_required('user')
def available_treks():
    query = Trek.query.filter_by(status='Open')

    difficulty = request.args.get('difficulty')
    location = request.args.get('location')

    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f'%{location}%'))

    treks = query.all()

    my_booked_trek_ids = {
        b.trek_id for b in Booking.query.filter_by(user_id=current_user.id, status='Booked').all()
    }

    return render_template('user/available_treks.html', treks=treks,
                            selected_difficulty=difficulty, selected_location=location or '',
                            my_booked_trek_ids=my_booked_trek_ids)

@user_bp.route('/trek/<int:trek_id>/book', methods=['POST'])
@login_required
@role_required('user')
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if trek.status != 'Open':
        flash('This trek is not currently open for booking.', 'danger')
        return redirect(url_for('user.available_treks'))

    if trek.available_slots <= 0:
        flash('This trek is fully booked.', 'danger')
        return redirect(url_for('user.available_treks'))

    existing = Booking.query.filter_by(user_id=current_user.id, trek_id=trek.id, status='Booked').first()
    if existing:
        flash('You already have an active booking for this trek.', 'warning')
        return redirect(url_for('user.available_treks'))

    if trek.start_date and trek.end_date:
        overlapping = Booking.query.join(Trek).filter(
            Booking.user_id == current_user.id,
            Booking.status == 'Booked',
            Trek.start_date <= trek.end_date,
            Trek.end_date >= trek.start_date,
            Trek.id != trek.id
        ).first()

        if overlapping:
            flash(f'You already have a trek booked during these dates.', 'danger')
            return redirect(url_for('user.available_treks'))

    new_booking = Booking(user_id=current_user.id, trek_id=trek.id, status='Booked')
    trek.available_slots -= 1

    db.session.add(new_booking)
    db.session.commit()

    flash(f'Successfully booked "{trek.name}"!', 'success')
    return redirect(url_for('user.dashboard'))


@user_bp.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
@role_required('user')
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        abort(403)

    if booking.status != 'Booked':
        flash('This booking cannot be cancelled.', 'danger')
        return redirect(url_for('user.dashboard'))

    booking.status = 'Cancelled'
    booking.trek.available_slots += 1

    db.session.commit()
    flash('Booking cancelled.', 'info')
    return redirect(url_for('user.dashboard'))


@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('user')
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/profile.html')


