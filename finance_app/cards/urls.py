from django.urls import path
from . import views

app_name = 'cards'

urlpatterns = [
    path('save-link/', views.save_link, name='save_link'),
    path("get-access-token/", views.get_access_token, name="get_access_token"),
    path("add_card",views.add_card, name="add_card"),
    path("transactions/card/<uuid:card_id>/page/<int:page>/", views.card_transactions_page, name="card_transactions_page"),
    path('', views.cards_dashboard, name='cards_dashboard'),
]
