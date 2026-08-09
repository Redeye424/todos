import csv
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from datetime import datetime, date, timedelta
import pandas as pd
from django.contrib.auth.views import LoginView
from ollama import Client
from .models import ChatMessage
from plyer import notification
from webpush import send_user_notification
import json
from .forms import SignUpForm
from .models import Profile, PushSubscription
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from webpush.models import PushInformation
from django.http import FileResponse
from webpush.models import PushInformation, SubscriptionInfo
from django.utils import timezone
from .scheduler import titles_and_bodies
import httpx
import django.http

def service_worker(request):
    response = FileResponse(
        open(settings.BASE_DIR / "todo1/static/todo1/service-worker.js", "rb"),
        content_type="application/javascript",
    )
    response["Service-Worker-Allowed"] = "/"
    return response

@login_required
def save_webpush(request):

    if request.method != "POST":
        return JsonResponse({
            "error": "POST required"
        }, status=400)

    try:
        data = json.loads(request.body)

        endpoint = data["endpoint"]
        auth = data["keys"]["auth"]
        p256dh = data["keys"]["p256dh"]

        subscription, created = SubscriptionInfo.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                "auth": auth,
                "p256dh": p256dh,
            }
        )

        PushInformation.objects.get_or_create(
            user=request.user,
            subscription=subscription,
            defaults={
                "group": None,
            }
        )

        return JsonResponse({
            "success": True
        })

    except (KeyError, json.JSONDecodeError) as e:

        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=400)

def send_todo_notification(user, head, body):
    send_user_notification(
        user=user,
        payload={
            "head": head,
            "body": body,
            "icon": "/static/todo1/icons/icon-192.png",
        },
        ttl=3600
    )

fieldnames = [
    "title",
    "description",
    "urgency",
    "due_date_check",
    "due_date",
    "repeat_check",
    "repeat",
    "day_of_week",
    "time",
    "when_made",
    "done"
]


def user_csv_path(User):
    safe_name = f'user_{User.id}.csv'
    return settings.USER_CSV_DIR / safe_name


def create_user_csv(User):
    settings.USER_CSV_DIR.mkdir(parents=True, exist_ok=True)
    path = user_csv_path(User)
    if not path.exists():
        with path.open('w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['title', 'description', 'urgency', 'due_date_check', 'due_date', 'repeat_check', 'repeat', 'day_of_week', 'time', 'when_made', 'done'])

class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    extra_context = {
        "active_page": "accounts"
    }

def signup(request):

    if request.method == "POST":

        form = SignUpForm(request.POST)

        if form.is_valid():

            user = form.save()

            create_user_csv(user)

            login(request, user)

            return redirect("make_todo")

        else:
            print("FORM ERRORS:")
            print(form.errors)

    else:
        form = SignUpForm()


    return render(
        request,
        "registration/signup.html",
        {
            "form": form,
            "active_page": "accounts"
        }
    )



def home(request):
    todos = []
    user = request.user
    
    if user.is_authenticated:
        
        
        if request.user.profile.last_online < timezone.now() - timezone.timedelta(hours=24):
            request.user.profile.karma -= 3
            request.user.profile.save(update_fields=["karma"])
        request.user.profile.last_online = timezone.now()
        request.user.profile.save(update_fields=["last_online"])
        create_user_csv(user)
        csv_path = user_csv_path(user)


        with open(csv_path, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            todos = list(reader)

        line_number = request.POST.get("line_number")
        repeat_not_remove = request.POST.get("repeat_not_remove")

        if line_number is not None:
            try:
                line_number = int(line_number)
            except ValueError:
                line_number = None

            if line_number is not None:

                if repeat_not_remove == "True":
                    if 0 <= line_number < len(todos):
                        request.user.profile.karma += int(1)
                        request.user.profile.save(update_fields=["karma"])
                        todos[line_number]["done"] = datetime.now().isoformat()


                        with open(csv_path, "w", newline="", encoding="utf-8") as file:
                            writer = csv.DictWriter(file, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(todos)

                else:
                    if 0 <= line_number < len(todos):
                        todos.pop(line_number)
                        request.user.profile.karma += int(3)
                        request.user.profile.save(update_fields=["karma"])

                        with open(csv_path, "w", newline="", encoding="utf-8") as file:
                            writer = csv.DictWriter(file, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(todos)

                return redirect("home")

        for index, todo in enumerate(todos):
            todo["line_number"] = index

        todays_todos = []

        for todo in todos:

            if todo["due_date_check"] == "True":
                due_date = datetime.strptime(todo["due_date"], "%Y-%m-%d").date()

                if due_date <= date.today():
                    todays_todos.append(todo)
                    continue


            if todo["repeat"] == "everyday":
                done = todo["done"]

                if done == "False":
                    todays_todos.append(todo)

                else:
                    done = datetime.fromisoformat(done)

                    if datetime.now() - done >= timedelta(days=1):
                        todays_todos.append(todo)


            elif todo["day_of_week"] != "False":
                done = todo["done"]

                if done == "False":
                    if date.today().strftime("%A").lower() == todo["day_of_week"]:
                        todays_todos.append(todo)

                else:
                    done = datetime.fromisoformat(done)

                    if (
                        date.today().strftime("%A").lower() == todo["day_of_week"]
                        and datetime.now() - done >= timedelta(days=7)
                    ):
                        todays_todos.append(todo)
    else:
        csv_path = None
        todays_todos = []


    return render(request, "home.html", {
        "csv_path": csv_path,
        "todos": todays_todos,
        "active_page": "home",
        "all_todos": todos,
    })


def accounts(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'logout':
            logout(request)
            print("LOGGED OUT")
            return redirect('home')

    return render(request, 'accounts.html', {
        "active_page": "accounts"
    })

def make_todo(request):
    if request.method == 'POST':
        
        title = request.POST.get('title')
        description = request.POST.get('description')
        urgency = request.POST.get('urgency')
        due_date_check = "due_date_check" in request.POST
        due_date = request.POST.get('due_date')
        if due_date == "":
            due_date = False
        repeat_check = "repeat_check" in request.POST
        repeat = request.POST.get('repeat')
        if repeat == "":
            repeat = False
        day_of_week = request.POST.get('day_of_week')
        if day_of_week == "":
            day_of_week = False
        if repeat == "everyday":
            day_of_week = False
        time = request.POST.get('time')
        when_made = datetime.now()
        done = False
        if due_date_check:
            day_of_week = False
            repeat = False
        
        csv_path = user_csv_path(request.user)
        with csv_path.open('a', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([title, description, urgency, due_date_check, due_date, repeat_check, repeat, day_of_week, time, when_made, done])

        return redirect('home')
    return render(request, 'make_todo.html', {
        "active_page": "home"
    })

def ai(request):
    if not request.user.is_authenticated:
        return redirect("login")

    df_todos = pd.read_csv(user_csv_path(request.user))

    response_to_user = "hello how can I help with your todos today!"
    client = Client(
        host="https://shawnvivobook.tail5fbbe2.ts.net",
                        timeout=10.0,
                        )

    try:
        client.list()
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, ConnectionError):
        return render(request, "ai.html", {
            "active_page": "ai",
            "response": "The AI is offline right now because it is running on a old laptop thank you for trying my ai tho"
        })
    
    if request.method == "POST":
        user_message = request.POST.get("user_message")

        
        if not user_message:
            return render(request, "ai.html", {
                "active_page": "ai",
                "response": "You need to actually say something to Knox 😭"
            })

        ChatMessage.objects.create(
            user=request.user,
            role="user",
            content=user_message
        )

        
        history = ChatMessage.objects.filter(
            user=request.user
        ).order_by("created_at")


        messages = [
            {
                "role": "system",
                "content": (
                    "You are a persuasive ai trying to convice people to do their todos and your name is Knox. "
                    "Your goal is to convince the person to do their todos. "
                    "You will also put at the end of your message what you set their karma to from 0-100 whole numbers 100 being the best like this |kamra_number_here  kamra_number_here will just be a number and that is it and only ever use | for right in front of the Karma number not after it there can only be one | in the message at the end of the message and never in anywhere else also dont put anything after the |karma_number_here btw karma_number_here is just a number nothing more and rember only one |"
                    "You will decide their karma by looking at how many todos they still have to do, if they make excuses that don't line up with what they have said before and base on how their treat you and how they talk about stuff"
                    "also the higher their karma the better you can treat them (50 is the normal score) and vice versia so if their karama is at 0 never tust them and treat them like trash also never tell them that you are giving them are karma score just put |kamra_number_here at the end of the message"
                    "Keep responses short.\n\n"
                    f"User todos:\n{df_todos.to_string(index=False)}"
                    f"User Karma:\n{request.user.profile.karma}"
                    f"This is the notifications that the user is even treat them like this base on their karma score:\n{titles_and_bodies}"
                ),
            }
        ]

        
        for message in history:
            messages.append({
                "role": message.role,
                "content": message.content
            })

        try:
            response = client.chat(
                model="llama3.2",
                messages=messages,
            )
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, ConnectionError):
            return render(request, "ai.html", {
                "active_page": "ai",
                "response": "The AI is offline right now because it is running on a old laptop thank you for trying my ai tho"
            })


        if "|" in response["message"]["content"]:
            response_to_user, karma = response["message"]["content"].split("|", 1)
            try:
                request.user.profile.karma = int(karma)
                request.user.profile.save(update_fields=["karma"])
            except (ValueError, TypeError):
                pass
        else:
            response_to_user = response["message"]["content"]



        ChatMessage.objects.create(
            user=request.user,
            role="assistant",
            content=response_to_user
        )
    history = ChatMessage.objects.filter(
        user=request.user
    ).order_by("-created_at")[:30]

    history = reversed(history)

    return render(request, "ai.html", {
        "active_page": "ai",
        "response": response_to_user,
    })