from apps.clients.models import Client

def get_client_from_user(user):
    try:
        return Client.objects.get(user=user)
    except Client.DoesNotExist:
        return None