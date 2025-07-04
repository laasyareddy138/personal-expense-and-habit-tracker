import os
import json
from datetime import date, timedelta
from openai import OpenAI
from models import Expense, Habit, HabitEntry, ExpenseCategory
from app import db
from sqlalchemy import func

# Initialize OpenAI client
OPENAI_API_KEY = "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"
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def get_expense_insights(user_id):
    """Generate insights for expense patterns"""
    try:
        # Get expense data for the last 30 days
        thirty_days_ago = date.today() - timedelta(days=30)
        expenses = db.session.query(
            ExpenseCategory.name,
            func.sum(Expense.amount).label('total'),
            func.count(Expense.id).label('count')
        ).join(Expense).filter(
            Expense.date >= thirty_days_ago,
            Expense.user_id == user_id
        ).group_by(ExpenseCategory.name).all()
        
        if not expenses:
            return ["Start tracking your expenses to see personalized spending insights here"]
        
        # Calculate insights based on spending patterns
        insights = []
        total_spent = sum(float(exp.total) for exp in expenses)
        
        # Find top spending category
        top_category = max(expenses, key=lambda x: x.total)
        top_percentage = (float(top_category.total) / total_spent) * 100
        
        if top_percentage > 50:
            insights.append(f"⚠️ {top_category.name} dominates your spending at {top_percentage:.1f}% (${top_category.total:.2f}). Consider setting a budget limit for this category.")
        else:
            insights.append(f"📊 Your top spending category is {top_category.name} with ${top_category.total:.2f} ({top_percentage:.1f}% of total spending).")
        
        # Daily average insight
        avg_daily = total_spent / 30
        insights.append(f"💰 Your average daily spending is ${avg_daily:.2f}. Setting a daily budget of ${avg_daily * 0.9:.2f} could help you save 10% more.")
        
        # Transaction frequency insight
        total_transactions = sum(exp.count for exp in expenses)
        avg_per_transaction = total_spent / total_transactions if total_transactions > 0 else 0
        insights.append(f"🛒 You made {total_transactions} transactions with an average of ${avg_per_transaction:.2f} each. Track smaller purchases to avoid impulse spending.")
        
        # Category diversity insight
        if len(expenses) >= 3:
            insights.append(f"📈 You're tracking {len(expenses)} expense categories - great for understanding your spending patterns!")
        
        return insights[:4]  # Return top 4 insights
        
    except Exception as e:
        return [f"Unable to generate expense insights at the moment. Your data is being tracked."]

def get_habit_insights(user_id):
    """Generate insights for habit patterns"""
    try:
        # Get habit completion data for the last 30 days
        thirty_days_ago = date.today() - timedelta(days=30)
        active_habits = Habit.query.filter_by(user_id=user_id, is_active=True).all()
        
        if not active_habits:
            return ["Start creating habits to see your progress insights here"]
        
        insights = []
        
        # Analyze each habit's performance
        high_performers = []
        needs_improvement = []
        
        for habit in active_habits:
            completed_entries = HabitEntry.query.filter(
                HabitEntry.habit_id == habit.id,
                HabitEntry.date >= thirty_days_ago,
                HabitEntry.completed == True
            ).count()
            
            total_possible = 30  # days
            completion_rate = (completed_entries / total_possible) * 100
            current_streak = habit.get_current_streak()
            
            if completion_rate >= 70:
                high_performers.append((habit.name, completion_rate, current_streak))
            elif completion_rate < 30:
                needs_improvement.append((habit.name, completion_rate))
        
        # Generate insights based on performance
        if high_performers:
            best_habit = max(high_performers, key=lambda x: x[1])
            insights.append(f"🌟 Excellent work on '{best_habit[0]}' with {best_habit[1]:.1f}% completion rate! Your current streak is {best_habit[2]} days.")
        
        if needs_improvement:
            struggling_habit = min(needs_improvement, key=lambda x: x[1])
            insights.append(f"💪 '{struggling_habit[0]}' needs attention at {struggling_habit[1]:.1f}% completion. Try setting a smaller daily goal or reminder.")
        
        # Overall habit tracking insight
        total_habits = len(active_habits)
        if total_habits == 1:
            insights.append("🎯 You're focused on building one strong habit - consistency is key to success!")
        elif total_habits <= 3:
            insights.append(f"✅ Tracking {total_habits} habits is a great balance. Focus on consistency over quantity.")
        else:
            insights.append(f"📊 You're tracking {total_habits} habits. Consider focusing on your top 3 priorities for better results.")
        
        # Streak motivation
        max_streak = max([habit.get_current_streak() for habit in active_habits], default=0)
        if max_streak >= 7:
            insights.append(f"🔥 Amazing! Your longest current streak is {max_streak} days. Keep the momentum going!")
        elif max_streak >= 3:
            insights.append(f"📈 You're building momentum with a {max_streak}-day streak. Each day gets easier!")
        
        return insights[:4]  # Return top 4 insights
        
    except Exception as e:
        return ["Your habit tracking is working great! Keep logging your daily progress."]

def get_personalized_recommendations():
    """Generate personalized recommendations based on both expense and habit data"""
    if not client:
        return ["Personalized recommendations unavailable - OpenAI API key not configured"]
    
    try:
        expense_insights = get_expense_insights()
        habit_insights = get_habit_insights()
        
        # Combine insights for a holistic recommendation
        combined_prompt = f"""
        Based on the following financial and habit insights, provide 2-3 holistic recommendations 
        that connect financial health with habit formation:
        
        Expense insights: {expense_insights[:2]}  # Limit to first 2 insights
        Habit insights: {habit_insights[:2]}      # Limit to first 2 insights
        
        Provide recommendations in JSON format:
        {{
            "recommendations": [
                {{
                    "title": "Short recommendation title",
                    "description": "Detailed recommendation connecting finance and habits"
                }}
            ]
        }}
        """
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a life coach specializing in the connection between financial wellness and habit formation."
                },
                {
                    "role": "user",
                    "content": combined_prompt
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=400
        )
        
        result = json.loads(response.choices[0].message.content)
        return [f"{rec['title']}: {rec['description']}" for rec in result.get('recommendations', [])]
        
    except Exception as e:
        return [f"Error generating personalized recommendations: {str(e)}"]
