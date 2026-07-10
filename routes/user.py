from flask import Blueprint, render_template, redirect, url_for, request, flash

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('user/dashboard.html')
    