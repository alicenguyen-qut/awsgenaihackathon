"""Nutrition analytics calculations"""
from datetime import timedelta
from utils.helpers import now_aest

CALORIE_GOALS = {
    'weight_loss': 1500,
    'lose weight': 1500,
    'weight-loss': 1500,
    'maintain': 2000,
    'maintain weight': 2000,
    'maintenance': 2000,
    'muscle gain': 2500,
    'build muscle': 2500,
    'gain muscle': 2500,
    'muscle-gain': 2500,
    'heart-health': 1800,
    'energy-boost': 2200,
}
DEFAULT_CALORIE_GOAL = 2000

def get_calorie_goal(health_goal: str) -> int:
    if not health_goal:
        return DEFAULT_CALORIE_GOAL
    return CALORIE_GOALS.get(health_goal.lower(), DEFAULT_CALORIE_GOAL)

def calculate_nutrition_stats(logs, date, health_goal: str = ''):
    """Calculate nutrition stats for a specific date"""
    date_logs = [l for l in logs if l['date'] == date]
    
    total = {
        'calories': sum(l['calories'] for l in date_logs),
        'protein': sum(l['protein'] for l in date_logs),
        'carbs': sum(l['carbs'] for l in date_logs),
        'fats': sum(l['fats'] for l in date_logs)
    }
    calorie_goal = get_calorie_goal(health_goal)
    remaining = max(0, calorie_goal - total['calories'])
    return {
        'stats': total,
        'meal_count': len(date_logs),
        'calorie_goal': calorie_goal,
        'calories_remaining': remaining
    }

def calculate_period_analytics(logs, period):
    """Calculate analytics for a time period"""
    if period == 'today':
        today = now_aest().strftime('%Y-%m-%d')
        period_logs = [l for l in logs if l['date'] == today]
    elif period == 'week':
        week_ago = (now_aest() - timedelta(days=7)).strftime('%Y-%m-%d')
        period_logs = [l for l in logs if l['date'] >= week_ago]
    elif period == 'month':
        month_ago = (now_aest() - timedelta(days=30)).strftime('%Y-%m-%d')
        period_logs = [l for l in logs if l['date'] >= month_ago]
    else:  # year
        year_ago = (now_aest() - timedelta(days=365)).strftime('%Y-%m-%d')
        period_logs = [l for l in logs if l['date'] >= year_ago]
    
    if not period_logs:
        return {
            'analytics': {'avgCalories': 0, 'avgProtein': 0, 'totalDays': 0, 'bestDay': 0},
            'insights': []
        }
    
    total_cal = sum(l['calories'] for l in period_logs)
    total_protein = sum(l['protein'] for l in period_logs)
    unique_days = len(set(l['date'] for l in period_logs))
    best_day = max((sum(l['calories'] for l in logs if l['date'] == date) 
                    for date in set(l['date'] for l in period_logs)), default=0)
    
    analytics = {
        'avgCalories': total_cal / unique_days if unique_days > 0 else 0,
        'avgProtein': total_protein / unique_days if unique_days > 0 else 0,
        'totalDays': unique_days,
        'bestDay': best_day
    }
    
    most_common_meal = max(set(l['meal_type'] for l in period_logs), 
                           key=lambda x: sum(1 for l in period_logs if l['meal_type'] == x)) if period_logs else 'None'
    
    insights = [
        f"You've logged meals for {unique_days} days",
        f"Average daily intake: {int(analytics['avgCalories'])} calories",
        f"Most common meal type: {most_common_meal}"
    ]

    # Per-day summary for frontend drill-down
    day_logs = sorted([
        {
            'date': date,
            'calories': sum(l['calories'] for l in period_logs if l['date'] == date),
            'meal_count': sum(1 for l in period_logs if l['date'] == date)
        }
        for date in set(l['date'] for l in period_logs)
    ], key=lambda x: x['date'], reverse=True)
    
    return {'analytics': analytics, 'insights': insights, 'day_logs': day_logs}

def update_streak(streaks):
    """Update login streak data"""
    today = now_aest().strftime('%Y-%m-%d')
    last = streaks.get('last_login')
    
    if last != today:
        if last == (now_aest() - timedelta(days=1)).strftime('%Y-%m-%d'):
            streaks['current'] += 1
        else:
            streaks['current'] = 1
        streaks['longest'] = max(streaks['current'], streaks.get('longest', 0))
        streaks['last_login'] = today
        return True
    return False
