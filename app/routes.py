from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Cat, StudySession
from datetime import datetime, date, timedelta

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

    # Calculate today's study progress
    today = datetime.utcnow().date()
    today_sessions = StudySession.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).all()
    minutes_today = sum(
        (s.actual_duration if s.actual_duration is not None else s.focus_duration)
        for s in today_sessions
        if s.completed_at and s.completed_at.date() == today
    )
    daily_goal = current_user.daily_goal
    goal_met = minutes_today >= daily_goal
    grew_today = current_user.cat.last_growth_date == today

    return render_template('dashboard.html',
        cat=current_user.cat,
        minutes_today=minutes_today,
        daily_goal=daily_goal,
        goal_met=goal_met,
        grew_today=grew_today
    )


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

        if not cat_name or cat_type < 1 or cat_type > 6:
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

    data = request.json
    focus_score = int(data.get('focus_score', 100))
    actual_duration = data.get('actual_duration')
    if actual_duration is not None:
        actual_duration = int(actual_duration)
    session.complete_session(focus_score, actual_duration=actual_duration)
    db.session.commit()

    return jsonify({
        'success': True,
        'cat_age': current_user.cat.age_days,
        'cat_stage': current_user.cat.get_growth_stage(),
        'cat_happiness': current_user.cat.happiness
    })


@main_bp.route('/api/create-session', methods=['POST'])
@login_required
def create_session():
    """API endpoint to create a new study session (used by Repeat button)"""
    data = request.json
    focus_duration = int(data.get('focus_duration', 45))
    break_duration = int(data.get('break_duration', 15))
    camera_enabled = bool(data.get('camera_enabled', False))

    session = StudySession(
        user_id=current_user.id,
        focus_duration=focus_duration,
        break_duration=break_duration,
        camera_enabled=camera_enabled
    )
    db.session.add(session)
    db.session.commit()

    return jsonify({
        'success': True,
        'session_id': session.id
    })


@main_bp.route('/api/set-goal', methods=['POST'])
@login_required
def set_goal():
    """API endpoint to set daily study goal"""
    data = request.get_json()
    goal = data.get('daily_goal', 60)
    goal = max(10, min(480, int(goal)))  # Clamp between 10 and 480 minutes
    current_user.daily_goal = goal
    db.session.commit()
    return jsonify({'success': True, 'daily_goal': goal})


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

    # Use actual_duration when available, fall back to focus_duration
    def effective_minutes(s):
        return s.actual_duration if s.actual_duration is not None else s.focus_duration

    total_sessions = len(sessions)
    total_focus_time = sum(effective_minutes(s) for s in sessions)
    avg_focus_score = sum(s.focus_score for s in sessions) / total_sessions if total_sessions > 0 else 0

    # --- Current week daily breakdown (Mon=0 ... Sun=6) ---
    today = datetime.utcnow().date()
    monday = today - timedelta(days=today.weekday())
    week_days = []
    for i in range(7):
        day = monday + timedelta(days=i)
        day_sessions = StudySession.query.filter(
            StudySession.user_id == current_user.id,
            StudySession.completed == True,
            db.func.date(StudySession.completed_at) == day
        ).all()
        minutes = sum(effective_minutes(s) for s in day_sessions)
        week_days.append({
            'label': day.strftime('%a'),
            'date': day,
            'minutes': minutes,
            'is_today': day == today
        })
    week_max = max((d['minutes'] for d in week_days), default=1) or 1

    # --- Last 4 weeks comparison ---
    weeks = []
    for w in range(4):
        week_start = monday - timedelta(weeks=w)
        week_end = week_start + timedelta(days=6)
        week_sessions = StudySession.query.filter(
            StudySession.user_id == current_user.id,
            StudySession.completed == True,
            db.func.date(StudySession.completed_at) >= week_start,
            db.func.date(StudySession.completed_at) <= week_end
        ).all()
        total_mins = sum(effective_minutes(s) for s in week_sessions)
        label = 'This week' if w == 0 else f'{w}w ago'
        weeks.append({
            'label': label,
            'start': week_start,
            'end': week_end,
            'minutes': total_mins,
            'count': len(week_sessions)
        })
    weeks.reverse()  # oldest first for chart display
    weeks_max = max((w['minutes'] for w in weeks), default=1) or 1

    # --- Study streak (consecutive days with at least 1 completed session) ---
    streak = 0
    check_date = today
    while True:
        has_session = StudySession.query.filter(
            StudySession.user_id == current_user.id,
            StudySession.completed == True,
            db.func.date(StudySession.completed_at) == check_date
        ).first()
        if has_session:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    return render_template('stats.html',
                         cat=current_user.cat,
                         sessions=sessions,
                         total_sessions=total_sessions,
                         total_focus_time=total_focus_time,
                         avg_focus_score=avg_focus_score,
                         streak=streak,
                         week_days=week_days,
                         week_max=week_max,
                         weeks=weeks,
                         weeks_max=weeks_max)
