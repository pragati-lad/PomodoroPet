from datetime import datetime, date, timedelta
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """User model"""
    __tablename__ = 'users'  # Avoid PostgreSQL reserved keyword "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    daily_goal = db.Column(db.Integer, default=60, nullable=False)  # Daily study goal in minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    cat = db.relationship('Cat', backref='owner', uselist=False, cascade='all, delete-orphan')
    study_sessions = db.relationship('StudySession', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Cat(db.Model):
    """Cat model - each user has one cat"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    cat_type = db.Column(db.Integer, nullable=False)  # 1-6 for personality types
    age_days = db.Column(db.Integer, default=0)  # Age in "cat days"
    mood = db.Column(db.String(20), default='happy')  # happy, neutral, sad, angry
    hunger = db.Column(db.Integer, default=50)  # 0-100
    happiness = db.Column(db.Integer, default=80)  # 0-100
    size = db.Column(db.Float, default=1.0)  # Growth multiplier
    last_fed = db.Column(db.DateTime, default=datetime.utcnow)
    last_interaction = db.Column(db.DateTime, default=datetime.utcnow)
    last_growth_date = db.Column(db.Date, nullable=True)  # Last real date the cat aged
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Cat personalities (1-6)
    CAT_PERSONALITIES = {
        1: {'name': 'Shadow', 'trait': 'Mysterious and independent'},
        2: {'name': 'Ginger', 'trait': 'Energetic and demanding'},
        3: {'name': 'Mittens', 'trait': 'Playful and mischievous'},
        4: {'name': 'Mochi', 'trait': 'Lazy and sleepy'},
        5: {'name': 'Pepper', 'trait': 'Sassy and moody'},
        6: {'name': 'Tofu', 'trait': 'Gentle and supportive'}
    }

    def get_growth_stage(self):
        """Get cat's current growth stage"""
        if self.age_days < 14:
            return 'newborn'
        elif self.age_days < 60:
            return 'kitten'
        elif self.age_days < 180:
            return 'young'
        elif self.age_days < 365:
            return 'adult'
        else:
            return 'mature'

    def update_mood(self):
        """Update cat's mood based on hunger and happiness"""
        if self.hunger > 80:
            self.mood = 'angry'
        elif self.happiness < 30:
            self.mood = 'sad'
        elif self.happiness > 70:
            self.mood = 'happy'
        else:
            self.mood = 'neutral'

    def feed(self):
        """Feed the cat"""
        self.hunger = max(0, self.hunger - 30)
        self.happiness = min(100, self.happiness + 10)
        self.last_fed = datetime.utcnow()
        self.update_mood()

    def play(self):
        """Play with the cat"""
        self.happiness = min(100, self.happiness + 20)
        self.hunger = min(100, self.hunger + 10)
        self.last_interaction = datetime.utcnow()
        self.update_mood()

    def neglect_check(self):
        """Check if cat is being neglected and adjust stats"""
        time_since_fed = datetime.utcnow() - self.last_fed
        time_since_interaction = datetime.utcnow() - self.last_interaction

        # Increase hunger over time
        hours_since_fed = time_since_fed.total_seconds() / 3600
        self.hunger = min(100, self.hunger + int(hours_since_fed * 5))

        # Decrease happiness over time
        hours_since_interaction = time_since_interaction.total_seconds() / 3600
        self.happiness = max(0, self.happiness - int(hours_since_interaction * 3))

        # Shrink if severely neglected
        if self.hunger > 80 and self.happiness < 20:
            self.size = max(0.5, self.size - 0.05)

        self.update_mood()

    def __repr__(self):
        return f'<Cat {self.name} ({self.get_growth_stage()})>'


class StudySession(db.Model):
    """Study session model - tracks Pomodoro sessions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    focus_duration = db.Column(db.Integer, default=45)  # Minutes
    break_duration = db.Column(db.Integer, default=15)  # Minutes
    completed = db.Column(db.Boolean, default=False)
    focus_score = db.Column(db.Integer, default=100)  # 0-100, based on distractions
    actual_duration = db.Column(db.Integer, nullable=True)  # Actual minutes studied
    camera_enabled = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    def complete_session(self, focus_score=100, actual_duration=None):
        """Mark session as completed and reward cat if daily goal is met"""
        self.completed = True
        self.focus_score = focus_score
        self.actual_duration = actual_duration
        self.completed_at = datetime.utcnow()

        cat = self.user.cat
        if cat:
            # Always reward happiness and size per session
            cat.happiness = min(100, cat.happiness + 15)
            cat.size = min(2.0, cat.size + 0.02)

            # Cat ages only if daily goal is met AND hasn't grown today
            today = datetime.utcnow().date()
            if cat.last_growth_date != today:
                # Sum all completed sessions today (including this one)
                this_duration = actual_duration or self.focus_duration
                total_today = this_duration
                for s in self.user.study_sessions.filter(
                    StudySession.completed == True,
                    StudySession.id != self.id
                ).all():
                    if s.completed_at and s.completed_at.date() == today:
                        total_today += (s.actual_duration or s.focus_duration)

                if total_today >= self.user.daily_goal:
                    cat.age_days += 1
                    cat.last_growth_date = today

            cat.update_mood()

    def __repr__(self):
        return f'<StudySession {self.id} - {self.started_at}>'
