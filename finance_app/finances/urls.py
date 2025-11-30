
from django.urls import path
from . import views

app_name = 'finances'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('edit/<int:pk>/', views.edit_transaction, name='edit_transaction'),
    path('delete/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    path('set_budget/', views.set_budget, name='set_budget'),
    path('export_csv/', views.export_csv, name='export_csv'),
    path('recurring/create/', views.create_recurring_income, name='create_recurring_income'),
    path('weekly_report/', views.weekly_report, name='weekly_report'),
]
