import random
from django.contrib.auth.models import User
from django.utils import timezone
from webpush import send_user_notification
from apscheduler.schedulers.background import BackgroundScheduler
import csv
from datetime import datetime
from django.conf import settings

def send_scheduled_todo_notifications():
    now = timezone.localtime()

    current_time = now.strftime("%H:%M")
    today = now.date()

    for user in User.objects.all():

        csv_path = settings.USER_CSV_DIR / f"user_{user.id}.csv"

        if not csv_path.exists():
            continue

        try:
            with csv_path.open(
                newline="",
                encoding="utf-8"
            ) as file:
                todos = list(csv.DictReader(file))
        except Exception:
            continue

        for todo in todos:

            todo_time = todo.get("time", "").strip()

            if not todo_time:
                continue

            # Only run at the todo's exact time
            if todo_time != current_time:
                continue

            # Don't notify completed todos
            if todo.get("done") not in ("False", "", None):
                continue

            # Check whether this todo should occur today
            should_notify = False

            # -------------------------
            # DUE DATE
            # -------------------------

            if (
                todo.get("due_date_check") == "True"
                and todo.get("due_date") not in ("", "False", None)
            ):
                try:
                    due_date = datetime.strptime(
                        todo["due_date"],
                        "%Y-%m-%d"
                    ).date()

                    should_notify = due_date == today

                except ValueError:
                    continue

            # -------------------------
            # EVERY DAY
            # -------------------------

            elif todo.get("repeat") == "everyday":
                should_notify = True

            # -------------------------
            # WEEKLY
            # -------------------------

            elif todo.get("repeat") == "weekly":

                should_notify = (
                    todo.get("day_of_week", "").lower()
                    == today.strftime("%A").lower()
                )

            # -------------------------
            # MONTHLY
            # -------------------------

            elif todo.get("repeat") == "monthly":

                should_notify = (
                    todo.get("day_of_month", "") == str(today.day)
                )

            # -------------------------
            # YEARLY
            # -------------------------

            elif todo.get("repeat") == "yearly":

                should_notify = (
                    todo.get("yearly_day", "") == str(today.day)
                    and
                    todo.get("yearly_month", "") == str(today.month)
                )

            if not should_notify:
                continue

            # -------------------------
            # SEND NOTIFICATION
            # -------------------------

            send_user_notification(
                user=user,
                payload={
                    "head": f"Todo: {todo.get('title', 'Todo')}",
                    "body": todo.get(
                        "description",
                        "You have a todo to do!"
                    ),
                    "icon": "/static/todo1/icons/icon-192.png",
                },
                ttl=3600
            )

def emoji_to_icon(emoji):
    codepoints = "-".join(
        f"{ord(char):x}" for char in emoji
        if char != "\ufe0f"
    )

    return f"https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/{codepoints}.png"

a0to9_titles = [
    "Rotten Gremlin",
    "Absolutely Feral",
    "Emergency Goblin Alert",
    "You Again?",
]

a0to9_bodies = [
    "Your todo list has unionized against you.",
    "I'm stealing every left sock in your house until you finish a task.",
    "Your fridge is being audited by raccoons. This could've been avoided.",
    "The dust on your todo list just paid rent.",
]

a0to9_emojis = [
    "🗑️",
    "🦝",
    "🚨",
    "😭",
]

a10to19_titles = [
    "Barely Alive",
    "Suspicious Activity",
    "Almost a Person",
    "Progress... Sort Of",
]

a10to19_bodies = [
    "Do one task before your houseplants start judging you.",
    "You're improving. The fridge has been granted a temporary pardon.",
    "Momentum is trying to find you. Open the door.",
    "Future you keeps calling. They're disappointed.",
]

a10to19_emojis = [
    "🌱",
    "👀",
    "👍",
    "😐",
]

a20to29_titles = [
    "Signs of Intelligence",
    "Not Bad...",
    "Hope Detected",
    "You're Cooking",
]

a20to29_bodies = [
    "One more task and we'll pretend the past never happened.",
    "You're officially harder to roast.",
    "Keep going before the procrastination gremlins regroup.",
    "This is looking surprisingly respectable.",
]

a20to29_emojis = [
    "🧠",
    "😅",
    "✨",
    "🍳",
]

a30to39_titles = [
    "Respect Earned",
    "Locked In",
    "Actually Productive",
    "Looking Sharp",
]

a30to39_bodies = [
    "Your todo list is beginning to fear you.",
    "You're building momentum. Don't waste it.",
    "Keep stacking wins.",
    "Today's looking pretty good.",
]

a30to39_emojis = [
    "😎",
    "🎯",
    "✅",
    "✨",
]

a40to49_titles = [
    "Almost There",
    "So Close",
    "One Last Push",
    "Momentum Max",
]

a40to49_bodies = [
    "A few more tasks and today's a victory.",
    "Don't let the streak escape.",
    "You're doing great. Finish strong.",
    "Keep the engine running.",
]

a40to49_emojis = [
    "🚀",
    "👏",
    "💪",
    "⚡",
]

a50to59_titles = [
    "Perfectly Balanced",
    "The Middle Path",
    "Neutral Energy",
    "Halfway Hero",
]

a50to59_bodies = [
    "Neither chaos nor greatness. Just vibes.",
    "You're standing perfectly in the middle. That's oddly impressive.",
    "This is the calm before the productivity storm.",
    "A balanced day is still a good day.",
]

a50to59_emojis = [
    "⚖️",
    "😌",
    "🧘",
    "🦸",
]

a60to69_titles = [
    "On Fire",
    "Momentum Unlocked",
    "You're Rolling",
    "Crushing It",
]

a60to69_bodies = [
    "Keep the streak alive.",
    "You're making productivity look easy.",
    "Every task is another victory.",
    "Don't stop now.",
]

a60to69_emojis = [
    "🔥",
    "⚡",
    "🚂",
    "💥",
]

a70to79_titles = [
    "Elite Mode",
    "Machine Status",
    "Unstoppable",
    "Locked In",
]

a70to79_bodies = [
    "Your todo list is running out of places to hide.",
    "This is what consistency looks like.",
    "You're setting a serious pace.",
    "Keep the momentum alive.",
]

a70to79_emojis = [
    "⭐",
    "🤖",
    "💪",
    "🎯",
]

a80to89_titles = [
    "Legend Status",
    "Peak Human",
    "Checklist Destroyer",
    "Master Class",
]

a80to89_bodies = [
    "Tasks disappear when you look at them.",
    "Your consistency is inspiring.",
    "Keep showing that todo list who's boss.",
    "This pace is incredible.",
]

a80to89_emojis = [
    "👑",
    "🌟",
    "✔️",
    "🎓",
]

a90to99_titles = [
    "Living Legend",
    "Almost Mythical",
    "Built Different",
    "GOAT Energy",
]

a90to99_bodies = [
    "The finish line is waving at you.",
    "Your productivity should be studied.",
    "You're making discipline look effortless.",
    "One final push.",
]

a90to99_emojis = [
    "🏆",
    "✨",
    "💯",
    "🐐",
]

over100_titles = [
    "The.. The.. Solo Exception",
    "The Chosen One",
    "Ascended Being",
    "Hall of Fame",
]

over100_bodies = [
    "Your todo list bows before you.",
    "Legends are written about days like this.",
    "Are you the strongest because you do your todos or do you do your todos because you're the strongest?",
    "Even procrastination is afraid of you.",
]

over100_emojis = [
    "😇",
    "👑",
    "🌌",
    "🏆",
]

titles_and_bodies = [[a0to9_titles, a0to9_bodies], [a10to19_titles, a10to19_bodies], [a20to29_titles, a20to29_bodies], [a30to39_titles, a30to39_bodies], [a40to49_titles, a40to49_bodies], [a50to59_titles, a50to59_bodies], [a60to69_titles, a60to69_bodies], [a70to79_titles, a70to79_bodies], [a80to89_titles, a80to89_bodies], [a90to99_titles, a90to99_bodies], [over100_titles, over100_bodies]]


def send_random_notifications():
    now = timezone.localtime()
    if not (7 <= now.hour < 20 or (now.hour == 20 and now.minute <= 30)):
        return

    for user in User.objects.all():
        if random.randint(1, 10) != 1:
        #if False:
            continue
        karma = user.profile.karma

        if 0 <= karma <= 9:
            head = random.choice(a0to9_titles)
            body = random.choice(a0to9_bodies)
            emoji = random.choice(a0to9_emojis)

        elif 10 <= karma <= 19:
            head = random.choice(a10to19_titles)
            body = random.choice(a10to19_bodies)
            emoji = random.choice(a10to19_emojis)

        elif 20 <= karma <= 29:
            head = random.choice(a20to29_titles)
            body = random.choice(a20to29_bodies)
            emoji = random.choice(a20to29_emojis)

        elif 30 <= karma <= 39:
            head = random.choice(a30to39_titles)
            body = random.choice(a30to39_bodies)
            emoji = random.choice(a30to39_emojis)

        elif 40 <= karma <= 49:
            head = random.choice(a40to49_titles)
            body = random.choice(a40to49_bodies)
            emoji = random.choice(a40to49_emojis)

        elif 50 <= karma <= 59:
            head = random.choice(a50to59_titles)
            body = random.choice(a50to59_bodies)
            emoji = random.choice(a50to59_emojis)

        elif 60 <= karma <= 69:
            head = random.choice(a60to69_titles)
            body = random.choice(a60to69_bodies)
            emoji = random.choice(a60to69_emojis)

        elif 70 <= karma <= 79:
            head = random.choice(a70to79_titles)
            body = random.choice(a70to79_bodies)
            emoji = random.choice(a70to79_emojis)

        elif 80 <= karma <= 89:
            head = random.choice(a80to89_titles)
            body = random.choice(a80to89_bodies)
            emoji = random.choice(a80to89_emojis)

        elif 90 <= karma <= 99:
            head = random.choice(a90to99_titles)
            body = random.choice(a90to99_bodies)
            emoji = random.choice(a90to99_emojis)

        else:
            head = random.choice(over100_titles)
            body = random.choice(over100_bodies)
            emoji = random.choice(over100_emojis)

        send_user_notification(
            user=user,
            payload={
                "head": head,
                "body": body,
                "icon": "/static/todo1/icons/icon-192.png",
                "image": emoji_to_icon(emoji),
            },
            ttl=3600
        )

def start_scheduler():
    scheduler = BackgroundScheduler()

    scheduler.add_job(
        send_random_notifications,
        "interval",
        minutes=15
    )

    scheduler.add_job(
        send_scheduled_todo_notifications,
        "interval",
        minutes=1,
        id="scheduled_todo_notifications",
        replace_existing=True,
    )

    scheduler.start()