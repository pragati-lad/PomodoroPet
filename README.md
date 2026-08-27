# PomoPet 🐱⏰

A Pomodoro timer with a virtual pet companion that grows as you study!

## Features
- 🐱 10 unique cat personalities (Shadow, Ginger, Luna, Mittens, Whiskers, Neko, Mochi, Pepper, Tofu, Bandit)
- 📈 Cat growth system - ages from newborn to mature based on your study habits
- ⏰ Customizable Pomodoro timer (default: 45min focus / 15min break)
- 📸 Optional camera-based focus tracking (detects phone usage)
- 😊 Mood & hunger system - feed and play with your cat during breaks
- 📊 Study statistics and progress tracking

## Tech Stack
- **Backend**: Python Flask
- **Database**: SQLite (easily upgradable to PostgreSQL)
- **Frontend**: HTML templates (Jinja2) + CSS + JavaScript
- **Authentication**: Flask-Login
- **Camera Detection**: TensorFlow.js (optional)

## Setup Instructions

### 1. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
```bash
# Copy the example file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Edit .env and add your secret key
# SECRET_KEY=your-random-secret-key-here
```

### 4. Run the Application
```bash
python run.py
```

The app will be available at: **http://localhost:5000**

## Project Structure
```
pomodoro/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── models.py            # Database models (User, Cat, StudySession)
│   ├── routes.py            # Main routes
│   ├── auth.py              # Authentication routes
│   ├── templates/           # HTML templates
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── cat_selection.html
│   │   ├── timer_setup.html
│   │   ├── timer.html
│   │   ├── dashboard.html
│   │   └── stats.html
│   └── static/              # CSS, JS, images
│       ├── css/
│       ├── js/
│       └── images/cats/
├── config.py               # Configuration
├── requirements.txt        # Python dependencies
└── run.py                 # Application entry point
```

## Development Workflow

### Branching Strategy
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features

### Creating a New Feature
```bash
git checkout develop
git pull origin develop
git checkout -b feature/feature-name

# Make changes, commit
git add .
git commit -m "Add feature description"

# Push and create PR
git push -u origin feature/feature-name
```

## Database Models

### User
- Username, email, password
- One cat per user
- Study session history

### Cat
- 10 personality types with unique traits
- Age (in days), mood, hunger, happiness
- Growth stages: newborn → kitten → young → adult → mature
- Size changes based on care

### StudySession
- Focus/break duration
- Completion status
- Focus score (affected by distractions)
- Timestamps

## API Endpoints

- `POST /auth/login` - User login
- `POST /auth/signup` - User registration
- `GET /auth/logout` - User logout
- `GET /cat-selection` - Choose and name cat
- `POST /cat-selection` - Create cat
- `GET /timer-setup` - Configure timer
- `POST /timer-setup` - Start session
- `GET /timer/<id>` - Timer page
- `POST /api/complete-session/<id>` - Complete session
- `POST /api/cat/feed` - Feed cat
- `POST /api/cat/play` - Play with cat
- `GET /stats` - View statistics

## Future Enhancements
- [ ] Implement TensorFlow.js phone detection
- [ ] Add more cat animations
- [ ] Leaderboard/social features
- [ ] Mobile responsive design improvements
- [ ] PWA support
- [ ] Dark mode
- [ ] Multiple cat support
- [ ] Achievement system

## License
MIT
