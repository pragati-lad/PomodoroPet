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

    app.run(debug=True, host='0.0.0.0', port=5001)
