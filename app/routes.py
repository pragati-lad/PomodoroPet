from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Cat, StudySession
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - redirect based on user's progress"""
    # If user doesn't have a cat, go to cat selection
    if not current_user.cat:
        return redirect(url_for('main.cat_selection'))

    # Check for neglect
    current_user.cat.neglect_check()
    db.session.commit()

    return render_template('dashboard.html', cat=current_user.cat)


@main_bp.route('/cat-selection', methods=['GET', 'POST'])
@login_required
def cat_selection():
    """Cat selection page"""
    # If user already has a cat, redirect to dashboard
    if current_user.cat:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        cat_type = int(request.form.get('cat_type'))
        cat_name = request.form.get('cat_name')

        if not cat_name or cat_type < 1 or cat_type > 10:
            return jsonify({'error': 'Invalid cat selection'}), 400

        # Create new cat
        cat = Cat(
            user_id=current_user.id,
            name=cat_name,
            cat_type=cat_type
        )
        db.session.add(cat)
        db.session.commit()

        return redirect(url_for('main.timer_setup'))

    return render_template('cat_selection.html', personalities=Cat.CAT_PERSONALITIES)


@main_bp.route('/timer-setup', methods=['GET', 'POST'])
@login_required
def timer_setup():
    """Timer setup page - choose default or custom"""
    if request.method == 'POST':
        mode = request.form.get('mode')  # 'default' or 'custom'
        camera_enabled = request.form.get('camera') == 'on'

        if mode == 'custom':
            focus_duration = int(request.form.get('focus_duration', 45))
            break_duration = int(request.form.get('break_duration', 15))
        else:
            focus_duration = 45
            break_duration = 15

        # Create new study session
        session = StudySession(
            user_id=current_user.id,
            focus_duration=focus_duration,
            break_duration=break_duration,
            camera_enabled=camera_enabled
        )
        db.session.add(session)
        db.session.commit()

        return redirect(url_for('main.timer', session_id=session.id))

    return render_template('timer_setup.html')


@main_bp.route('/timer/<int:session_id>')
@login_required
def timer(session_id):
    """Pomodoro timer page"""
    session = StudySession.query.get_or_404(session_id)

    if session.user_id != current_user.id:
        return redirect(url_for('main.dashboard'))

    return render_template('timer.html', session=session, cat=current_user.cat)


@main_bp.route('/api/complete-session/<int:session_id>', methods=['POST'])
@login_required
def complete_session(session_id):
    """API endpoint to complete a study session"""
    session = StudySession.query.get_or_404(session_id)

    if session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    focus_score = int(request.json.get('focus_score', 100))
    session.complete_session(focus_score)
    db.session.commit()

    return jsonify({
        'success': True,
        'cat_age': current_user.cat.age_days,
        'cat_stage': current_user.cat.get_growth_stage(),
        'cat_happiness': current_user.cat.happiness
    })


@main_bp.route('/api/cat/feed', methods=['POST'])
@login_required
def feed_cat():
    """API endpoint to feed cat"""
    cat = current_user.cat
    if not cat:
        return jsonify({'error': 'No cat found'}), 404

    cat.feed()
    db.session.commit()

    return jsonify({
        'success': True,
        'hunger': cat.hunger,
        'happiness': cat.happiness,
        'mood': cat.mood
    })


@main_bp.route('/api/cat/play', methods=['POST'])
@login_required
def play_with_cat():
    """API endpoint to play with cat"""
    cat = current_user.cat
    if not cat:
        return jsonify({'error': 'No cat found'}), 404

    cat.play()
    db.session.commit()

    return jsonify({
        'success': True,
        'hunger': cat.hunger,
        'happiness': cat.happiness,
        'mood': cat.mood
    })


@main_bp.route('/stats')
@login_required
def stats():
    """Statistics page"""
    sessions = StudySession.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).order_by(StudySession.completed_at.desc()).limit(30).all()

    total_sessions = len(sessions)
    total_focus_time = sum(s.focus_duration for s in sessions)
    avg_focus_score = sum(s.focus_score for s in sessions) / total_sessions if total_sessions > 0 else 0

    return render_template('stats.html',
                         cat=current_user.cat,
                         sessions=sessions,
                         total_sessions=total_sessions,
                         total_focus_time=total_focus_time,
                         avg_focus_score=avg_focus_score)
