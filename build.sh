#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python -c "
import os
os.environ.setdefault('FLASK_ENV', 'production')
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
"
