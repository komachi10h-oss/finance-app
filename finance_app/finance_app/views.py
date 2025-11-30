from django.shortcuts import redirect

def home_redirect(request):
    return redirect('users/login')  # Redirige a la vista con nombre "users"
