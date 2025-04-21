from flask import Flask, flash, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from routes.login import login_user
from routes.register import register_bp  # Import register blueprint
from models.models import Chapter, Question, Quiz, Subject, UserScore, Users, db
from routes.login import login_bp  # ✅ Import login blueprint
from routes.admin import admin_bp  # Import admin blueprint
from routes.user import user_bp
from werkzeug.security import generate_password_hash
from datetime import datetime 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Required for session handling

db.init_app(app)

with app.app_context():
    db.create_all()
    # Check if admin user already exists
    if not Users.query.filter_by(username="admin").first():
        admin_user = Users(
            username="admin",
            password_hash=generate_password_hash("1234"),  # Securely hash the password
            dob=datetime(2004, 2, 5),  # Hardcoded DOB (YYYY, MM, DD)
            role="ADMIN",
            email="shirsamaitra@gmail.com",
            qualification="Undergraduate"  # Hardcoded Qualification
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists.")

# Register Blueprints
app.register_blueprint(register_bp)
app.register_blueprint(login_bp)  # ✅ Register login routes
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)

@app.route('/')
def main():
    return render_template("login.html")

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    total_subjects = Subject.query.count()
    total_chapters = Chapter.query.count()
    total_quizzes = Quiz.query.count()
    total_users = Users.query.count()
   
    # Fetch subjects with their chapters and quizzes
    subjects_with_chapters = Subject.query.options(
        db.joinedload(Subject.chapters).joinedload(Chapter.quizzes)
    ).all()
     
    return render_template('admin_dashboard.html', 
                           total_subjects=total_subjects, 
                           total_chapters=total_chapters, 
                           total_quizzes=total_quizzes,
                           total_users=total_users,
                           subjects_with_chapters=subjects_with_chapters)

@app.route('/user_dashboard')
def user_dashboard():
    role = request.args.get('role')
    username = request.args.get('username')

    if role != 'USER':
        flash('Access denied!', 'danger')
        return redirect(url_for('login'))

    user = Users.query.filter_by(username=username).first()
    subjects = Subject.query.all()  # ✅ Fetch all subjects
    
    # Fetch attempted quizzes for the user
    attempted_quizzes = UserScore.query.filter_by(user_id=user.id).all()

    return render_template('user_dashboard.html', user=user, subjects=subjects, attempted_quizzes=attempted_quizzes)  # ✅ Pass subjects


@app.route('/chapters/<int:subject_id>/<int:user_id>')
def view_chapters(subject_id, user_id):
    subject = Subject.query.get_or_404(subject_id)
    chapters = subject.chapters
    user_id = Users.query.get(user_id)  # ✅ Fetch user
    return render_template('view_chapters.html', subject=subject, chapters=chapters, user_id=user_id)


@app.route('/quizzes/<int:chapter_id>/<int:user_id>')
def view_quizzes(chapter_id, user_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    subject = Subject.query.get_or_404(chapter.subject_id)  # ✅ Fetch subject
    quizzes = chapter.quizzes  # Fetch quizzes related to this chapter
    return render_template('view_quizzes.html', chapter=chapter, quizzes=quizzes, user_id=user_id, subject=subject)


@app.route('/logout')
def logout():
    return redirect(url_for('main'))



if __name__ == '__main__':
    app.run(debug=True)
