from flask import Blueprint, request, jsonify, url_for
from models.models import Users, db
from werkzeug.security import generate_password_hash
from datetime import datetime

register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()  # Accept JSON input

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    dob_str = data.get('dob')
    qualification = data.get('qualification')

    if not all([username, email, password, dob_str, qualification]):
        return jsonify({'error': 'All fields are required!'}), 400

    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Check if email already exists
    if Users.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered!'}), 400

    hashed_password = generate_password_hash(password)

    new_user = Users(
    username=username,
    email=email,
    password_hash=hashed_password,
    dob=dob,
    qualification=qualification,
    role='USER'
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'redirect': url_for('main', _external=True)}), 200  # Redirect to login page
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
