import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_apscheduler import APScheduler
from flask_migrate import Migrate

#from flask_migrate import Migrate
#from flask_apscheduler import APScheduler
#from flask_mail import Message

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the Flask app
app = Flask(__name__)
app.secret_key = ""
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure PostgreSQL database
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://neondb_owner:npg_8oZjPiXvH7za@ep-bitter-haze-a5sacvqf-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

migrate = Migrate(app, db)
# Initialize the database with the app
db.init_app(app)

# Initialize login manager
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

#migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    # Import models to ensure tables are created
    import models
    db.create_all()
    
    # Create sample data for demonstration
    from datetime import datetime, timedelta
    from models import ExpenseCategory, HabitCategory
    
    # Create default expense categories
    default_expense_categories = [
        "Food & Dining", "Transportation", "Shopping", "Entertainment",
        "Bills & Utilities", "Healthcare", "Education", "Travel", "Other"
    ]
    
    for cat_name in default_expense_categories:
        if not ExpenseCategory.query.filter_by(name=cat_name).first():
            category = ExpenseCategory(name=cat_name)
            db.session.add(category)
    
    # Create default habit categories
    default_habit_categories = [
        "Health & Fitness", "Learning", "Productivity", "Wellness",
        "Social", "Hobbies", "Finance", "Career", "Other"
    ]
    
    for cat_name in default_habit_categories:
        if not HabitCategory.query.filter_by(name=cat_name).first():
            category = HabitCategory(name=cat_name)
            db.session.add(category)
    
    db.session.commit()

'''
scheduler = APScheduler()

def send_daily_emails():
    with app.app_context():
        users = User.query.join(NotificationSetting).filter(NotificationSetting.daily_email == True).all()
        for user in users:
            msg = Message("Your Daily Summary", recipients=[user.email])
            msg.body = f"Hi {user.username}, here is your daily progress summary!"
            mail.send(msg)

scheduler.add_job(id='daily_summary', func=send_daily_emails, trigger='cron', hour=7)  # 7 AM
scheduler.start()
'''



# Import routes after app creation to avoid circular imports
from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
