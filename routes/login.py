from flask import Blueprint, request, jsonify, session, url_for
from werkzeug.security import check_password_hash
from models.models import Users, db

login_bp = Blueprint('login_bp', __name__)

@login_bp.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and Password are required!'}), 400

    user = Users.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, password):
        # Redirect based on role
        if user.role == 'ADMIN':
            return jsonify({'redirect': url_for('admin_dashboard')}), 200
        elif user.role == 'USER':
            return jsonify({'redirect': url_for('user_dashboard', role=user.role, username=user.username)}), 200
    else:
        return jsonify({'message': 'Invalid credentials!'}), 401
