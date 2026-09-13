import os
from app import create_app, db
from app.models import User, Cat, StudySession

# Create Flask app
app = create_app(os.getenv('FLASK_ENV') or 'development')

# Shell context for flask shell command
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Cat': Cat,
        'StudySession': StudySession
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables

        # One-time migration: add email_verified column for existing databases
        import sqlite3
        db_path = db.engine.url.database
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("ALTER TABLE user ADD COLUMN email_verified BOOLEAN DEFAULT 0 NOT NULL")
            conn.commit()
            conn.close()
        except Exception:
            pass  # Column already exists

    app.run(debug=True, host='0.0.0.0', port=5001)
