from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import EmailForm, PasswordForm, RegisterForm
from .models import User
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from operations.services.event_service import log_event
from operations.constants import EventType

def enter_email(request):
    form = EmailForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"].lower()

        # Check if user exists
        if User.objects.filter(email=email).exists():
            return redirect(f"/accounts/enter-password/?email={email}")
        else:
            return redirect(f"/accounts/register/?email={email}")

    return render(request, "accounts/enter_email.html", {"form": form})


def enter_password(request):
    email = request.GET.get("email")
    if not email:
        return redirect("enter_email")

    form = PasswordForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        password = form.cleaned_data["password"]
        user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)
            if user.role == 'tenant':
                return redirect('/dashboard/tenant/')
            elif user.role == 'landlord':
                return redirect('/dashboard/landlord/')
            elif user.role == 'agent':
                return redirect('/dashboard/agent/')
            elif user.role == 'admin':
                return redirect('/dashboard/admin/') # dashboard or home

        messages.error(request, "Invalid password")

    return render(request, "accounts/enter_password.html", {
        "email": email,
        "form": form
    })


def register(request):
    email_from_query = request.GET.get("email")
    form = RegisterForm(initial={"email": email_from_query})

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = User.objects.create_user(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                name=form.cleaned_data["name"],
            )

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            current_site = get_current_site(request)
            verification_link = f"http://{current_site.domain}/accounts/verify-email/{uid}/{token}/"

            send_mail(
                subject="Verify your QuestNest account",
                message=f"Click the link to verify: {verification_link}",
                from_email="no-reply@questnest.com",
                recipient_list=[user.email],
            )

            messages.success(request, "Account created. Please verify your email.")

            return redirect("enter_email")

    return render(request, "accounts/register.html", {"form": form})


def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_object_or_404(User, pk=uid)
    except:
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save()
        return redirect('enter_email')  # Or a "verified" page
    else:
        return render(request, 'accounts/verification_failed.html')


@login_required
def user_update(request):
    user = request.user

    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():

            old_values = {
                "name": user.name,
                "email": user.email,
            }

            updated_user = form.save()

            changes = {}
            for field, old_value in old_values.items():
                new_value = getattr(updated_user, field)
                if old_value != new_value:
                    changes[field] = {
                        "old": old_value,
                        "new": new_value
                    }

            if changes:
                log_event(
                    organisation=request.organisation,
                    actor=request.user,
                    event_type=EventType.USER_UPDATED,
                    object_type="User",
                    object_id=str(updated_user.id),
                    metadata={"changes": changes}
                )

            return redirect("dashboard")

    else:
        form = UserUpdateForm(instance=user)

    return render(request, "accounts/user_update.html", {"form": form})
