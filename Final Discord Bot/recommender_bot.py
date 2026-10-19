import discord
from discord.ext import commands
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
from surprise import accuracy
import pandas as pd
import asyncio
import openai
import time

# Ensure your API key is set
openai.api_key = "<fill me>"  # Replace with your key

def get_or_create_assistant_by_name(name: str, model: str = "gpt-4o",
                                    instructions: str = "You are a helpful assistant.") -> str:
    """
    Checks if an assistant with the given name exists.
    If it does, returns the assistant ID.
    If not, creates a new assistant and returns its ID.

    Parameters:
        name (str): Name of the assistant to look for or create.
        model (str): Model to use when creating a new assistant.
        instructions (str): Default instructions for new assistant.

    Returns:
        str: The ID of the found or newly created assistant.
    """
    # Paginate through all assistants
    assistants = []
    first_page = openai.beta.assistants.list(order="desc", limit=100)
    assistants.extend(first_page.data)

    while first_page.has_next_page():
        first_page = first_page.get_next_page()
        assistants.extend(first_page.data)

    # Look for assistant with matching name
    for assistant in assistants:
        if assistant.name == name:
            print(f"Assistant '{name}' found with ID: {assistant.id}")
            return assistant.id

    # If not found, create new assistant
    print(f"Assistant '{name}' not found. Creating a new one...")
    new_assistant = openai.beta.assistants.create(
        name=name,
        instructions=instructions,
        model=model
    )
    print(f"New assistant created with ID: {new_assistant.id}")
    return new_assistant.id

# discord values
f = open("discord_token_2")  # opens file with one line: token string
token = f.read()
intents = discord.Intents.default()
intents.message_content = True
help_command = commands.DefaultHelpCommand(show_parameter_descriptions=False)
bot = commands.Bot(command_prefix='!', intents=intents, help_command=help_command)

global movies_df
movies_df = pd.read_csv("movies.csv")


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')



# !search outputs movies with user's text in title, genre, or id
@bot.command(name='search', brief="Search for movies using keywords, genre, or id")
async def search(ctx, u_type=None, *args):
    """
        Simple search for movies with keywords/numbers in title, genre, or movie_id category.
        Parameters:
        - u_type: Type of search: 'title'/'genre'/'id'
        - args: Keywords (or numbers in case of id)
        Example:
            !search genre Comedy
        """

    search_amount = 20
    args_list = []
    for arg in args:
        args_list.append(arg)

    msg = ' '.join(args_list)
    if u_type == 'title':
        a_type = 'title'
    elif u_type == 'genre':
        a_type = 'genres'
    elif u_type == 'id':
        a_type = 'movieId'
    else:
        await ctx.send("Invalid type. Must be 'title', 'genres', or 'id'")
        return
    result_df = movies_df[movies_df[a_type].astype('str').str.contains(msg)]

    result_list = []
    for index, row in result_df.iterrows():  # iterate over movies that contain user input
        if len(result_list) < search_amount:
            title = row['title'][:-7]
            year = row['title'][-7:]
            if len(row['title']) > 37:
                title = title[:37] + "..."

            result_list.append(f"Title: {title:<40}  ID: {row['movieId']:<6}  Year: {year}")
        else:
            break


    if len(result_list) == 0:  # if no movie found
        results = f"Couldn't find any movie that contained " + msg
    else:
        results = "```" + "\n".join(result_list) + "```"
    await ctx.send(results)
    await ctx.send("Finished program")


# !advanced search to specify genre, year, year range, amount, and contains, as well as sort by either year newest or older, or alphabetize
@bot.command(name='advsearch', brief="Search for movies with advanced functions")
async def advsearch(ctx, *args):
    """
        Advanced search that asks which specifications to use, then asks user for answers on them.
        args specifications include: keywords=False, year=False, genres=False, id=False, sort=False, amount=20
        specifications don't need to be in any order. Do not use spaces around equal sign.
        Parameters:
        -args: Takes in all specifications to ask for.
            + keywords: keywords in the title: will ask for anything
            + year: The year or year range of movie's release: will ask for a year or a year-year format
            + genres: What genres to include: will ask for genres separated by commas and spaces
            + id: Numbers contained in movie's id: will ask for a number with 1-6 digits
            + sort: In what order to show movies: will ask for 'alphabetical' or 'year', 'descending' or 'ascending'
            + amount: How many movies to show: will ask for a number with 1-6 digits
        Example:
            !adv search keywords=True sort=True amount=40
        """
    def check(msg):
        if msg.author != ctx.author:
            return False
        return True

    def check_year(title): #extract year from title
        title_list = title.split(" ")
        year = title_list[-1][1:-1]
        try:
            year = int(year)
        except ValueError:
            return False #return false if cannot extract (doesn't exist)
        if year < 2030:
            return year
        return False #return false if cannot extract (incorrect input)

    def year_sort(titles): #go over titles and return years
        result_list = []
        for t in titles:
            result = check_year(t)
            if result != False:
                result_list.append(result)
            else:
                result_list.append(0) #no year counts as 0
        return pd.Series(result_list)

    args_list = []
    sort_list = ["alphabetical", "year"]
    for arg in args:
        args_list.append(arg)
    condition_dict = {"keywords" : [False, "Input keywords:"],
                      "year" : [False, "Input year or year1-year2"],
                      "genres" : [False, "Input genres (separate by a comma and space)"],
                      "id" : [False, "Input movie id number"],
                      "sort" : [False, "Input sort style ('alphabetical ascending', 'alphabetical descending', 'year ascending', 'year descending')"]}
    amount = 20
    if len(args_list) != 0:
        for arg in args_list:
            for key in condition_dict:
                if arg == str(key+"=True"):
                    condition_dict[key][0] = True
                    break
                elif "amount=" in arg:
                    try:
                        amount = int(arg[7:])
                    except:
                        await ctx.send("couldn't convert arg to amount (integer")


    result_df = movies_df.copy(deep=True)
    sort_type = "None"
    for key,val in condition_dict.items(): #go over each specification
        if val[0] == True: #if specification is asked for
            await ctx.send(val[1])
            try:
                msg = await bot.wait_for("message", check=check) #ask for keywords, year, id, etc
            except asyncio.TimeoutError:
                await ctx.send("Sorry, you didn't reply in time")
                continue
            content = msg.content
            if key == "keywords": #check what the key is, remove movies based on msg
                try:
                    result_df = result_df[result_df["title"].str.contains(content)]
                except:
                    await ctx.send("Can't search title with keywords.\nFinished program")
                    return
            elif key == "year":
                if len(content) == 9:
                    year1 = content[:4]
                    year2 = content[5:]
                elif len(content) == 4:
                    year1 = content
                    year2 = content
                else:
                    await ctx.send("Invalid input for year(s)")
                    continue
                try:
                    year1 = int(year1)
                    year2 = int(year2)
                except ValueError:
                    await ctx.send("Invalid year(s)")
                    continue
                for index, row in result_df.iterrows():
                    drop = True
                    for year in range(year1, year2+1):
                        movie_year = check_year(row['title'])
                        if movie_year == False:
                            continue
                        if movie_year == year:
                            drop = False
                            break
                    if drop == True:
                        result_df = result_df.drop([index])
            elif key == "genres":
                genres_list = content.split(", ")
                for genre in genres_list:
                    result_df = result_df[result_df["genres"].str.contains(genre)]
            elif key == "id":
                try:
                    movie_id = int(content)
                except ValueError:
                    await ctx.send("id is not integer")
                result_df = result_df[result_df["movieId"].astype('str').str.contains(str(movie_id))]
            elif key == "sort": #ask for type of sort
                sort_type = content.split(" ")[0]
                sort_order = content.split(" ")[1]
                if not sort_type in sort_list:
                    condition_dict["sort"][0] = False
                if sort_order == "descending":
                    sort_ascending = False
                else:
                    sort_ascending = True
            if result_df.shape[0] == 1:
                await ctx.send("One movie found! sending...")
                condition_dict["sort"][0] == False
                break
            elif result_df.shape[0] == 0:
                await ctx.send("No movies found.")
                await ctx.send("Finished program")
                return

    if condition_dict["sort"][0] == True: #sort the movies list by title or year
        if sort_type == "alphabetical":
            result_df = result_df.sort_values("title", ascending = sort_ascending)
        elif sort_type == "year":
            result_df = result_df.sort_values("title", ascending=sort_ascending, key=year_sort)

    result_list = []
    for index, row in result_df.iterrows():  # iterate over movies that contain user input
        if len(result_list) < amount:
            title = str(row['title'])
            year = check_year(str(row['title']))
            if year == False:
                year = "N/A"
            if len(str(row['title'])) > 35:
                title = title[:35] + "..."

            result_list.append(f"Title: {title:<38}  ID: {row['movieId']:<6}  Year: {year}")
        else:
            break
    discord_limit = 1950
    results = ""
    if len(result_list) > 0:
        for row in result_list:
            if len(results) + len(row) > discord_limit: #if result is too long, break up result and send current text
                await ctx.send("```" + results + "```")
                results = ""
            results += "\n" + row
    await ctx.send("```" + results + "```")
    await ctx.send("Finished program")



@bot.command(name='rate',brief="Rate the movie out of 5")
async def rate(ctx, *args):  # args = all inputs for movie name + rating
    """
            Let's user rate a movie on a scale of 1.0-5.0
            Parameters:
            - args: Takes name of movie, last element must be rating in integer or float form
            Example:
                !rate Terminator 2: Judgement Day 4.5
            """
    def check(msg): #make sure msg is from original author
        if msg.author != ctx.author:
            return False
        return True

    def rater(ctx, id_list):
        df = pd.read_csv("ratings.csv")[["userId", "movieId", "rating"]]
        print("sent to rater")
        m_id = ' '.join(id_list[:-1])  # id = all values except last
        rating = id_list[-1]  # rating = last value
        try:
            int(m_id)
        except:
            if movies_df["title"].str.contains(m_id, regex=False).any():  # convert movie name to movie id
                correct_row = []
                for index,movie in movies_df.iterrows():
                    if movie["title"][:-7] == m_id or movie["title"] == m_id:
                        correct_row.append(movie)
                if len(correct_row) > 1:
                    return "More than one movie with such name. Please specify year after movie inside parentheses"
                m_id = correct_row[0]["movieId"]

        try:  # check if movie name didn't convert
            m_id = int(m_id)
        except ValueError:
            return "Couldn't add rating, invalid movie name"

        try:  # check if last value is numeric
            rating = int(rating)
        except ValueError:
            try:
                rating = float(rating)
            except ValueError:
                return "Couldn't add rating, invalid rating"

        if int(m_id) in df["movieId"].values:  # check if movie id and rating valid, then add rating to ratings.csv
            if rating >= 1 and rating <= 5:
                user_df = pd.DataFrame(
                    {'userId': [ctx.message.author.id], 'movieId': [m_id], 'rating': [round(rating, 1)]})
                df = pd.concat([df, user_df], ignore_index=True)
                df_cleaned = df.drop_duplicates(subset=df.columns.difference(['rating']), keep="last", ignore_index=True)
                df_cleaned.to_csv('ratings.csv')
                message = "Added successfully!"
            else:
                message = "Couldn't add rating, invalid rating"
        else:
            message = "Couldn't add rating, invalid movie id"
        return message

    id_list = []
    for arg in args:
        id_list.append(arg)
    if len(id_list) == 1 and id_list[0] == "multiple": #loop if msg = multiple
        await ctx.send("Input movie name/movie id and rating, or input 'done' to finish rating")
        while True:
            try:
                msg = await bot.wait_for("message", check=check)
            except asyncio.TimeoutError:
                await ctx.send("Sorry, you didn't reply in time")
                break
            if msg.content == "done":
                break
            msg_list = msg.content.split(" ")
            output = rater(ctx, msg_list)
            await ctx.send(output)
    else:
        msg_list = id_list
        output = rater(ctx,msg_list)
        await ctx.send(output)
    await ctx.send("Finished program")



@bot.command(name='recommend', brief='Recommends 5 movies to user')
async def recommend(ctx, n=5):
    """
                Recommends n amount of movies based on previous user ratings (default 5).
                Parameters:
                - n=5: Amount of movies to recommend
                Example:
                    !recommend 10
                """
    df = pd.read_csv("ratings.csv")[["userId", "movieId", "rating"]]
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(df, reader)
    trainset = data.build_full_trainset()
    algo = SVD()
    algo.fit(trainset)
    user_id = ctx.message.author.id
    user_recommendations = []

    item_ids = df[~df["movieId"].isin(df[df["userId"] == user_id]["movieId"].unique())]["movieId"].unique()  # ¯\_(ツ)_/¯

    for iid in item_ids:
        _, _, _, est, _ = algo.predict(user_id, iid)
        user_recommendations.append((iid, est))

    ordered_recommendations = sorted(user_recommendations, key=lambda x: x[1], reverse=True)

    ordered_recommendations_top_n = ordered_recommendations[:n]
    for result in ordered_recommendations_top_n:
        value_series = movies_df[movies_df['movieId'] == result[0]]['title']
        message = f"Title: {value_series.iloc[0]}, Est. Rating: {round(result[1], 2)}"
        await ctx.send(message)
    await ctx.send("Finished program")


def open_thread(user_id):
    try:
        thread_df = pd.read_csv("threads.csv")
    except:
        thread_df = pd.DataFrame(columns=['user_id', 'thread_id'])
    if not thread_df.empty:
        if thread_df["user_id"].astype(str).str.contains(str(user_id)).any():
            thread_id = thread_df[thread_df["user_id"].astype(str).str.contains(str(user_id))]["thread_id"].iloc[0]
        else:
            thread = openai.beta.threads.create()
            thread_id = thread.id
            user_df = pd.DataFrame( {'user_id': [user_id], 'thread_id': [thread_id]})
            thread_df = pd.concat([thread_df, user_df], ignore_index=True)
            thread_df.to_csv('threads.csv')
    else:
        thread = openai.beta.threads.create()
        thread_id = thread.id
        user_df = pd.DataFrame({'user_id': [user_id], 'thread_id': [thread_id]})
        thread_df = pd.concat([thread_df, user_df], ignore_index=True)
        thread_df.to_csv('threads.csv')
    return thread_id




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

def wait_for_response(thread_id, run_id, sleep_interval=1):
    while True:
        run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status == "completed":
            break
        elif run.status in ["failed", "cancelled", "expired"]:
            raise Exception(f"Run failed with status: {run.status}")
        time.sleep(sleep_interval)

    messages = openai.beta.threads.messages.list(thread_id=thread_id)
    for message in messages.data:
        if message.role == "assistant":
            return message.content[0].text.value
    return None

@bot.command(name='synopsis', brief="Asks OpenAi for a synopsis")
async def synopsis(ctx):
    """
            Sends chat-gpt4o the user's message, outputs a relevant movie description
            Parameters:
                None
            Example:
                !synopsis
            """
    await ctx.send("What do you want to ask the ai?")

    def check(msg):
        if msg.author != ctx.author:
            return False
        return True

    try:
        msg = await bot.wait_for("message", check=check)
    except asyncio.TimeoutError:
        await ctx.send("Sorry, you didn't reply in time, or the spelling was wrong!")
    await ctx.send("Getting thread...")
    thread_id = open_thread(ctx.message.author.id)
    ai_msg = "Your job is to listen to what movie the user is asking of and then provide an a short (3-4 lines) description of the movie. If someone asks anything different than about a movie, ignore and say 'I can only provide assistance finding out information about movies'."
    assistant_id = get_or_create_assistant_by_name(name="Student Assistant #5021", instructions=ai_msg)
    await ctx.send("Getting reply...")
    run_id = send_message_to_assistant(assistant_id, thread_id, msg.content)
    reply = wait_for_response(thread_id, run_id)
    await ctx.send(reply)


@bot.command(name='accuracy', brief="Outputs accuracy of bot")
async def error_count(ctx):  # test algo with newest ratings.csv, then print rmse and mae
    """
                    Prints RMSE and MAE errors of bot's SVD algorithm.
                    Parameters:
                    - none
                    Example:
                        !accuracy
                    """
    df = pd.read_csv("ratings.csv")[["userId", "movieId", "rating"]]
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(df, reader)
    trainset, testset = train_test_split(data, test_size=0.25)
    algo = SVD()
    algo.fit(trainset)
    predictions = algo.test(testset)
    string = f"RMSE: {accuracy.rmse(predictions)} \n MAE: {accuracy.mae(predictions)}"
    await ctx.send(string)
    await ctx.send("Finished program")


bot.run(token)
