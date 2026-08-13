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
from webpush import send_user_notification
import json
from .forms import SignUpForm
from .models import Profile, PushSubscription, Todo
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
import calendar
from django.http import HttpResponse
from django.contrib import messages


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
    "day_of_month",
    "yearly_day",
    "yearly_month",
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
            writer.writerow(['title', 'description', 'urgency', 'due_date_check', 'due_date', 'repeat_check', 'repeat', 'day_of_week',"day_of_month", "yearly_day", "yearly_month", 'time', 'when_made', 'done'])

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
    todays_todos = []
    calendar_todos = {}
    month_calendar = []
    month_name = ""
    csv_path = None

    user = request.user

    if user.is_authenticated:

        if request.user.profile.last_online < timezone.now() - timezone.timedelta(hours=24):
            request.user.profile.karma -= 3
            request.user.profile.save(update_fields=["karma"])

        request.user.profile.last_online = timezone.now()
        request.user.profile.save(update_fields=["last_online"])

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

                        request.user.profile.karma += 1
                        request.user.profile.save(update_fields=["karma"])

                        todos[line_number]["done"] = datetime.now().isoformat()

                        with open(csv_path, "w", newline="", encoding="utf-8") as file:
                            writer = csv.DictWriter(
                                file,
                                fieldnames=fieldnames
                            )
                            writer.writeheader()
                            writer.writerows(todos)

                else:

                    if 0 <= line_number < len(todos):

                        todos.pop(line_number)

                        request.user.profile.karma += 3
                        request.user.profile.save(update_fields=["karma"])

                        with open(csv_path, "w", newline="", encoding="utf-8") as file:
                            writer = csv.DictWriter(
                                file,
                                fieldnames=fieldnames
                            )
                            writer.writeheader()
                            writer.writerows(todos)

                return redirect("home")

        for index, todo in enumerate(todos):
            todo["line_number"] = index

        today = date.today()

        for todo in todos:

            if (
                todo["due_date_check"] == "True"
                and todo["due_date"] != "False"
                and todo["due_date"] != ""
            ):

                due_date = datetime.strptime(
                    todo["due_date"],
                    "%Y-%m-%d"
                ).date()

                if due_date <= today:
                    todays_todos.append(todo)

                continue

            if todo["repeat"] == "everyday":

                done = todo["done"]

                if done == "False" or done == "":
                    todays_todos.append(todo)

                else:
                    try:
                        done_date = datetime.fromisoformat(done).date()

                        if done_date < today:
                            todays_todos.append(todo)

                    except ValueError:
                        todays_todos.append(todo)


            elif todo["repeat"] == "weekly":

                if todo["day_of_week"] == today.strftime("%A").lower():

                    done = todo["done"]

                    if done == "False" or done == "":
                        todays_todos.append(todo)

                    else:
                        try:
                            done_date = datetime.fromisoformat(done).date()

                            if done_date < today:
                                todays_todos.append(todo)

                        except ValueError:
                            todays_todos.append(todo)

            elif todo["repeat"] == "monthly":

                if todo["day_of_month"] == str(today.day):

                    done = todo["done"]

                    if done == "False" or done == "":
                        todays_todos.append(todo)

                    else:
                        try:
                            done_date = datetime.fromisoformat(done).date()

                            if done_date < today:
                                todays_todos.append(todo)

                        except ValueError:
                            todays_todos.append(todo)

            elif todo["repeat"] == "yearly":

                if (
                    todo["yearly_day"] == str(today.day)
                    and
                    todo["yearly_month"] == str(today.month)
                ):

                    done = todo["done"]

                    if done == "False" or done == "":
                        todays_todos.append(todo)

                    else:
                        try:
                            done_date = datetime.fromisoformat(done).date()

                            if done_date < today:
                                todays_todos.append(todo)

                        except ValueError:
                            todays_todos.append(todo)

        if todays_todos:
            urgency_order = {
                "high": 0,
                "medium": 1,
                "low": 2,
            }

            todays_todos.sort(
                key=lambda todo: urgency_order.get(todo["urgency"], 99)
            )
        if todos:
            urgency_order = {
                "high": 0,
                "medium": 1,
                "low": 2,
            }

            todos.sort(
                key=lambda todo: (
                    todo["due_date"],
                    urgency_order.get(todo["urgency"], 99)
                )
            )
        month_name = today.strftime("%B")
        for todo in todos:

            if (
                todo["due_date_check"] == "True"
                and todo["due_date"] != "False"
                and todo["due_date"] != ""
            ):

                due_date = datetime.strptime(
                    todo["due_date"],
                    "%Y-%m-%d"
                ).date()

                if (
                    due_date.year == today.year
                    and due_date.month == today.month
                ):
                    calendar_todos.setdefault(
                        due_date.day,
                        []
                    ).append(todo)

            if todo["repeat"] == "everyday":

                for day in range(
                    1,
                    calendar.monthrange(
                        today.year,
                        today.month
                    )[1] + 1
                ):

                    calendar_todos.setdefault(
                        day,
                        []
                    ).append(todo)

            elif todo["repeat"] == "weekly":

                wanted_day = todo["day_of_week"]

                for day in range(
                    1,
                    calendar.monthrange(
                        today.year,
                        today.month
                    )[1] + 1
                ):

                    current_date = date(
                        today.year,
                        today.month,
                        day
                    )

                    if current_date.strftime("%A").lower() == wanted_day:

                        calendar_todos.setdefault(
                            day,
                            []
                        ).append(todo)

            elif todo["repeat"] == "monthly":

                if todo["day_of_month"] != "False":

                    day = int(todo["day_of_month"])

                    if day <= calendar.monthrange(
                        today.year,
                        today.month
                    )[1]:

                        calendar_todos.setdefault(
                            day,
                            []
                        ).append(todo)

            elif todo["repeat"] == "yearly":

                if (
                    todo["yearly_day"] != "False"
                    and
                    todo["yearly_month"] != "False"
                ):

                    yearly_day = int(todo["yearly_day"])
                    yearly_month = int(todo["yearly_month"])

                    if (
                        yearly_month == today.month
                        and
                        yearly_day <= calendar.monthrange(
                            today.year,
                            today.month
                        )[1]
                    ):

                        calendar_todos.setdefault(
                            yearly_day,
                            []
                        ).append(todo)

        raw_calendar = calendar.Calendar(
            firstweekday=6
        ).monthdayscalendar(
            today.year,
            today.month
        )

        month_calendar = []

        for week in raw_calendar:

            calendar_week = []

            for day in week:

                if day == 0:

                    calendar_week.append({
                        "day": 0,
                        "todos": []
                    })

                else:

                    calendar_week.append({
                        "day": day,
                        "todos": calendar_todos.get(day, [])
                    })

            month_calendar.append(calendar_week)

    else:
        csv_path = None
        todays_todos = []
        todos = []
        calendar_todos = {}
        month_calendar = []
        month_name = ""

    return render(request, "home.html", {
        "csv_path": csv_path,
        "todos": todays_todos,
        "active_page": "home",
        "all_todos": todos,
        "month_calendar": month_calendar,
        "calendar_todos": calendar_todos,
        "month_name": month_name,
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
        day_of_month = request.POST.get('day_of_month')
        yearly_day = request.POST.get('yearly_day')
        yearly_month = request.POST.get('month')
        if day_of_week == "":
            day_of_week = False
        if day_of_month == "":
            day_of_month = False
        if yearly_day == "":
            yearly_day = False
        if yearly_month == "":
            yearly_month = False
        if repeat == "everyday":
            day_of_week = False
            day_of_month = False
            yearly_day = False
            yearly_month = False
        elif repeat == "weekly":
            day_of_month = False
            yearly_day = False
            yearly_month = False
        elif repeat == "monthly":
            day_of_week = False
            yearly_day = False
            yearly_month = False
        elif repeat == "yearly":
            day_of_week = False
            day_of_month = False
        time = request.POST.get('time')
        when_made = datetime.now()
        done = False
        if due_date_check:
            repeat_check = False
            repeat = False
            day_of_week = False
            day_of_month = False
            yearly_day = False
            yearly_month = False
        
        csv_path = user_csv_path(request.user)
        with csv_path.open('a', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([title, description, urgency, due_date_check, due_date, repeat_check, repeat, day_of_week, day_of_month, yearly_day, yearly_month, time, when_made, done])

        return redirect('home')
    return render(request, 'make_todo.html', {
        "active_page": "home"
    })

def ai(request):
    if not request.user.is_authenticated:
        return redirect("login")
    create_user_csv(request.user)
    df_todos = pd.read_csv(user_csv_path(request.user))

    response_to_user = "hello how can I help with your todos today!"
    
    if request.method == "POST":

        client = Client(
            host="http://shawnvivobook.tail5fbbe2.ts.net:11434",
                            timeout=10.0,
                            )

        try:
            client.list()
        except (httpx.ProxyError, httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, ConnectionError):
            return render(request, "ai.html", {
                "active_page": "ai",
                "response": "Knox is offline right now because it is running on my old laptop checkout about Knox for more info!"
            })

        user_message = request.POST.get("user_message")

        
        if not user_message:
            return render(request, "ai.html", {
                "active_page": "ai",
                "response": "hello how can I help with your todos today!"
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

def about_us(request):
    return render(request, "about_us.html", {
        "active_page": "about_us",
    })

@login_required
def export_todos(request):
    csv_path = user_csv_path(request.user)

    if not csv_path.exists():
        create_user_csv(request.user)

    with open(csv_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        todos = list(reader)

    response = HttpResponse(
        json.dumps(todos, indent=4),
        content_type="application/json"
    )

    response["Content-Disposition"] = 'attachment; filename="todos.json"'

    return response

@login_required
def import_todos(request):

    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect("accounts")

    uploaded_file = request.FILES.get("todo_file")

    if not uploaded_file:
        messages.error(request, "Please choose a JSON file first.")
        return redirect("accounts")

    try:
        data = json.load(uploaded_file)

        if not isinstance(data, list):
            raise ValueError("Invalid todo format")

        csv_path = user_csv_path(request.user)

        create_user_csv(request.user)

        with open(csv_path, "a", newline="", encoding="utf-8") as csv_file:

            writer = csv.writer(csv_file)

            for item in data:

                writer.writerow([
                    item.get("title", ""),
                    item.get("description", ""),
                    item.get("urgency", ""),
                    item.get("due_date_check", "False"),
                    item.get("due_date", "False"),
                    item.get("repeat_check", "False"),
                    item.get("repeat", "False"),
                    item.get("day_of_week", "False"),
                    item.get("day_of_month", "False"),
                    item.get("yearly_day", "False"),
                    item.get("yearly_month", "False"),
                    item.get("time", ""),
                    item.get("when_made", ""),
                    item.get("done", "False"),
                ])

        messages.success(request, "Todos imported successfully!")

    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        messages.error(request, "That file is not a valid Todos JSON file.")

    return redirect("accounts")