import openai
import time
import discord
from discord.ext import commands
import asyncio

openai.api_key = "<fill me>"  # Replace with your key


#discord values
f = open("discord_token_2") #opens file with one line: token string
token = f.read()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


# Create an assistant
def create_assistant():
    assistant = openai.beta.assistants.create(
        name="My Student Assistant",
        instructions="You're a helpful assistant for discord users.",
        model="gpt-4o"  # or 'gpt-4o'

    )
    return assistant.id

assistant_id = create_assistant()
print("Assistant created with ID:", assistant_id)


def create_thread():
    thread = openai.beta.threads.create()
    return thread.id

thread_id = create_thread()
print("🧵 Thread ID:", thread_id)

# Send message and run assistant
def send_message_to_assistant(assistant_id, thread_id, user_message):
    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message
    )

    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    return run.id

# Wait for response
def wait_for_response(thread_id, run_id, sleep_interval=1):
    while True:
        run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status == "completed":
            break
        elif run.status in ["failed", "cancelled", "expired"]:
            raise Exception(f"Run failed with status: {run.status}")
        time.sleep(sleep_interval)

    messages = openai.beta.threads.messages.list(thread_id=thread_id)
    for message in reversed(messages.data):
        if message.role == "assistant":
            return message.content[0].text.value
    return None




@bot.command(name='ai')
async def search(ctx):
    await ctx.send("What do you want to ask the ai?")
    def check(msg):
        if msg.author != ctx.author:
            return False

    try:
        msg = await bot.wait_for("message", check=check)
    except asyncio.TimeoutError:
        await ctx.send("Sorry, you didn't reply in time, or the spelling was wrong!")

    run_id = send_message_to_assistant(assistant_id, thread_id, msg)
    reply = wait_for_response(thread_id, run_id)
    await ctx.send(reply)


bot.run(token)