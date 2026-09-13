# PomoPet 🐱

A Pomodoro timer app with a virtual cat companion that grows as you study.

## Features

- 🐱 Choose from 6 unique cat personalities
- ⏰ Customizable focus and break timers
- 📈 Cat grows and evolves based on completed sessions
- 😊 Mood & hunger system - care for your cat during breaks
- 📊 Track your study statistics
- ✉️ Email verification for account security

## Tech Stack

- Flask (Python web framework)
- SQLite database
- Flask-Login for authentication
- Flask-Mail for email verification
- Studio Ghibli-inspired UI design

## Quick Start

```bash
# Clone and navigate to project
cd pomodoro

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Gmail credentials

# Run the app
python run.py
```

Visit **http://localhost:5001**

## Environment Setup

Create a `.env` file with:

```env
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
```

**Note:** Use a Gmail App Password, not your regular password. [Generate one here](https://myaccount.google.com/apppasswords)

## Project Structure

```
├── app/
│   ├── auth.py           # Authentication & email verification
│   ├── routes.py         # Main app routes
│   ├── models.py         # Database models
│   ├── templates/        # HTML templates
│   └── static/           # CSS, JS, audio files
├── config.py             # App configuration
├── run.py               # Application entry point
└── Procfile             # Deployment configuration
```

## Cat Personalities

1. **Shadow** - Mysterious and independent
2. **Ginger** - Energetic and playful
3. **Mittens** - Gentle and affectionate
4. **Mochi** - Lazy and food-loving
5. **Pepper** - Curious and adventurous
6. **Tofu** - Calm and wise

## Deployment

Configured for deployment on Render, Railway, or similar platforms.

See [CLAUDE.md](CLAUDE.md) for detailed development instructions.

## License

MIT
