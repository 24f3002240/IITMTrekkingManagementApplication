from werkzeug.security import generate_password_hash
from models import db, User


def init_db(app):
    """
    Initialize the database: create all tables from the models,
    and seed the pre-existing Admin account if it doesn't already exist.
    Must be called once, inside the Flask app context.
    """
    with app.app_context():
        db.create_all()
        _seed_admin(app)


def _seed_admin(app):
    """
    Ensure exactly one Admin account exists.
    Runs on every app startup, but only inserts if no admin is found —
    this prevents a duplicate-email IntegrityError on repeated restarts.
    """
    existing_admin = User.query.filter_by(role='admin').first()

    if existing_admin is None:
        admin = User(
            name=app.config['ADMIN_NAME'],
            email=app.config['ADMIN_EMAIL'],
            password_hash=generate_password_hash(app.config['ADMIN_PASSWORD']),
            role='admin',
            approval_status='approved',
            is_blacklisted=False,
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin account created: avinash732004kumar@gmail.com')
    else:
        print('Admin account already exists — skipping seed.')



