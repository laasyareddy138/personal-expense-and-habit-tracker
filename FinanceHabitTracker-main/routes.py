from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import (User, Expense, ExpenseCategory, Habit, HabitCategory, 
                   HabitEntry, FinancialGoal, Milestone, Income)
from datetime import datetime, date, timedelta
from sqlalchemy import func, desc
import json
from ai_insights import get_expense_insights, get_habit_insights

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/signup.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Registration successful! Welcome to your expense and habit tracker!', 'success')
        return redirect(url_for('index'))
    
    return render_template('auth/signup.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            try:
                current_user.username = request.form['username']
                current_user.email = request.form['email']
                db.session.commit()
                flash('Profile updated successfully!', 'success')
            except Exception as e:
                flash(f'Error updating profile: {str(e)}', 'error')
                
        elif action == 'change_password':
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            
            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'error')
            elif new_password != confirm_password:
                flash('New passwords do not match', 'error')
            else:
                try:
                    current_user.set_password(new_password)
                    db.session.commit()
                    flash('Password changed successfully!', 'success')
                except Exception as e:
                    flash(f'Error changing password: {str(e)}', 'error')
        
        return redirect(url_for('profile'))
    
    # Get user statistics
    total_expenses = Expense.query.filter_by(user_id=current_user.id).count()
    total_habits = Habit.query.filter_by(user_id=current_user.id).count()
    total_goals = FinancialGoal.query.filter_by(user_id=current_user.id).count()
    
    return render_template('profile.html', 
                         total_expenses=total_expenses,
                         total_habits=total_habits,
                         total_goals=total_goals)

@app.route('/')
@login_required
def index():
    """Dashboard showing overview of expenses, habits, and goals"""
    # Get recent expenses for current user
    recent_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(desc(Expense.date)).limit(5).all()
    
    # Get active habits with today's status for current user
    active_habits = Habit.query.filter_by(user_id=current_user.id, is_active=True).all()
    today = date.today()
    
    habits_status = []
    for habit in active_habits:
        entry = HabitEntry.query.filter_by(habit_id=habit.id, date=today).first()
        habits_status.append({
            'habit': habit,
            'completed_today': entry.completed if entry else False,
            'current_streak': habit.get_current_streak()
        })
    
    # Get active financial goals for current user
    active_goals = FinancialGoal.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    # Calculate this month's total expenses for current user
    current_month = datetime.now().replace(day=1).date()
    monthly_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.date >= current_month
    ).scalar() or 0
    
    # Get uncelebrated milestones for current user
    uncelebrated_milestones = Milestone.query.filter_by(user_id=current_user.id, is_celebrated=False).all()
    
    return render_template('index.html', 
                         recent_expenses=recent_expenses,
                         habits_status=habits_status,
                         active_goals=active_goals,
                         monthly_expenses=monthly_expenses,
                         uncelebrated_milestones=uncelebrated_milestones)

@app.route('/expenses')
@login_required
def expenses():
    """Expense tracking page"""
    page = request.args.get('page', 1, type=int)
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(desc(Expense.date)).paginate(
        page=page, per_page=20, error_out=False
    )
    categories = ExpenseCategory.query.all()
    habits = Habit.query.filter_by(user_id=current_user.id, is_active=True).all()
    return render_template('expenses.html', expenses=expenses, categories=categories, habits=habits)

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    """Add a new expense"""
    try:
        amount = float(request.form['amount'])
        description = request.form['description']
        category_id = int(request.form['category_id'])
        expense_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        related_habit_id = request.form.get('related_habit_id')
        reminder_enabled = bool(request.form.get('reminder_enabled'))
        reminder_time = request.form.get('reminder_time')
        if reminder_enabled and reminder_time:
            expense.reminder_time = datetime.strptime(reminder_time, '%H:%M')
            expense.reminder_enabled = True

        expense = Expense(
            amount=amount,
            description=description,
            category_id=category_id,
            user_id=current_user.id,
            date=expense_date,
            related_habit_id=int(related_habit_id) if related_habit_id else None
        )
        
        
        db.session.add(expense)
        db.session.commit()
        
        flash('Expense added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding expense: {str(e)}', 'error')
    
    return redirect(url_for('expenses'))

@app.route('/delete_expense/<int:expense_id>')
def delete_expense(expense_id):
    """Delete a financial goal"""
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    flash('expense deleted successfully!', 'success')
    return redirect(url_for('expenses'))

@app.route('/habits')
@login_required
def habits():
    """Habit tracking page"""
    active_habits = Habit.query.filter_by(user_id=current_user.id, is_active=True).all()
    categories = HabitCategory.query.all()
    today = date.today()
    
    habits_data = []
    for habit in active_habits:
        entry = HabitEntry.query.filter_by(habit_id=habit.id, date=today).first()
        habits_data.append({
            'habit': habit,
            'entry': entry,
            'completed_today': entry.completed if entry else False,
            'current_streak': habit.get_current_streak(),
            'completion_rate': habit.get_completion_rate()
        })
    
    return render_template('habits.html', habits_data=habits_data, categories=categories)

@app.route('/add_habit', methods=['POST'])
@login_required
def add_habit():
    """Add a new habit"""
    try:
        name = request.form['name']
        description = request.form['description']
        category_id = int(request.form['category_id'])
        target_frequency = request.form['target_frequency']
        reminder_enabled = bool(request.form.get('reminder_enabled'))
        reminder_time = request.form.get('reminder_time')
        

        habit = Habit(
            name=name,
            description=description,
            category_id=category_id,
            user_id=current_user.id,
            target_frequency=target_frequency
        )
        
        db.session.add(habit)
        db.session.commit()
        
        flash('Habit added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding habit: {str(e)}', 'error')
    
    return redirect(url_for('habits'))

@app.route('/toggle_habit/<int:habit_id>')
def toggle_habit(habit_id):
    """Toggle habit completion for today"""
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    today = date.today()
    
    entry = HabitEntry.query.filter_by(habit_id=habit_id, date=today).first()
    
    if entry:
        entry.completed = not entry.completed
    else:
        entry = HabitEntry(habit_id=habit_id, date=today, completed=True)
        db.session.add(entry)
    
    db.session.commit()
    
    # Check for streak milestones
    if entry.completed:
        streak = habit.get_current_streak()
        milestone_values = [7, 30, 100, 365]  # Week, month, 100 days, year
        
        for value in milestone_values:
            if streak == value:
                milestone = Milestone(
                    milestone_type='habit_streak',
                    milestone_value=value,
                    description=f'Maintained "{habit.name}" for {value} days!'
                )
                db.session.add(milestone)
                db.session.commit()
                break
    
    return redirect(url_for('habits'))

@app.route('/delete_habit/<int:habit_id>')
def delete_habit(habit_id) :
    """Delete a habit"""
    habit = Habit.query.get_or_404(habit_id)
    db.session.delete(habit)
    db.session.commit()
    flash('Habit deleted successfully!', 'success')
    return redirect(url_for('habits'))

@app.route('/goals')
def goals():
    """Financial goals page"""
    active_goals = FinancialGoal.query.filter_by(is_active=True).all()
    for goal in active_goals:
        if goal.target_date:
            goal.days_left = (goal.target_date - date.today()).days
        else:
            goal.days_left = None
    return render_template('goals.html', goals=active_goals)

@app.route('/add_goal', methods=['POST'])
def add_goal():
    """Add a new financial goal"""
    try:
        name = request.form['name']
        target_amount = float(request.form['target_amount'])
        target_date = datetime.strptime(request.form['target_date'], '%Y-%m-%d').date()
        description = request.form['description']
        
        goal = FinancialGoal(
            name=name,
            target_amount=target_amount,
            target_date=target_date,
            description=description,
            user_id=current_user.id
        )
        
        db.session.add(goal)
        db.session.commit()
        
        flash('Goal added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding goal: {str(e)}', 'error')
    
    return redirect(url_for('goals'))

@app.route('/delete_goal/<int:goal_id>')
def delete_goal(goal_id):
    """Delete a financial goal"""
    goal = FinancialGoal.query.get_or_404(goal_id)
    db.session.delete(goal)
    db.session.commit()
    flash('Goal deleted successfully!', 'success')
    return redirect(url_for('goals'))

@app.route('/income')
@login_required
def income():
    """Income tracking page"""
    income_entries = Income.query.filter_by(user_id=current_user.id).order_by(desc(Income.date)).all()
    
    # Calculate monthly totals
    monthly_totals = db.session.query(
        func.TO_CHAR(Income.date, 'YYYY-MM').label('month'),
        func.sum(Income.amount).label('total')
    ).filter(Income.user_id == current_user.id).group_by(
        func.TO_CHAR(Income.date, 'YYYY-MM')
    ).order_by(desc('month')).limit(6).all()
    
    return render_template('income.html', 
                         income_entries=income_entries,
                         monthly_totals=monthly_totals)

@app.route('/add_income', methods=['POST'])
@login_required
def add_income():
    """Add a new income entry"""
    try:
        amount = float(request.form['amount'])
        source = request.form['source']
        description = request.form.get('description', '')
        date_str = request.form['date']
        income_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        income = Income(
            amount=amount,
            source=source,
            description=description,
            date=income_date,
            user_id=current_user.id
        )
        
        db.session.add(income)
        db.session.commit()
        
        flash('Income added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding income: {str(e)}', 'error')
    
    return redirect(url_for('income'))

@app.route('/delete_income/<int:income_id>')
def delete_income(income_id) :
    """Delete a income entry"""
    income = Income.query.get_or_404(income_id)
    db.session.delete(income)
    db.session.commit()
    flash('Income deleted successfully!', 'success')
    return redirect(url_for('income'))

@app.route('/update_goal/<int:goal_id>', methods=['POST'])
def update_goal(goal_id):
    """Update progress on a financial goal"""
    goal = FinancialGoal.query.get_or_404(goal_id)
    
    try:
        amount_to_add = float(request.form['amount'])
        goal.current_amount += amount_to_add
        
        db.session.commit()
        
        # Check if goal is achieved
        if goal.is_achieved() and goal.current_amount - amount_to_add < goal.target_amount:
            milestone = Milestone(
                milestone_type='financial_goal',
                milestone_value=int(goal.target_amount),
                description=f'Achieved financial goal: {goal.name}!'
            )
            db.session.add(milestone)
            db.session.commit()
        
        flash('Goal updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating goal: {str(e)}', 'error')
    
    return redirect(url_for('goals'))

@app.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard with charts and insights"""
    # Get expense data for charts
    current_month = datetime.now().replace(day=1).date()
    monthly_expenses = db.session.query(
        ExpenseCategory.name,
        func.sum(Expense.amount).label('total')
    ).join(Expense).filter(
        Expense.date >= current_month,
        Expense.user_id == current_user.id
    ).group_by(ExpenseCategory.name).all()
    
    # Get daily expenses for the last 30 days
    thirty_days_ago = date.today() - timedelta(days=30)
    daily_expenses = db.session.query(
        Expense.date,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.date >= thirty_days_ago,
        Expense.user_id == current_user.id
    ).group_by(Expense.date).all()
    
    # Get habit completion data
    active_habits = Habit.query.filter_by(user_id=current_user.id, is_active=True).all()
    habit_completion_data = []
    for habit in active_habits:
        completion_rate = habit.get_completion_rate()
        habit_completion_data.append({
            'name': habit.name,
            'completion_rate': completion_rate
        })

    # Get income data
    monthly_income = db.session.query(func.sum(Income.amount)).filter(
        Income.date >= current_month,
        Income.user_id == current_user.id
    ).scalar() or 0

    # Sum of expenses this month
    monthly_expense_total = sum([row.total for row in monthly_expenses]) if monthly_expenses else 0
    
    # Get AI insights
    expense_insights = get_expense_insights(current_user.id)
    habit_insights = get_habit_insights(current_user.id)
    
    return render_template('analytics.html',
                         monthly_expenses=monthly_expenses,
                         daily_expenses=daily_expenses,
                         monthly_income=monthly_income,
                         monthly_expense_total=monthly_expense_total,
                         habit_completion_data=habit_completion_data,
                         expense_insights=expense_insights,
                         habit_insights=habit_insights)

@app.route('/celebrate_milestone/<int:milestone_id>')
def celebrate_milestone(milestone_id):
    """Mark milestone as celebrated and show celebration page"""
    milestone = Milestone.query.get_or_404(milestone_id)
    milestone.is_celebrated = True
    db.session.commit()
    
    return render_template('milestone.html', milestone=milestone)

@app.route('/api/chart_data')
def chart_data():
    """API endpoint for chart data (exception to avoid JSON APIs rule for charts)"""
    chart_type = request.args.get('type')
    
    if chart_type == 'expenses_by_category':
        current_month = datetime.now().replace(day=1).date()
        data = db.session.query(
            ExpenseCategory.name,
            func.sum(Expense.amount).label('total')
        ).join(Expense).filter(
            Expense.date >= current_month,
            Expense.user_id == current_user.id
        ).group_by(ExpenseCategory.name).all()
        
        return jsonify({
            'labels': [row.name for row in data],
            'data': [float(row.total) for row in data]
        })
    
    elif chart_type == 'daily_expenses':
        thirty_days_ago = date.today() - timedelta(days=30)
        data = db.session.query(
            Expense.date,
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.date >= thirty_days_ago,
            Expense.user_id == current_user.id
        ).group_by(Expense.date).order_by(Expense.date).all()
        
        return jsonify({
            'labels': [str(row.date) for row in data],
            'data': [float(row.total) for row in data]
        })
    
    
        
    elif chart_type == 'weekly_expenses':
        today = datetime.today().date()
        start_date = today - timedelta(weeks=4)

        weekly_data = (
            db.session.query(
                func.to_char(Expense.date, 'IYYY-IW').label('week'),
                func.sum(Expense.amount).label('total')
            )
            .filter(
                Expense.date >= start_date,
                Expense.user_id == current_user.id
            )
            .group_by('week')
            .order_by('week')
            .all()
        )

        return jsonify({
            'labels': [row.week for row in weekly_data],
            'data': [float(row.total) for row in weekly_data]
        })

    elif chart_type == 'yearly_expenses':
        current_year = datetime.today().year

        yearly_data = (
            db.session.query(
                func.to_char(Expense.date, 'YYYY-MM').label('month'),
                func.sum(Expense.amount).label('total')
            )
            .filter(
                func.extract('year', Expense.date) == current_year,
                Expense.user_id == current_user.id
            ).group_by('month')
            .order_by('month')
            .all()
        )

        return jsonify({
            'labels': [row.month for row in yearly_data],
            'data': [float(row.total) for row in yearly_data]
        })
    
    elif chart_type == 'habit_completion':
        active_habits = Habit.query.filter_by(user_id=current_user.id, is_active=True).all()
        data = []
        labels = []
        
        for habit in active_habits:
            labels.append(habit.name)
            data.append(habit.get_completion_rate())
        
        return jsonify({
            'labels': labels,
            'data': data
        })

    elif chart_type == 'habit_expenses':
        habit_data = (
            db.session.query(
                Habit.name,
                func.sum(Expense.amount)
            )
            .join(Expense, Expense.related_habit_id == Habit.id)
            .filter(
                Expense.user_id == current_user.id,
                Habit.user_id == current_user.id
            )
            .group_by(Habit.id)
            .all()
        )
        if not habit_data:
            return jsonify({'labels': [], 'data': []})

        return jsonify({
            'labels': [row[0] for row in habit_data],
            'data': [float(row[1]) for row in habit_data]
        })
    
    return jsonify({'error': 'Invalid chart type'})



@app.route('/notifications', methods=['GET', 'POST'])
@login_required
def notifications():
    if request.method == 'POST':
        setting = current_user.notification_setting
        if not setting:
            setting = NotificationSetting(user_id=current_user.id)

        setting.daily_email = 'daily_email' in request.form
        setting.habit_reminders = 'habit_reminders' in request.form
        time_str = request.form.get('reminder_time', '00:00')
        setting.reminder_time = datetime.strptime(time_str, '%H:%M').time()

        db.session.add(setting)
        db.session.commit()
        flash('Notification settings saved successfully!', 'success')
        return redirect(url_for('notifications'))

    return render_template('notifications.html')
    
'''    if request.method == 'POST':
        current_user.daily_summary = bool(request.form.get('daily_summary'))
        current_user.habit_reminders = bool(request.form.get('habit_reminders'))

        reminder_hour = int(request.form.get('reminder_hour', 0))
        reminder_minute = int(request.form.get('reminder_minute', 0))
        current_user.reminder_time = time(reminder_hour, reminder_minute)

        db.session.commit()
        flash("Notification settings saved!", "success")
        return redirect(url_for('notifications'))

    return render_template('notifications.html', user=current_user)
    '''
    
