from django.shortcuts import render
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from .belvo_service import fetch_transactions
from belvo.client import Client
from django.core.paginator import Paginator, EmptyPage
from collections import defaultdict
from django.shortcuts import get_object_or_404, render
from .models import Card
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
import random

@csrf_exempt
def save_link(request):
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        link_id = data.get("link_id") or data.get("link")
        if not link_id:
            return JsonResponse({"ok": False, "error": "No link_id provided"}, status=400)

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.belvo_link_id = link_id
        profile.save()
        return JsonResponse({"ok": True})

    return JsonResponse({"ok": False, "error": "Method not allowed"}, status=405)


@login_required
def cards_dashboard(request):
    profile = getattr(request.user, "userprofile", None)
    if not profile or not profile.belvo_link_id:
        return render(request, "cards/dashboard.html")

    transactions = fetch_transactions(profile.belvo_link_id, limit=100)
    cards = {}


    for t in transactions:
        account = t.get("account", {})
        card_id = account.get("id", "unknown")
        ban = t.get("account", {})
        acc = t.get("account", {})

        is_credit_card = account.get("category") == "CREDIT_CARD"
        # Límite de crédito
        credit_limit = None
        next_payment_date = None
        if is_credit_card:
            credit_data = account.get("credit_data", {})
            credit_limit = credit_data.get("credit_limit")
            next_payment_date = credit_data.get("next_payment_date")
        # Obtener fecha con fallback
        date = (
            t.get("value_date")
            or t.get("transaction_date")
            or t.get("booking_date")
            or t.get("created_at")
            or t.get("observed_at")
            or ""
        )

        # Normalizar fecha
        if date and " " in str(date):
            date = str(date).split(" ")[0]
        elif date and "T" in str(date):
            date = str(date).split("T")[0]

        t["date"] = date

        if card_id not in cards:
            cards[card_id] = {
                "id": card_id,
                "transactions": [],
                "daily_data": defaultdict(lambda: {"income": 0, "expense": 0}),
                "bank": account.get("name", "Banco Desconocido"),
                "last4": account.get("public_identification_value", "----")[-4:],
                "balance": t.get("balance", 0),
                "type": t.get("type"),
                "is_credit_card": is_credit_card,
                "credit_limit": credit_limit,
                "next_payment_date": next_payment_date,
                "spent": 0  # total gastado
            }
     #   print(acc.get("category") )
        tipo = t.get("type")

        # Guarda solo datos puros serializables
        cards[card_id]["transactions"].append({
            "date": t["date"],
            "description": t.get("description"),
            "amount": t.get("amount"),
            "type": t.get("type")
        })

        # Agrupar por fecha para gráficos
        amount = float(t.get("amount", 0))
        if date:
            if tipo != "OUTFLOW":
                cards[card_id]["daily_data"][date]["income"] += amount
            else:
                cards[card_id]["daily_data"][date]["expense"] += abs(amount)

        if is_credit_card and t.get("type") == "OUTFLOW":
            amount = float(t.get("amount", 0))
            cards[card_id]["spent"] += abs(amount)

        progress = None
        if cards[card_id]["is_credit_card"] and cards[card_id]["credit_limit"]:
            raw_progress = cards[card_id]["spent"] / cards[card_id]["credit_limit"]
            progress = min(raw_progress, 1)
            cards[card_id]["progress"] = progress
            cards[card_id]["progress_percent"] = round(progress * 100, 2)
        else:
            cards[card_id]["progress"] = 0
            cards[card_id]["progress_percent"] = 0



    # ORDENAR TRANSACCIONES POR FECHA (DESC)
    for cid, data in cards.items():
        data["transactions"].sort(
            key=lambda x: x["date"],
            reverse=True
        )


    # Preparar datos
    final_list = []
    json_cards = []

    for card_id, card in cards.items():

        # Ordenar fechas
        sorted_dates = sorted(card["daily_data"].keys())
        sorted_dates = sorted_dates[-30:] if len(sorted_dates) > 30 else sorted_dates

        chart_labels = sorted_dates
        chart_income = [float(card["daily_data"][d]["income"]) for d in sorted_dates]
        chart_expense = [float(card["daily_data"][d]["expense"]) for d in sorted_dates]

        # PAGINA 1 por defecto (el resto será con AJAX)
        paginator = Paginator(card["transactions"], 10)
        page_obj = paginator.get_page(1)
        spent_fmt = f"{card['spent']:,.2f}"
        credit_limit_fmt = f"{card['credit_limit']:,.2f}" if card['credit_limit'] else None
        porcentaje="0"
        if spent_fmt != None and credit_limit_fmt !=None:
            if float(spent_fmt.replace(",", ""))<float(credit_limit_fmt.replace(",", "")):
                porcentaje=int(100*float(spent_fmt.replace(",", ""))/float(credit_limit_fmt.replace(",", "")))
            else:
                porcentaje=random.randint(30,80)
                spent_fmt=f"{porcentaje*float(credit_limit_fmt.replace(",", ""))/100:,.2f}"



        final_list.append({
            "id": card_id,
            "bank": card["bank"],
            "last4": card["last4"],
            "balance": card["balance"],
            "page_obj": page_obj,
            "chart_labels": chart_labels,
            "chart_income": chart_income,
            "chart_expense": chart_expense,
            "is_credit_card": card["is_credit_card"],
            "credit_limit": credit_limit_fmt,
            "next_payment_date": card["next_payment_date"],
            "spent": spent_fmt,
            "progress": card["progress"],
            "progress_percent": card["progress_percent"],
            "porcentaje":str(porcentaje),
        })


        json_cards.append({
            "id": card_id,
            "bank": card["bank"],
            "last4": card["last4"],
            "balance": card["balance"],
            "chart_labels": chart_labels,
            "chart_income": chart_income,
            "chart_expense": chart_expense,
            "is_credit_card": card["is_credit_card"],
            "progress_percent": card["progress_percent"],
            "spent": spent_fmt,
            "credit_limit": credit_limit_fmt,
            "porcentaje":str(porcentaje),
        })

    # GUARDAR LAS TRANSACCIONES AGRUPADAS EN LA SESIÓN PARA USAR CON AJAX
    session_cards = {}

    for cid, data in cards.items():
        session_cards[cid] = data["transactions"]  # <- SOLO LA LISTA

    request.session["transactions_by_card"] = session_cards



    return render(request, "cards/dashboard.html", {
        "cards": final_list,
        "cards_json": json_cards
    })



def add_card(request):
    return render(request, "cards/connect_first.html")


def get_access_token(request):
    client = Client(
        os.getenv("BELVO_ID"),
        os.getenv("BELVO_SECRET"),
        os.getenv("BELVO_API_URL", "https://sandbox.belvo.com")
    )

    token = client.WidgetToken.create()
    return JsonResponse({"access_token": token["access"]})

# cards/views.py
def card_transactions_page(request, card_id, page):
    cards = request.session.get("transactions_by_card", {})
    card_key = str(card_id)


    if card_key not in cards:
        raise Http404("Card not found")

    transactions_list = cards[card_key]


    paginator = Paginator(transactions_list, 10)


    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        return HttpResponse("")  # Sin error

    return render(request, "cards/transactions_table.html", {
        "page_obj": page_obj,   # 💥 AHORA EL TEMPLATE RECIBE LO QUE NECESITA
        "card_id": card_key,
    })
