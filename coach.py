import random
import time
import schedule
from datetime import datetime
from twilio.rest import Client
from anthropic import Anthropic

TWILIO_SID = "AC4846cb5a6cc4348d1ce9312da4b26a11"
TWILIO_AUTH = "0010adc0b17487ce30c89ab20bf260d8"
TWILIO_FROM = "+12524216506"
MY_NUMBER = "+17207853370"

twilio = Client(TWILIO_SID, TWILIO_AUTH)
claude = Anthropic()

TASKS = {
    "dealership": [
        "Walk the dealership floor and check everything looks good",
        "Dust the showroom",
        "Wipe down helmets",
        "Organize gear display",
        "Make product information cards",
        "Clear out old clearance stock",
        "Practice 10-key typing",
        "Fix the service door",
        "Fix the shop door",
        "Fix the lights",
        "Update product listings",
        "Respond to online inquiries",
        "Request customer reviews",
        "Organize your contact list",
        "Log any follow-ups needed",
        "Learn about a new product line",
        "Watch a manufacturer video",
        "Study fitment for top selling parts",
        "Study upgrade paths for popular bikes",
        "Check stock on fast moving items",
        "Flag items that need reordering",
        "Put together a bundle deal idea",
        "Post a product photo on social media",
        "Share a deal or new arrival online",
        "Reply to comments and messages",
        "Post a short video of a cool accessory",
    ],
    "home": [
        "Work on the 26 inch 2-stroke gas bike build",
        "Work on the 29 inch 2-stroke gas bike build",
        "Work on the 4-stroke 89cc bike build",
        "Research tires for the 1970 VW Bug",
        "Order the battery for the VW Bug",
        "Order clear coat for the VW Bug",
        "Work on your 3D stars project",
        "Research construction management programs",
        "Request your official transcripts for school",
        "Work on your college application",
        "Draft your personal statement for school",
        "Research auction sites with APIs for your scanner",
        "Sketch out how your auction alert system should work",
        "Work on building your auction scanner",
        "Set up price alert thresholds for your scanner",
    ]
}

conversation_history = []

def get_time_context():
    hour = datetime.now().hour
    if 9 <= hour < 18:
        return "dealership"
    return "home"

def pick_task():
    context = get_time_context()
    return random.choice(TASKS[context])

def send_text(message):
    twilio.messages.create(
        body=message,
        from_=TWILIO_FROM,
        to=MY_NUMBER
    )
    print(f"Sent: {message}")

def get_coaching_message(task, context):
    conversation_history.append({
        "role": "user",
        "content": f"Generate a short, energetic, encouraging text message (2-3 sentences max) assigning this task: '{task}'. Context: it is {'work hours at the dealership' if context == 'dealership' else 'after work hours at home'}. Be casual, motivating, and real. End with telling them to reply DONE when finished or SKIP for a different task. No emojis."
    })

    response = claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=150,
        system="You are a no-nonsense personal coach texting your friend throughout the day to keep them productive and moving. Keep messages short, real, and encouraging. Never use emojis. Always end by telling them to reply DONE when finished or SKIP for a different task.",
        messages=conversation_history
    )

    message = response.content[0].text
    conversation_history.append({
        "role": "assistant",
        "content": message
    })
    return message

def get_water_reminder():
    hour = datetime.now().hour
    messages = [
        "You walked in the door - grab your first bottle of water right now. Drink water, stay sharp.",
        "Bottle number 2. Get up, walk to the water, drink it. Do it now.",
        "Water check - you should be on bottle 3. Go get it. While you are up, take a quick walk around the dealership.",
        "Last water of the workday. Bottle 4. Drink it before you leave. You know the drill.",
    ]
    if hour < 11:
        return messages[0]
    elif hour < 13:
        return messages[1]
    elif hour < 15:
        return messages[2]
    else:
        return messages[3]

def send_task_reminder():
    now = datetime.now()
    hour = now.hour
    if hour < 7 or hour >= 23:
        return
    context = get_time_context()
    task = pick_task()
    message = get_coaching_message(task, context)
    send_text(message)

def send_water_reminder():
    now = datetime.now()
    hour = now.hour
    if 9 <= hour <= 17:
        send_text(get_water_reminder())

def handle_reply(reply_text):
    reply = reply_text.strip().upper()
    if reply == "DONE":
        responses = [
            "That is what I am talking about. Keep that energy going. Next task coming up.",
            "Done already? Let us go. Stay on it.",
            "Knocked it out. That is how you do it. Stand by for your next one.",
        ]
        send_text(random.choice(responses))
        time.sleep(3)
        send_task_reminder()
    elif reply == "SKIP":
        send_text("No problem. Here is something else for you.")
        time.sleep(2)
        send_task_reminder()
    else:
        conversation_history.append({
            "role": "user",
            "content": reply_text
        })
        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            system="You are a no-nonsense personal coach texting your friend to keep them productive. Keep replies short and real. Never use emojis.",
            messages=conversation_history
        )
        reply_message = response.content[0].text
        conversation_history.append({
            "role": "assistant",
            "content": reply_message
        })
        send_text(reply_message)

schedule.every(90).minutes.do(send_task_reminder)
schedule.every().day.at("09:00").do(send_water_reminder)
schedule.every().day.at("11:15").do(send_water_reminder)
schedule.every().day.at("13:30").do(send_water_reminder)
schedule.every().day.at("15:45").do(send_water_reminder)

if __name__ == "__main__":
    print("Coach is running! Sending first message...")
    send_task_reminder()
    while True:
        schedule.run_pending()
        time.sleep(60)
