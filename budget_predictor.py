# expense_app/ml_utils/budget_predictor.py

import pandas as pd
from sklearn.linear_model import LinearRegression
from django.db.models import Sum
from tracker.models import Expense
import datetime


def get_monthly_expenses():
    # Aggregate expenses by month
    expenses = (
        Expense.objects.values('date')
        .annotate(total=Sum('amount'))
        .order_by('date')
    )

    monthly_data = {}
    for item in expenses:
        date = item['date']
        month = date.strftime('%Y-%m')
        monthly_data.setdefault(month, 0)
        monthly_data[month] += float(item['total'])

    # Convert to DataFrame
    df = pd.DataFrame(list(monthly_data.items()), columns=["month", "total"])
    df["month"] = pd.to_datetime(df["month"])
    df.sort_values("month", inplace=True)
    df["month_num"] = range(1, len(df) + 1)  # e.g., Jan=1, Feb=2

    return df


def predict_next_month_budget():
    df = get_monthly_expenses()

    if len(df) < 2:
        return "Not enough data to make prediction."

    # Train linear regression model
    X = df[["month_num"]]
    y = df["total"]

    model = LinearRegression()
    model.fit(X, y)

    next_month_num = df["month_num"].max() + 1
    predicted_budget = model.predict([[next_month_num]])[0]

    return round(predicted_budget, 2)
