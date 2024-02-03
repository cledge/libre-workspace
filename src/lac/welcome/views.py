from django.shortcuts import render, redirect
import os
import subprocess
from django.conf import settings


# List of subdomains
subdomains = ["cloud", "office", "portal", "la", "chat", "meet", "element", "matrix"]

# Create your views here.
def welcome_start(request):
    # If request is POST
    message = ""
    if request.method == "POST":
        password = request.POST["password"]
        password_repeat = request.POST["password_repeat"]
        if password.strip() == "":
            message = "Passwort darf nicht leer sein."
        if password.count(" ") > 0:
            message = "Passwort darf keine Leerzeichen enthalten."
        # Check if password contains at least one number
        if not any(char.isdigit() for char in password):
            message = "Passwort muss mindestens eine Zahl enthalten."
        # Check if password contains at least one letter
        if not any(char.isalpha() for char in password):
            message = "Passwort muss mindestens einen Buchstaben enthalten."
        # Check if password contains at least one special character
        special_characters = "!\"%&'()*+,-./:;<=>?@[\]^_`{|}~"
        if not any(char in special_characters for char in password):
            message = "Passwort muss mindestens ein Sonderzeichen enthalten."
        # If password contains "$'# it is forbidden
        forbidden_characters = "$'#"
        if any(char in forbidden_characters for char in password):
            message = "Passwort darf keine der folgenden Zeichen enthalten: $'#"
        # Check if password is at least 8 characters long
        if len(password) < 8:
            message = "Passwort muss mindestens 8 Zeichen lang sein."
        if password == password_repeat:
            request.session["password"] = password
        else:
            message = "Passwörter stimmen nicht überein. Bitte versuchen Sie es erneut."
        if message == "":
            return redirect("welcome_select_apps")

    return render(request, "welcome/welcome_start.html", {"message": message, "hide_login_button": True})


def welcome_select_apps(request):
    if request.method == "POST":
        request.session["nextcloud"] = request.POST.get("nextcloud", "")
        if request.POST.get("online_office", "") == "onlyoffice":
            request.session["onlyoffice"] = "onlyoffice"
            request.session["collabora"] = ""
        elif request.POST.get("online_office", "") == "collabora":
            request.session["collabora"] = "collabora"
            request.session["onlyoffice"] = ""
        else:
            request.session["onlyoffice"] = ""
            request.session["collabora"] = ""
        request.session["rocketchat"] = request.POST.get("rocketchat", "")
        request.session["matrix"] = request.POST.get("matrix", "")
        request.session["jitsi"] = request.POST.get("jitsi", "")
        return redirect("welcome_dns_settings")

    return render(request, "welcome/welcome_select_apps.html", {"hide_login_button": True})


def welcome_dns_settings(request):
    message = ""
    if request.method == "POST":
        request.session["visibility"] = request.POST.get("visibility", "")
        request.session["domain"] = request.POST.get("domain", "")
        if request.session["visibility"] == "public":
            if request.session["domain"] == "":
                message = "Bitte geben Sie eine Domain an."
            elif request.session["domain"].count(".") != 1:
                message = "Bitte stellen Sie sicher, dass Sie nur die Domain angeben und keine Subdomain."
        else:
            request.session["domain"] = "int.de"
        if message == "":
            return redirect("installation_running")
    return render(request, "welcome/welcome_dns_settings.html", {"message": message, "subdomains": subdomains, "hide_login_button": True})


def installation_running(request):
    message = ""
    os.environ["DOMAIN"] = request.session["domain"]
    os.environ["ADMIN_PASSWORD"] = request.session["password"]
    # Get output of script: in lac/unix/unix_scripts/get_ip.sh
    os.environ["IP"] = os.popen("hostname -I").read().split(" ")[0]
    # Run basics script
    os.environ["NEXTCLOUD"] = request.session["nextcloud"]
    os.environ["ONLYOFFICE"] = request.session["onlyoffice"]
    os.environ["COLLABORA"] = request.session["collabora"]
    os.environ["ROCKETCHAT"] = request.session["rocketchat"]
    os.environ["MATRIX"] = request.session["matrix"]
    os.environ["JITSI"] = request.session["jitsi"]

    # Create env.sh file
    with open("/usr/share/linux-arbeitsplatz/unix/unix_scripts/env.sh", "w") as f:
        f.write(f"export DOMAIN={os.environ['DOMAIN']}\n")
        f.write(f"export IP={os.environ['IP']}\n")
        f.write(f"export ADMIN_PASSWORD={os.environ['ADMIN_PASSWORD']}\n")

    # Run installation script
    # if file /usr/share/linux-arbeitsplatz/unix/unix_scripts/installation_running exists
    if not os.path.isfile("/usr/share/linux-arbeitsplatz/unix/unix_scripts/installation_running"):
        if os.path.isfile("/usr/share/linux-arbeitsplatz/unix/unix_scripts/install.sh"):
            subprocess.Popen(["/usr/bin/bash", "/usr/share/linux-arbeitsplatz/unix/unix_scripts/install.sh"], cwd="/usr/share/linux-arbeitsplatz/unix/unix_scripts/" )
        else:
            print("WARNING: Installation script not found! If you are in a development environment, thats okay. If you are in a production environment, please check your installation.")
            message = "WARNING: Installation script not found! If you are in a development environment, thats okay. If you are in a production environment, please check your installation."
    
    if not "cert" in subdomains:
        subdomains.append("cert")

    variables = {
        "message": message, 
        "subdomains": subdomains, 
        "domain": os.environ["DOMAIN"],
        "ip": os.environ["IP"],
        "hide_login_button": True,
    }

    # Create rendered access_rendered.html
    with open(f'{settings.BASE_DIR}/welcome/templates/welcome/access_rendered.html', 'w') as f:
        string = render(request, "welcome/access.html", variables).content.decode("utf-8")
        string = "{% extends \"lac/base.html\" %}\n{% block content %}\n" + string + "\n{% endblock %}"
        f.write(string)

    variables["installation_running"] = True
    return render(request, "welcome/installation_running.html", variables)


def access(request):
    return render(request, "welcome/access_rendered.html", {"hide_login_button": True})
