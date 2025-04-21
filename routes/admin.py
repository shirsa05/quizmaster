from flask import Blueprint, flash, redirect, render_template, request, jsonify, session, url_for
from models.models import Chapter, Option, Question, Quiz, UserAnswer, UserScore, Users, db, Subject

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/add_subject', methods=['POST'])
def add_subject():
    
    data = request.json
    new_subject = Subject(
        name=data['name'],
        description=data.get('description', ''),
        created_by='ADMIN'
    )
    db.session.add(new_subject)
    db.session.commit()

    return jsonify({'message': 'Subject added successfully!'})

@admin_bp.route('/add_chapter', methods=['POST'])
def add_chapter():
    data = request.json
    
    subject = Subject.query.get(data['subject_id'])
    if not subject:
        return jsonify({'message': 'Subject not found'}), 404

    new_chapter = Chapter(
        name=data['name'],
        description=data.get('description', ''),
        subject_id=subject.id,
        created_by='ADMIN'
        )
    db.session.add(new_chapter)
    db.session.commit()

    return jsonify({'message': 'Chapter added successfully!'})

@admin_bp.route('/get_subjects', methods=['GET'])
def get_subjects():
    subjects = Subject.query.all()
    return jsonify([{'id': subject.id, 'name': subject.name} for subject in subjects])


@admin_bp.route('/get_chapters/<int:subject_id>', methods=['GET'])
def get_chapters(subject_id):
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return jsonify([{'id': chapter.id, 'name': chapter.name} for chapter in chapters])

@admin_bp.route('/get_quizzes/<int:chapter_id>', methods=['GET'])
def get_quizzes(chapter_id):
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return jsonify([{'id': quiz.id, 'title': quiz.title} for quiz in quizzes])


@admin_bp.route('/add_quiz', methods=['POST'])
def add_quiz():
    data = request.json

    chapter = Chapter.query.get(data['chapter_id'])
    if not chapter:
        return jsonify({'message': 'Chapter not found'}), 404

    # Correct way to access 'time_limit' from JSON request
    time_limit = int(data['time_limit']) * 60  # Convert minutes to seconds
        
    new_quiz = Quiz(
        chapter_id=chapter.id,
        title=data['title'],
        description=data['description'],
        created_by='ADMIN', 
        time_limit=time_limit
    )
    db.session.add(new_quiz)
    db.session.commit()

    return jsonify({'message': 'Quiz added successfully!'})

@admin_bp.route('/update/<string:type>/<int:id>', methods=['POST'])
def update_item_name(type, id):
    data = request.get_json()
    new_name = data.get("name", "").strip()
    
    if not new_name:
        return jsonify({'message': 'Name cannot be empty.'}), 400

    model_map = {
        "subject": Subject,
        "chapter": Chapter,
        "quiz": Quiz
    }

    model = model_map.get(type)
    if not model:
        return jsonify({'message': 'Invalid type'}), 400

    item = model.query.get_or_404(id)

    # Set the correct attribute name
    if type == "quiz":
        item.title = new_name
    else:
        item.name = new_name

    db.session.commit()
    return jsonify({'message': f'{type.capitalize()} updated successfully!'})

@admin_bp.route('/add_question', methods=['POST'])
def add_question():
    data = request.json
    if not data or 'quiz_id' not in data:
        return jsonify({'message': 'Missing quiz_id'}), 400

    print("Received Data:", data)  # Debugging log

    quiz = Quiz.query.get(data['quiz_id'])
    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404

    # Check if chapter and subject exist
    chapter = Chapter.query.get(quiz.chapter_id)
    if not chapter:
        return jsonify({'message': 'Chapter not found'}), 404

    subject = Subject.query.get(chapter.subject_id)
    if not subject:
        return jsonify({'message': 'Subject not found'}), 404

    print(f"Adding question to: Quiz: {quiz.title}, Chapter: {chapter.name}, Subject: {subject.name}")

    # Create new question
    new_question = Question(
        quiz_id=quiz.id,
        text=data['question_text'],
    )
    db.session.add(new_question)
    db.session.commit()  # Commit to get question ID

    # Add options
    for index, option_text in enumerate(data['options']):
        new_option = Option(
            question_id=new_question.id,
            text=option_text,
            is_correct=(index == data['correct_index']),
        )
        db.session.add(new_option)

    db.session.commit()

    return jsonify({'message': 'Question added successfully!'})

# Manage Quiz Page
@admin_bp.route('manage_quiz')
def manage_quiz():
    subjects = Subject.query.options(
        db.joinedload(Subject.chapters).joinedload(Chapter.quizzes).joinedload(Quiz.questions)
    ).all()
    return render_template('manage_quiz.html', subjects=subjects)

@admin_bp.route('/delete/<string:type>/<int:id>', methods=['DELETE'])
def delete_item(type, id):
    print(f"Attempting to delete {type} with ID {id}")  # ✅ Debugging print

    model_mapping = {
        'subject': Subject,
        'chapter': Chapter,
        'quiz': Quiz,
        'question': Question,
        'option': Option
    }

    model = model_mapping.get(type)
    if not model:
        return jsonify({'message': 'Invalid item type'}), 400

    item = db.session.get(model, id)
    if not item:
        return jsonify({'message': f'{type.capitalize()} not found'}), 404

    try:
        from models.models import UserAnswer, UserScore  # Import inside function to avoid circular import issues
        
        # **Handle cascading deletions**
        if type == "subject":
            # **Get all chapters belonging to the subject**
            chapters = Chapter.query.filter_by(subject_id=id).all()
            for chapter in chapters:
                delete_item("chapter", chapter.id)  # ✅ Recursive delete for chapters

        elif type == "chapter":
            # **Get all quizzes in the chapter**
            quizzes = Quiz.query.filter_by(chapter_id=id).all()
            for quiz in quizzes:
                delete_item("quiz", quiz.id)  # ✅ Recursive delete for quizzes

        elif type == "quiz":
            # **Delete user scores related to this quiz**
            UserScore.query.filter_by(quiz_id=id).delete()

            # **Get all questions in the quiz**
            questions = Question.query.filter_by(quiz_id=id).all()
            for question in questions:
                delete_item("question", question.id)  # ✅ Recursive delete for questions

        elif type == "question":
            # **Delete user answers related to this question**
            UserAnswer.query.filter_by(question_id=id).delete()
            # **Delete options related to this question**
            Option.query.filter_by(question_id=id).delete()

        # Finally, delete the main item
        db.session.delete(item)
        db.session.commit()

        return jsonify({'message': f'{type.capitalize()} deleted successfully'})

    except Exception as e:
        db.session.rollback()
        print("Error deleting:", str(e))  # ✅ Debugging print
        return jsonify({'message': 'Error deleting item', 'error': str(e)}), 500


@admin_bp.route('/edit/question/<int:id>', methods=['GET', 'POST'])
def edit_question(id):
    question = Question.query.get_or_404(id)
    
    if request.method == 'POST':
        data = request.json or request.form  # ✅ Handle both JSON and form data
        question.text = data['question_text']
        db.session.commit()
        return jsonify({'message': 'Question updated successfully!'})

    return render_template('edit_question.html', question=question)

@admin_bp.route('/add/option/<int:question_id>', methods=['POST'])
def add_option(question_id):
    question = Question.query.get_or_404(question_id)

    # Ensure JSON request
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json()

    # Debugging print
    print("Received data:", data)

    if not data:
        return jsonify({'error': 'Invalid JSON format'}), 400

    if 'option_text' not in data:
        return jsonify({'error': 'Missing option_text'}), 400

    new_option = Option(
        text=data['option_text'],
        is_correct=data.get('is_correct', False),
        question_id=question.id
    )
    db.session.add(new_option)
    db.session.commit()

    return jsonify({'message': 'Option added successfully!'})


@admin_bp.route('/edit/option/<int:id>', methods=['POST'])
def edit_option(id):
    option = Option.query.get_or_404(id)

    # Ensure JSON request
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400

    data = request.get_json()
    
    if 'option_text' not in data:
        return jsonify({'error': 'Missing option_text'}), 400

    option.text = data['option_text']
    option.is_correct = data.get('is_correct', False)  # Boolean flag handling

    db.session.commit()
    return jsonify({'message': 'Option updated successfully!'})


# Delete Option
@admin_bp.route('/delete/option/<int:id>', methods=['DELETE'])
def delete_option(id):
    option = Option.query.get_or_404(id)
    db.session.delete(option)
    db.session.commit()
    return jsonify({'message': 'Option deleted successfully'})

@admin_bp.route('/manage_users')
def manage_users():
    """Display the list of users in the admin panel."""
    users = Users.query.all()
    print(users)
    return render_template('manage_users.html', users=users)

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """Delete a user from the database."""
    user = Users.query.get(user_id)
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('admin.manage_users'))
    
    # Delete related records first to prevent constraint issues
    db.session.query(UserAnswer).filter_by(user_id=user_id).delete()
    db.session.query(UserScore).filter_by(user_id=user_id).delete()

    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully!", "success")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/quiz_stats')
def quiz_stats():
    """Render the quiz stats page with subjects list."""
    subjects = Subject.query.all()
    return render_template('quiz_stats.html', subjects=subjects)

@admin_bp.route('/quiz_stats_data/<int:quiz_id>')
def quiz_stats_data(quiz_id):
    """Fetch quiz stats data for charts."""
    user_scores = UserScore.query.filter_by(quiz_id=quiz_id).all()

    score_distribution = [0, 0, 0, 0]
    scores = []
    time_series = []

    for score_percentage in user_scores:
        percentage = score_percentage.score_percentage
        scores.append({"user": score_percentage.user.username, "score": percentage})
        time_series.append({"date": score_percentage.attempted_at.strftime("%Y-%m-%d"), "score": percentage})

        if percentage <= 40:
            score_distribution[0] += 1
        elif percentage <= 60:
            score_distribution[1] += 1
        elif percentage <= 80:
            score_distribution[2] += 1
        else:
            score_distribution[3] += 1

    return jsonify({"scoreDistribution": score_distribution, "scores": scores, "timeSeries": time_series})


@admin_bp.route('/search')
def admin_search():
    query = request.args.get('q', '').lower()

    matched_users = Users.query.filter(Users.username.ilike(f'%{query}%')).all()
    matched_subjects = Subject.query.filter(Subject.name.ilike(f'%{query}%')).all()
    matched_quizzes = Quiz.query.filter(Quiz.title.ilike(f'%{query}%')).all()

    return render_template('search.html', 
                           users=matched_users, 
                           subjects=matched_subjects, 
                           quizzes=matched_quizzes, 
                           search_query=query)

@admin_bp.route('/reset_all_subjects', methods=['POST'])
def reset_all_subjects():
    try:
        # Delete all subjects (cascades to chapters, quizzes, etc.)
        Subject.query.delete()
        db.session.commit()
        return jsonify({'message': 'All subjects and related data have been deleted successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to delete subjects.', 'error': str(e)}), 500
