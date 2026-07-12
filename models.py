from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    approval_status = db.Column(db.String(20), nullable=False, default='approved')
    is_blacklisted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint("role IN ('admin', 'staff', 'user')", name='check_valid_role'),
        db.CheckConstraint("approval_status IN ('pending', 'approved')", name='check_valid_approval_status'),
    )

    def is_active(self):
        return not self.is_blacklisted

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'

class Trek(db.Model):
    __tablename__ = 'treks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    difficulty = db.Column(db.String(255), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    available_slots= db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(60), nullable=False,default='Pending')
    start_date=db.Column(db.Date)
    end_date=db.Column(db.Date)
    assigned_staff_id=db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_staff = db.relationship('User', backref='assigned_treks', foreign_keys=[assigned_staff_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint("difficulty IN ('Easy', 'Moderate', 'Hard')", name='check_valid_difficulty'),
        db.CheckConstraint("status IN ('Pending', 'Approved', 'Open', 'Closed', 'Completed')", name='check_valid_status'),
        db.CheckConstraint("available_slots >= 0", name='check_slots_non_negative')
    )
    def __repr__(self):
        return f'<Trek {self.name} ({self.status})>'

    

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(60), nullable=False, default='Booked')

    user = db.relationship('User', backref='bookings')
    trek = db.relationship('Trek', backref='bookings')

    __table_args__ = (
        db.CheckConstraint("status IN ('Booked', 'Cancelled', 'Completed')", name='check_valid_status'),
    )

    def __repr__(self):
        return f'<Booking {self.id} ({self.status})>'