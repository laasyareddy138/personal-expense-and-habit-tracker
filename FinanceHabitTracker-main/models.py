from app import db
from datetime import datetime, date, time
from sqlalchemy import func
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    # Relationships
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')
    habits = db.relationship('Habit', backref='user', lazy=True, cascade='all, delete-orphan')
    goals = db.relationship('FinancialGoal', backref='user', lazy=True, cascade='all, delete-orphan')
    milestones = db.relationship('Milestone', backref='user', lazy=True, cascade='all, delete-orphan')
    income_entries = db.relationship('Income', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ExpenseCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    expenses = db.relationship('Expense', backref='category', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False, default=date.today)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    related_habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=True)  # Link to habit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reminder_time = db.Column(db.DateTime, nullable=True)
    reminder_enabled = db.Column(db.Boolean, default=False)

class HabitCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    habits = db.relationship('Habit', backref='category', lazy=True)

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    category_id = db.Column(db.Integer, db.ForeignKey('habit_category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_frequency = db.Column(db.String(20), default='daily')  # daily, weekly, monthly
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    entries = db.relationship('HabitEntry', backref='habit', lazy=True, cascade='all, delete-orphan')
    related_expenses = db.relationship('Expense', backref='related_habit', lazy=True)  # Link to expenses
    reminder_time = db.Column(db.Time, nullable=True)
    reminder_enabled = db.Column(db.Boolean, default=False)
    
    def get_current_streak(self):
        """Calculate current streak for this habit"""
        entries = HabitEntry.query.filter_by(habit_id=self.id, completed=True).order_by(HabitEntry.date.desc()).all()
        if not entries:
            return 0
        
        streak = 0
        current_date = date.today()
        
        for entry in entries:
            if entry.date == current_date:
                streak += 1
                current_date = current_date.replace(day=current_date.day - 1)
            elif entry.date == current_date.replace(day=current_date.day - 1):
                streak += 1
                current_date = current_date.replace(day=current_date.day - 1)
            else:
                break
                
        return streak

    def get_completion_rate(self, days=30):
        """Calculate completion rate for the last N days"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        total_entries = HabitEntry.query.filter(
            HabitEntry.habit_id == self.id,
            HabitEntry.date >= start_date
        ).count()
        
        completed_entries = HabitEntry.query.filter(
            HabitEntry.habit_id == self.id,
            HabitEntry.date >= start_date,
            HabitEntry.completed == True
        ).count()
        
        if total_entries == 0:
            return 0
        return (completed_entries / total_entries) * 100

class HabitEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    completed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('habit_id', 'date', name='unique_habit_date'),)

class FinancialGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    target_date = db.Column(db.Date)
    description = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_progress_percentage(self):
        """Calculate progress percentage towards goal"""
        if self.target_amount <= 0:
            return 0
        return min(100, (self.current_amount / self.target_amount) * 100)

    def is_achieved(self):
        """Check if goal is achieved"""
        return self.current_amount >= self.target_amount

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(100), nullable=False)  # Salary, Freelance, Investment, etc.
    description = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False, default=date.today)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Milestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    milestone_type = db.Column(db.String(50), nullable=False)  # 'habit_streak', 'expense_goal', etc.
    milestone_value = db.Column(db.Integer, nullable=False)  # streak days, amount saved, etc.
    description = db.Column(db.String(200))
    achieved_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_celebrated = db.Column(db.Boolean, default=False)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.String(20))  # 'habit' or 'payment'
    title = db.Column(db.String(100))
    message = db.Column(db.Text)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=True)
    due_date = db.Column(db.DateTime)
    repeat = db.Column(db.String(20))  # 'daily', 'weekly', 'once'
    is_sent = db.Column(db.Boolean, default=False)



'''class NotificationSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    daily_email = db.Column(db.Boolean, default=False)
    habit_reminders = db.Column(db.Boolean, default=False)
    reminder_time = db.Column(db.Time, nullable=True)

    user = db.relationship('User', backref=db.backref('notification_setting', uselist=False))
'''