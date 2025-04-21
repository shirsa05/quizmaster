import datetime
from flask import Blueprint, request, redirect, url_for, flash, render_template
from psutil import users
from models.models import Subject, UserScore, Users, db, Quiz, Question, Option, UserAnswer

user_bp = Blueprint('user', __name__)

@user_bp.route('/attempt_quiz/<int:quiz_id>/<int:user_id>')
def attempt_quiz(quiz_id, user_id):
    """Display the quiz questions to the user."""
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions
    return render_template('attempt_quiz.html', quiz=quiz, questions=questions, user_id=user_id, time_limit=quiz.time_limit)


@user_bp.route('/submit_quiz/<int:quiz_id>/<int:user_id>', methods=['POST'])
def submit_quiz(quiz_id, user_id):
    """Handles quiz submission and stores user answers."""
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = quiz.questions
    chapter = quiz.chapter
    subject = chapter.subject
    
    correct_answers = 0
    total_questions = len(questions)

    for question in questions:
        selected_option_id = request.form.get(f'question_{question.id}')
        
        if selected_option_id:
            selected_option = Option.query.get(int(selected_option_id))
            is_correct = selected_option.is_correct if selected_option else False

            # Save the user's answer with the correct user_id
            user_answer = UserAnswer(
                user_id=user_id,
                question_id=question.id,
                selected_option_id=selected_option.id if selected_option else None,
                is_correct=is_correct
            )
            db.session.add(user_answer)

            # Count correct answers
            if is_correct:
                correct_answers += 1

    db.session.commit()

    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # Check if the user already has an attempt record for this quiz
    existing_score = UserScore.query.filter_by(user_id=user_id, quiz_id=quiz.id).first()

    if existing_score:
        # Update the existing record
        existing_score.score_percentage = score
        existing_score.attempted_at = datetime.datetime.utcnow()
        flash("Your quiz attempt has been updated!", "success")
    else:
        # Insert a new record
        new_score = UserScore(
            user_id=user_id,
            quiz_id=quiz.id,
            chapter_id=chapter.id,
            subject_id=subject.id,
            score_percentage=score,
            attempted_at=datetime.datetime.utcnow()
        )
        db.session.add(new_score)
        flash("Your quiz has been submitted!", "success")
        
    db.session.commit()
    
    flash(f'You scored {score:.2f}%', 'success')

    return render_template('attempt_quiz.html', quiz=quiz, questions=questions, user_id=user_id, score=score)

@user_bp.route('/search_user/<int:user_id>')
def search_user(user_id):
    query = request.args.get('q', '').lower()

    user_id = Users.query.get(user_id)  # ✅ Fetch user
    matched_subjects = Subject.query.filter(Subject.name.ilike(f'%{query}%')).all()
    matched_quizzes = Quiz.query.filter(Quiz.title.ilike(f'%{query}%')).all()

    return render_template('search_user.html', 
                           user_id=user_id,
                           subjects=matched_subjects, 
                           quizzes=matched_quizzes, 
                           search_query=query)