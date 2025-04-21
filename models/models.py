import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, DateTime, Integer, String, Date, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship, backref

db = SQLAlchemy()
    
class Users(db.Model):
    __tablename__ = 'users'  # ✅ Make table names lowercase for consistency
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # ✅ Increase length for hashed passwords
    dob = db.Column(Date, nullable=False)
    role = db.Column(db.String(50), nullable=False)  # Define max length properly
    email = db.Column(db.String(100), unique=True, nullable=False)  # ✅ Increased length for better storage
    qualification = Column(db.Enum('High School', 'Undergraduate', 'Postgraduate', 'PhD'), nullable=False)


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    chapters = relationship('Chapter', backref='subject', lazy=True, cascade="all, delete-orphan")
    creator = relationship('Users', backref='created_subjects')

class Chapter(db.Model):
    __tablename__ = 'chapters'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    quizzes = relationship('Quiz', backref='chapter', lazy=True, cascade="all, delete-orphan")
    creator = relationship('Users', backref='created_chapters')

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    time_limit = Column(Integer, default=600)  # Time limit in seconds
    created_by = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_published = Column(Boolean, default=False)
    chapter_id = Column(Integer, ForeignKey('chapters.id'), nullable=True)

    # Relationships
    questions = relationship('Question', backref='quiz', lazy=True, cascade="all, delete-orphan")

class Question(db.Model):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), nullable=False)

    # Relationships
    options = relationship('Option', backref='question', lazy=True, cascade="all, delete-orphan")

class Option(db.Model):
    __tablename__ = 'options'
    id = Column(Integer, primary_key=True)
    text = Column(String(255), nullable=False)
    is_correct = Column(Boolean, default=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)

class UserAnswer(db.Model):
    __tablename__ = 'user_answers'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    selected_option_id = Column(Integer, ForeignKey('options.id'), nullable=True)  # Null if not answered
    is_correct = Column(Boolean, nullable=False, default=False)
    answered_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship('Users', backref='answers')
    question = relationship('Question', backref='user_answers')
    selected_option = relationship('Option', backref='user_answers')

class UserScore(db.Model):
    __tablename__ = 'user_scores'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    quiz_id = db.Column(db.Integer, ForeignKey('quizzes.id'), nullable=False)
    chapter_id = db.Column(db.Integer, ForeignKey('chapters.id'), nullable=False)
    subject_id = db.Column(db.Integer, ForeignKey('subjects.id'), nullable=False)
    score_percentage = db.Column(db.Float, nullable=False)  # Stores score as percentage
    attempted_at = db.Column(DateTime, default=datetime.datetime.utcnow)  # Timestamp of attempt

    # Relationships
    user = relationship('Users', backref='scores')
    quiz = relationship('Quiz', backref='scores')
    chapter = relationship('Chapter', backref='scores')
    subject = relationship('Subject', backref='scores')