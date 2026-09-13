# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run the application (runs on port 5001, NOT 5000)
python run.py
```

**Important**: The app runs on port **5001** (not 5000) to avoid conflicts with other Flask apps on the system.

## Database

The database is automatically created on first run via `db.create_all()` in `run.py`. SQLite database file: `pomopet.db`

To reset the database:
```bash
# Delete the database file
rm pomopet.db  # Linux/Mac
del pomopet.db  # Windows

# Restart the app to recreate tables
python run.py
```

## Architecture Overview

### Application Factory Pattern
- `create_app()` in `app/__init__.py` initializes Flask app with config
- Uses blueprints for modular routing:
  - `main_bp` (routes.py) - Main application routes
  - `auth_bp` (auth.py) - Authentication routes at `/auth` prefix

### Database Models & Relationships
**One-to-one**: User ↔ Cat (each user has exactly one cat)
**One-to-many**: User ↔ StudySession (users have multiple study sessions)

Key model interactions:
- `Cat.neglect_check()` - Called on dashboard load, adjusts hunger/happiness/size based on time since last interaction
- `StudySession.complete_session()` - Rewards the user's cat (age+1, happiness+15, size+0.02)
- `Cat.update_mood()` - Automatically sets mood based on hunger/happiness thresholds

### Configuration
`config.py` provides environment-based configs:
- `development` (DEBUG=True, default)
- `production` (DEBUG=False, secure cookies)

Environment set via: `create_app(os.getenv('FLASK_ENV') or 'development')`

## Design System

**Studio Ghibli / Kawaii Stationery Aesthetic**

All pages follow this design language:
- **Fonts**: Patrick Hand (headings), Nunito (body)
- **Colors**: CSS variables in `style.css` (--card-cream, --card-pink, --card-blue, --card-lavender, --card-green, --border-sketch, --accent-*)
- **Paper card style**: Border-radius: 4px, sketchy borders (2.5px solid --border-sketch), box-shadow: 4-5px offset
- **Tape effects**: `::before` pseudo-elements with `rgba(200, 190, 170, 0.6)` background
- **NO EMOJIS**: Use SVG icons or text labels only
- **Slight rotations**: `transform: rotate(-1deg)` to `rotate(1deg)` for paper effect
- **Dashed borders**: Use for dividers/separators

When creating new templates, use inline `{% block extra_css %}` with the above patterns or extend `style.css`.

## Important Implementation Details

### Werkzeug Import Fix
**Do NOT use** `from werkzeug.urls import url_parse` (removed in Werkzeug 3.0+)

**Use instead**: `from urllib.parse import urlparse`

Example in `auth.py`:
```python
from urllib.parse import urlparse
# ...
next_page = request.args.get('next')
if not next_page or urlparse(next_page).netloc != '':
    next_page = url_for('main.dashboard')
```

### Cat Personalities (CAT_PERSONALITIES)
Defined as class variable in `Cat` model (models.py:46-53). Maps cat_type (1-6) to:
- Shadow, Ginger, Mittens, Mochi, Pepper, Tofu

When displaying cat personality traits, access via: `cat.CAT_PERSONALITIES[cat.cat_type]['trait']`

### Session Flow
1. User selects cat → `/cat-selection` (GET: show 6 cats, POST: create Cat)
2. Setup timer → `/timer-setup` (GET: mode selection, POST: create StudySession)
3. Active timer → `/timer/<session_id>` (countdown with JavaScript)
4. Complete → `/api/complete-session/<id>` (POST: marks completed, rewards cat)
5. Dashboard → `/dashboard` (shows cat stats, runs `cat.neglect_check()`)

### API Endpoints (JSON responses)
- `POST /api/complete-session/<id>` - Body: `{focus_score: int}`, Returns: cat stats
- `POST /api/cat/feed` - No body, Returns: `{happiness: int, hunger: int}`
- `POST /api/cat/play` - No body, Returns: `{happiness: int}`

## Git Workflow

Branch strategy:
- `main` - Production-ready
- `develop` - Integration branch
- `feature/*` - Feature branches

**User prefers to run git commands manually** - provide commands but let them execute.

Example workflow:
```bash
git checkout develop
git pull origin develop
git checkout -b feature/feature-name

# After changes
git add .
git commit -m "Descriptive message"
git push -u origin feature/feature-name

# Create PR on GitHub: feature/* → develop
# After merge, feature branches are kept (not deleted)
```

## User Preferences

- **No emojis** - User explicitly dislikes emojis in code/UI. Remove all emojis, replace with SVG/text.
- **Manual git commands** - User wants to learn Git, so provide commands but don't execute them automatically.
- **Explain changes** - User is learning, so explain what code does and why decisions were made.
