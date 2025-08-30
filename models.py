from django.db import models



class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='subcategories', on_delete=models.CASCADE)

    def __str__(self):
        return self.name if not self.parent else f"{self.parent.name} → {self.name}"


class Expense(models.Model):
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return f"{self.title} - ₨{self.amount}"

class MonthlyBudget(models.Model):
    month = models.CharField(max_length=7)  # e.g. "2025-06"
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.month} - PKR {self.amount}"
