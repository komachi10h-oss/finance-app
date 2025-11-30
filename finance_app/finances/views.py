
from django.shortcuts import render, redirect, get_object_or_404
from .models import Transaction, Category, Budget, RecurringIncome
from .forms import TransactionForm, BudgetForm, RecurringIncomeForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncWeek, TruncMonth
from django.http import HttpResponse
import csv
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, date, timedelta
from django.core.paginator import Paginator
import json

def get_weekly_data(transactions):
    today = date.today()
    start_date = today - timedelta(weeks=4)

    # Filtra solo las transacciones de las últimas 4 semanas
    last_weeks = transactions.filter(date__gte=start_date)

    weekly_labels = []
    weekly_income = []
    weekly_expense = []

    for i in range(4):
        week_start = today - timedelta(weeks=3 - i)
        week_end = week_start + timedelta(days=6)

        # Etiqueta de la semana
        label = f"{week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')}"
        weekly_labels.append(label)

        # Calcular ingresos y gastos por semana
        week_data = last_weeks.filter(date__range=[week_start, week_end])
        income_sum = week_data.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        expense_sum = week_data.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0

        weekly_income.append(float(income_sum))
        weekly_expense.append(float(expense_sum))

    # Si todas las semanas están vacías, mostrar solo una semana
    if all(v == 0 for v in weekly_income + weekly_expense):
        weekly_labels = [today.strftime('%d/%m')]
        weekly_income = [0]
        weekly_expense = [0]

    # Datos por categoría (para el gráfico circular)
    grouped = last_weeks.filter(transaction_type='expense', category__isnull=False).values('category__name').annotate(total=Sum('amount')).order_by('-total')
    categories = [g['category__name'] for g in grouped]
    category_values = [float(g['total']) for g in grouped]

    return {
        'labels': weekly_labels,
        'income': weekly_income,
        'expense': weekly_expense,
        'categories': categories or ['Sin datos'],
        'category_values': category_values or [0],
    }


@login_required
def dashboard(request):
    user = request.user

    # ============================================================
    # CREAR CATEGORÍAS POR DEFECTO (si no existen)
    # ============================================================
    if Category.objects.count() == 0:
        default = [
            "Salario", "Ventas", "Otros ingresos",
            "Alimentación", "Transporte", "Servicios",
            "Salud", "Educación", "Entretenimiento",
            "Otros gastos",
        ]
        for d in default:
            Category.objects.get_or_create(name=d)

    # ============================================================
    # AGREGAR NUEVA TRANSACCIÓN
    # ============================================================
    if request.method == 'POST' and 'add_transaction' in request.POST:
        form = TransactionForm(request.POST)
        if form.is_valid():
            tr = form.save(commit=False)
            tr.user = user
            tr.save()
            check_budget_and_notify(user, tr)
            return redirect('finances:dashboard')
    else:
        form = TransactionForm()

    # ============================================================
    # QUERY BASE PARA TODA LA APP (NO SE FILTRA)
    # ============================================================
    transactions_qs = Transaction.objects.filter(user=user)

    # ============================================================
    # 1) FILTROS — SOLO PARA LA TABLA
    # ============================================================
    category_filter = request.GET.get('category')   # filtro tabla
    type_filter = request.GET.get('type')           # filtro tabla

    table_qs = transactions_qs.order_by('-date')

    if category_filter:
        table_qs = table_qs.filter(category_id=category_filter)

    if type_filter in ['income', 'expense']:
        table_qs = table_qs.filter(transaction_type=type_filter)

    # ============================================================
    # PAGINACIÓN DE LA TABLA
    # ============================================================
    paginator = Paginator(table_qs, 10)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)

    # ============================================================
    # 2) GRÁFICO DE BARRAS — FILTRO INDEPENDIENTE
    # ============================================================
    chart_category = request.GET.get('chart_category')

    transactions_for_chart = transactions_qs  # siempre base sin filtros

    if chart_category:
        transactions_for_chart = transactions_for_chart.filter(category_id=chart_category)

    # Datos del gráfico semanal (SOLO usa transactions_for_chart)
    weekly_data = get_weekly_data(transactions_for_chart)

    # ============================================================
    # 3) GRÁFICO CIRCULAR — NUNCA SE FILTRA
    # ============================================================
    pie_source = transactions_qs  # sin filtros garantizado

    total_income = pie_source.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
    total_expense = pie_source.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
    balance = total_income - total_expense

    # ============================================================
    # FORMULARIOS EXTRA
    # ============================================================
    budget_form = BudgetForm()
    recurring_form = RecurringIncomeForm()

    # ============================================================
    # GRÁFICO CIRCULAR (NO FILTRADO NUNCA)
    # ============================================================
    pie_labels = []
    pie_values = []

    for cat in Category.objects.all():
        total = pie_source.filter(
            category=cat,
            transaction_type="expense"
        ).aggregate(total=Sum("amount"))["total"] or 0

        total = float(total)  # 👈 Convertimos Decimal → float
        if total > 0:
            pie_labels.append(cat.name)
            pie_values.append(total)


    context = {
        'form': form,
        'transactions': transactions,             # tabla filtrada
        'categories': Category.objects.all(),
        'total_income': total_income,            # KPIs NO filtrados
        'total_expense': total_expense,
        'balance': balance,
        'budget_form': budget_form,
        'recurring_form': recurring_form,

        'weekly_data': weekly_data,              # gráfico filtrado independiente

        # Para mantener los selects activos
        'selected_category': category_filter,
        'selected_type': type_filter,
        'selected_chart_category': chart_category,
        "pie_labels": json.dumps(pie_labels),
        "pie_values": json.dumps(pie_values),
    }

    return render(request, 'finances/dashboard.html', context)



@login_required
def edit_transaction(request, pk):
    tr = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=tr)
        if form.is_valid():
            form.save()
            return redirect('finances:dashboard')
    else:
        form = TransactionForm(instance=tr)
    return render(request, 'finances/edit_transaction.html', {'form': form, 'transaction': tr})

@login_required
def delete_transaction(request, pk):
    tr = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        tr.delete()
        return redirect('finances:dashboard')
    return render(request, 'finances/delete_transaction.html', {'transaction': tr})

@login_required
def set_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            cat = form.cleaned_data['category']
            month = form.cleaned_data['month']
            # convert to first day of month
            month_date = date(month.year, month.month, 1)
            amount = form.cleaned_data['amount']
            Budget.objects.update_or_create(user=request.user, category=cat, month=month_date, defaults={'amount': amount})
            return redirect('finances:dashboard')
    return redirect('finances:dashboard')

@login_required
def export_csv(request):
    user = request.user
    qs = Transaction.objects.filter(user=user).order_by('-date')
    # Apply same filters if present
    category_id = request.GET.get('category')
    if category_id:
        qs = qs.filter(category_id=category_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    writer = csv.writer(response)
    writer.writerow(['date','title','amount','transaction_type','category','description'])
    for t in qs:
        writer.writerow([t.date, t.title, t.amount, t.transaction_type, t.category.name if t.category else '', t.description])
    return response

@login_required
def create_recurring_income(request):
    if request.method == 'POST':
        form = RecurringIncomeForm(request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.user = request.user
            rec.save()
            return redirect('finances:dashboard')
    return redirect('finances:dashboard')

def check_budget_and_notify(user, transaction):
    # simple check: find budget for the month and category
    if not transaction.category:
        return
    month_start = date(transaction.date.year, transaction.date.month, 1)
    try:
        budget = Budget.objects.get(user=user, category=transaction.category, month=month_start)
    except Budget.DoesNotExist:
        return
    # sum expenses in that category for the month
    total = Transaction.objects.filter(user=user, category=transaction.category, date__year=transaction.date.year, date__month=transaction.date.month, transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
    if total > budget.amount:
        # send email (if configured)
        if settings.EMAIL_HOST:
            send_mail(
                subject="Presupuesto Excedido",
                message=f"Has excedido el presupuesto para {transaction.category.name}. Presupuesto: {budget.amount}. Gastado: {total}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

@login_required
def weekly_report(request):
    user = request.user
    today = date.today()
    start = today - timedelta(weeks=4)
    qs = Transaction.objects.filter(user=user, date__date__gte=start)
    # build CSV-like response or render template
    return render(request, 'finances/weekly_report.html', {'data': qs})

