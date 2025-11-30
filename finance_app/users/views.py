from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth import login
from .forms import CustomUserCreationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth import get_user_model
from .forms import CustomAuthenticationForm
import random
from .forms import CustomAuthenticationForm, OTPForm
from django.core.mail import send_mail

User = get_user_model()
def users(request):
  template = loader.get_template('login.html')
  return HttpResponse(template.render())


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect("users")  
    else:
        form = CustomUserCreationForm()
    return render(request, "users/register.html", {"form": form})




class CustomLoginView(LoginView):
    template_name = "users/login.html"
    authentication_form = CustomAuthenticationForm

    def form_valid(self, form):
        """Este método se ejecuta cuando email+password son correctos"""

        # Obtener usuario validado
        user = form.get_user()

        # Generar OTP
        otp = random.randint(100000, 999999)

        # Guardarlo en la sesión
        self.request.session["pending_user_id"] = user.id
        self.request.session["otp"] = otp

        # Enviar correo
        send_mail(
            "Tu código de verificación",
            f"Tu código es: {otp}",
            None,
            [user.email],
        )
        print(otp)
        # Redirigir al usuario a ingresar el OTP
        return redirect("users:verify_otp")
    
def verify_otp(request):
    if "pending_user_id" not in request.session:
        return redirect("users:login")

    if request.method == "POST":
        form = OTPForm(request.POST)
        if form.is_valid():
            user_input = form.cleaned_data["otp"]
            session_otp = str(request.session.get("otp"))
            user_id = request.session.get("pending_user_id")

            if user_input == session_otp:
                user = User.objects.get(id=user_id)

                # Login final
                login(request, user)

                # Limpiar sesión
                del request.session["otp"]
                del request.session["pending_user_id"]

                return redirect("finances:dashboard")  # Cambia a tu vista principal

            form.add_error("otp", "Código incorrecto")
    else:
        form = OTPForm()

    return render(request, "users/verify_otp.html", {"form": form})

