import discord
from discord.ext import commands
import random
import asyncio
#commands: !test, !rps, !roll, !flip, and !ask

f = open("discord_token") #opens file with one line: token string
token = f.read()


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command(name='test')
async def test(ctx):
    await ctx.send('Test succeeded')

@bot.command(name='rps')
async def rps(ctx, choice="none"):
    choices = ["rock", "paper", "scissors"]
    if choice not in choices:
        await ctx.send("Not a valid choice. Choice rock, paper, or scissors")
        return
    bot_choice = random.choice(choices)
    await ctx.send(f"I choose {bot_choice}")
    if choice == bot_choice:
      await ctx.send("It's a tie!")
    elif choice == 'rock' and bot_choice == 'scissor' or\
     choice == 'scissor' and bot_choice == 'paper' or\
      choice == 'paper' and bot_choice == 'rock':
      await ctx.send('You win!')
    else:
      await ctx.send('I win!')

@bot.command(name='roll')
async def roll(ctx):
    bot_roll = random.randint(1, 6)
    await ctx.send(f"You rolled a {bot_roll}!")

@bot.command(name='flip')
async def flip(ctx, choice="none"):
    choices = ["heads", "tails"]
    bot_flip = random.choice(choices)
    if not choice in choices:
        await ctx.send("That's not a valid choice. Choose heads or tails")
        return
    await ctx.send(f"The coin landed on {bot_flip}!")
    if choice == bot_flip:
        s = "You win!"
    else:
        s = "You lose!"
    await ctx.send(s)

@bot.command(name="ask")
async def _command(ctx):
    global times_used
    await ctx.send("What do you want to ask?")
    prompt_list = ["What is NULL's favorite movie?", "Who is NULL?", "How old is NULL?"]
    person_list = [("John", "Patriots Day", 22), ("Maria", "Blacklight", 3), ("Frank", "The Human Centipide II", 54), ("Lily", "The Two Popes", 11)]
    def check(msg):
        if msg.author != ctx.author:
            return False
        msg = msg.content
        split_msg = msg.split(" ")
        result = False
        for prompt in prompt_list: #goes through each prompt
            split_prompt = prompt.split(" ")
            for i in range(len(split_prompt)): #goes through each word of msg
                if "NULL" in split_prompt[i]: #checks if NULL in word
                    continue #Ignores NULL. Allows output to then explain it cannot find person


                #    non_null = split_prompt[i].replace("NULL", "")
                #    pure_msg = split_msg[i].replace(non_null, "")

                #    answer = False
                #    for person in person_list: #goes through each person, checks if word matches
                #        if pure_msg.lower() == person[0].lower(): #if TRUE, person in word
                #            answer = True
                #            break
                #    if answer == False: #if person not in word, check next prompt
                #        print(split_msg, split_prompt)
                #        break


                try:
                    split_msg[i]
                except IndexError: #if msg too short
                    result = False
                    break
                if split_msg[i].lower() != split_prompt[i].lower(): #checks if user word == prompt word
                    result = False
                    break
                result = True #assigns true if passed all conditions
            if result == True: #not check other prompts
                break

        return result
    try:
        msg = await bot.wait_for("message", check=check)
    except asyncio.TimeoutError:
        await ctx.send("Sorry, you didn't reply in time, or the spelling was wrong!")

    low_msg = msg.content.lower()
    for person in person_list:
        if person[0].lower() in low_msg: #if valid name in msg
            if "movie" in low_msg:
                output = f"{person[0]} likes '{person[1]}'"
                break
            elif "who" in low_msg:
                output = f"{person[0]} is {person[0]}"
                break
            elif "old" in low_msg:
                output = f"{person[0]} is {person[2]} years old"
                break
            else: #if check didn't catch an edge case
                output = "Not sure I got all that. Did you mean something else?"
                break
        else:
            output  = "I don't know that person"
    await ctx.send(output)





bot.run(token)
