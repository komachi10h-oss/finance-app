import os
from belvo.client import Client
from django.conf import settings

def get_belvo_client():
    return Client(
        os.getenv("BELVO_ID") or settings.BELVO_ID,
        os.getenv("BELVO_SECRET") or settings.BELVO_SECRET,
        os.getenv("BELVO_API_URL") or getattr(settings, "BELVO_API_URL", "https://sandbox.belvo.com"),
    )


def create_link_if_none(client, institution="sandbox_mx_retail"):
    links = list(client.Links.list())
    if not links:
        link = client.Links.create(
            institution=institution,
            username="full",
            password="full",
            token=None
        )
    else:
        link = links[0]
    # Asegura que sea dict
    if isinstance(link, list):
        link = link[0]
    return link.get("id")

def fetch_transactions(link_id, limit=100):
    client = get_belvo_client()
    # Forzar creación/descarga de transacciones (sandbox suele usar create)
    try:
        # Dependiendo de la versión del SDK podría ser client.Transactions.create(...)
        # o otro método; intenta create() primero
        client.Transactions.create(link=link_id)
    except Exception:
        # si create() no existe o falla, ignorar y seguir con list()
        pass

    transactions = list(client.Transactions.list(link=link_id, limit=limit))
    return transactions

