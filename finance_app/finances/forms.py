
from django import forms
from .models import Transaction, Category, RecurringIncome
from django.utils import timezone
from decimal import Decimal

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title','amount','transaction_type','date','category','description']
        widgets = {
            'date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'  # 👈 formato ISO requerido por HTML
            ),
            'amount': forms.NumberInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class':'form-control','rows':2}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= Decimal('0.00'):
            raise forms.ValidationError("El monto debe ser un número positivo.")
        return amount

class BudgetForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    month = forms.DateField(widget=forms.DateInput(attrs={'type':'month'}))
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

class RecurringIncomeForm(forms.ModelForm):
    class Meta:
        model = RecurringIncome
        fields = ['title','amount','category','frequency','next_date','active']
        widgets = {
            'next_date': forms.DateInput(attrs={'type':'date'}),
        }
