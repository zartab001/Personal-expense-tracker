from django.shortcuts import render, redirect, get_object_or_404
from .models import Expense, Category
from .forms import ExpenseForm, CategoryForm
import plotly.graph_objs as go
import plotly.offline as opy
from django.db.models import Sum
from django.db.models.functions import TruncDay
from django.db.models import Q
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
import csv
from .models import MonthlyBudget
from .forms import MonthlyBudgetForm
from django.utils import timezone
from django.utils.timezone import now
from django.db.models import Sum
from .models import Expense, MonthlyBudget, Category
from datetime import datetime, timedelta, date  
from django.shortcuts import render, redirect
from calendar import month_name
from collections import Counter
from django.shortcuts import render
from expense_project.ML_Utils.budget_predictor import predict_next_month_budget
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from .models import Expense
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date





from django.contrib import messages  # Add this import at the top

def dashboard(request):
    query = request.GET.get('q')
    category_filter = request.GET.get('category')
    selected_month = request.GET.get('month')

    today = now().date()
    current_year = today.year
    current_month = today.replace(day=1)

    # Show all months from Jan to Dec
    months = [date(current_year, m, 1) for m in range(1, 13)]

    if selected_month:
        try:
            month = int(selected_month)
            filter_date = date(current_year, month, 1)
        except ValueError:
            filter_date = current_month
    else:
        filter_date = current_month

    expenses = Expense.objects.filter(date__year=filter_date.year, date__month=filter_date.month)

    if query:
        expenses = expenses.filter(title__icontains=query)
    if category_filter and category_filter != "All":
        expenses = expenses.filter(category__name=category_filter)

    total_spent = sum(exp.amount for exp in expenses)

    budget = MonthlyBudget.objects.filter(month=filter_date.strftime('%Y-%m')).first()
    if budget:
        budget_amount = budget.amount
    else:
        budget_amount = 0

    remaining_balance = budget_amount - total_spent



    # Chart setup
    chart_div = ""
    line_chart_div = ""

    if expenses.exists():
        category_totals = {}
        for exp in expenses:
            if exp.category:
                cat_name = exp.category.name
                category_totals[cat_name] = category_totals.get(cat_name, 0) + exp.amount

        if category_totals:
            pie_trace = go.Pie(labels=list(category_totals.keys()), values=list(category_totals.values()), hole=0.4)
            pie_layout = go.Layout(
                height=300,
                margin=dict(t=40, b=40, l=40, r=40),
                paper_bgcolor='#1e1e2f',
                plot_bgcolor='#1e1e2f',
                font=dict(color='white'),
                legend=dict(font=dict(size=12))
            )
            pie_fig = go.Figure(data=[pie_trace], layout=pie_layout)
            chart_div = opy.plot(pie_fig, auto_open=False, output_type='div', config={'responsive': True})
        else:
            chart_div = "<div class='no-chart'>No category data yet</div>"

        daily_totals = expenses.annotate(day=TruncDay('date')).values('day').annotate(total=Sum('amount')).order_by('day')
        line_x = [entry['day'].strftime('%Y-%m-%d') for entry in daily_totals]
        line_y = [float(entry['total']) for entry in daily_totals]

        if line_x and line_y:
            line_trace = go.Scatter(
                x=line_x,
                y=line_y,
                mode='lines',
                name='Expenses',
                line=dict(color='rgba(255,100,100,1)', width=2),
                fill='tozeroy',
                fillcolor='rgba(255,100,100,0.2)',
                hoverinfo='x+y',
            )
            max_income_y = [max(line_y) * 1.2 for _ in line_x]
            income_trace = go.Scatter(
                x=line_x,
                y=max_income_y,
                mode='lines',
                name='Max Income',
                line=dict(color='rgba(0,255,180,1)', width=2, dash='dot'),
                hoverinfo='skip'
            )
            line_layout = go.Layout(
                title=dict(text='Income & Expenses', font=dict(color='white', size=18), x=0.05),
                xaxis=dict(title='', showgrid=False, color='white', tickfont=dict(size=10)),
                yaxis=dict(title='', showgrid=False, color='white', tickfont=dict(size=10)),
                height=300,
                paper_bgcolor='#131735',
                plot_bgcolor='#131735',
                font=dict(color='white'),
                margin=dict(t=50, b=40, l=40, r=30),
                legend=dict(orientation='h', yanchor='bottom', y=1.05, xanchor='right', x=1),
            )
            line_fig = go.Figure(data=[line_trace, income_trace], layout=line_layout)
            line_chart_div = opy.plot(line_fig, auto_open=False, output_type='div', config={'responsive': True})
        else:
            line_chart_div = "<div class='no-chart'>No trend data yet</div>"
    else:
        chart_div = "<div class='no-chart'>No expenses to display</div>"
        line_chart_div = "<div class='no-chart'>No trend data yet</div>"

    categories = Category.objects.all()

    return render(request, 'tracker/dashboard.html', {
        'expenses': expenses,
        'total_spent': total_spent,
        'remaining_balance': remaining_balance,
        'budget_amount': budget_amount,
        'chart_div': chart_div,
        'line_chart_div': line_chart_div,
        'categories': categories,
        'months': months,
        'selected_month': selected_month,
    })
    
    
def ai_summary(request):
    today = timezone.now()
    month_str = today.strftime('%Y-%m')  # e.g., '2025-07'

    # Fetch expenses for current month
    monthly_expenses = Expense.objects.filter(date__year=today.year, date__month=today.month)
    total_expense = sum(exp.amount for exp in monthly_expenses)

    # Get top category
    category_counts = Counter(exp.category.name for exp in monthly_expenses)
    top_categories = category_counts.most_common(2)  # Top 2 categories

    # Get budget for the month
    try:
        budget = MonthlyBudget.objects.get(month=month_str).amount
        remaining = budget - total_expense
    except MonthlyBudget.DoesNotExist:
        budget = None
        remaining = None

    # Prepare summary text
    summary = f"In {month_str}, you spent a total of ₨{total_expense:.2f}. "
    if top_categories:
        summary += f"Most of your expenses were in the '{top_categories[0][0]}' category"
        if len(top_categories) > 1:
            summary += f", followed by '{top_categories[1][0]}'. "
        else:
            summary += ". "
    if budget:
        if remaining > 0:
            summary += f"You are under budget by ₨{remaining:.2f}. Good job!"
        elif remaining < 0:
            summary += f"You exceeded your budget by ₨{abs(remaining):.2f}. Try to manage better next month!"
        else:
            summary += "You've exactly matched your budget. Nice balance!"

    return render(request, 'tracker/ai_summary.html', {'ai_summary': summary})

def predict_budget(request):
    # Get expenses and group by month
    expenses = Expense.objects.all().order_by('date')
    if not expenses:
        return render(request, 'tracker/budget_prediction.html', {'prediction': "No data available"})

    df = pd.DataFrame.from_records(expenses.values('amount', 'date'))
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    monthly = df.groupby('month')[['amount']].sum().reset_index()
    monthly['month'] = monthly['month'].astype(str)

    # Create numeric month index
    monthly['month_index'] = np.arange(len(monthly))

    model = LinearRegression()
    model.fit(monthly[['month_index']], monthly['amount'])

    next_index = [[len(monthly)]]
    predicted = model.predict(next_index)[0]
    predicted = round(predicted, 2)

    return render(request, 'tracker/budget_prediction.html', {'prediction': predicted})

def set_budget(request):
    if request.method == 'POST':
        form = MonthlyBudgetForm(request.POST)
        if form.is_valid():
            # Get raw month string like "2025-08"
            month_str = form.cleaned_data['month']

            # Ensure only year-month format is stored
            try:
                # Remove any trailing day (if added by browser)
                month_only = month_str[:7]
            except:
                month_only = month_str

            amount = form.cleaned_data['amount']

            # Save or update the MonthlyBudget
            budget, created = MonthlyBudget.objects.get_or_create(
                month=month_only,
                defaults={'amount': amount}
            )
            if not created:
                budget.amount = amount
                budget.save()

            return redirect('dashboard')  # Or wherever you want
    else:
        form = MonthlyBudgetForm()

    return render(request, 'tracker/set_budget.html', {'form': form})



def recent_expenses_view(request):
    categories = Category.objects.all()
    expenses = Expense.objects.all().order_by('-date')[:10]  # Optional: recent 10

    context = {
        "expenses": expenses,
        "categories": categories,
    }
    return render(request, 'tracker/recent_expenses.html', context)

def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm()
    return render(request, 'tracker/add_expense.html', {'form': form})


def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = CategoryForm()
    return render(request, 'tracker/add_category.html', {'form': form})


def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'tracker/edit_expense.html', {'form': form})


def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        return redirect('dashboard')
    return render(request, 'tracker/delete_expense.html', {'expense': expense})


def export_expenses_pdf(request):
    expenses = Expense.objects.all()
    total_spent = sum(exp.amount for exp in expenses)

    template = get_template('tracker/export_pdf.html')
    html = template.render({'expenses': expenses, 'total_spent': total_spent})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="expenses_report.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('PDF generation failed', status=500)

    return response


def export_expenses_excel(request):
    expenses = Expense.objects.all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Title', 'Amount', 'Category'])

    for exp in expenses:
        writer.writerow([exp.date, exp.title, exp.amount, exp.category.name])

    return response