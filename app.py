from flask import Flask
from config import Config
from models import db,User
from database import init_db
from flask_login import LoginManager

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    init_db(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    from routes.user import user_bp
    app.register_blueprint(user_bp)
    from routes.admin import admin_bp
    app.register_blueprint(admin_bp)
    return app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)


