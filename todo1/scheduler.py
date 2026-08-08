import random
from django.contrib.auth.models import User
from django.utils import timezone
from webpush import send_user_notification
from apscheduler.schedulers.background import BackgroundScheduler

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
                "icon": emoji_to_icon(emoji),
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

    scheduler.start()