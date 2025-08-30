from django import forms
from .models import Expense
from .models import Category
from .models import MonthlyBudget
from datetime import date

class MonthlyBudgetForm(forms.ModelForm):
    class Meta:
        model = MonthlyBudget
        fields = ['month', 'amount']
        widgets = {
            'month': forms.TextInput(attrs={'type': 'month'}),
        }

    def clean_month(self):
        month_str = self.data.get('month')
        if not month_str:
            raise forms.ValidationError("Month is required.")
        if len(month_str) != 7 or '-' not in month_str:
            raise forms.ValidationError("Enter a valid month in YYYY-MM format.")
        return month_str  # e.g. "2025-08"




class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }
        

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'parent']  # Include parent

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].required = False
        self.fields['parent'].label = "Parent Category (optional)"
