from django.urls import path
from . import views
from .views import export_expenses_pdf
from .views import export_expenses_excel
from .views import recent_expenses_view
from django.urls import path
from .views import ai_summary
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # ✅ root path
    path('add-expense/', views.add_expense, name='add_expense'),
    path('add-category/', views.add_category, name='add_category'),
    path('edit-expense/<int:pk>/', views.edit_expense, name='edit_expense'),
    path('delete-expense/<int:pk>/', views.delete_expense, name='delete_expense'),
    path('export/pdf/', export_expenses_pdf, name='export_pdf'),
    path('export/excel/', export_expenses_excel, name='export_excel'),
    path('set-budget/', views.set_budget, name='set_budget'),
    path('recent-expenses/', recent_expenses_view, name='recent_expenses'),
    path('ai-summary/', ai_summary, name='ai_summary'),
    path('predict-budget/', views.predict_budget, name='budget_prediction')


]
