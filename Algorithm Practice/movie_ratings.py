import pandas as pd
import random


# To practice with creating DataFrames, create a Movie Ratings matrix:

# Generate a movie DataFrame array to represent ratings given by users to a set of movies.
# Assume there are 5 users and 5 movies.
# Ratings should be integers from 1 to 5, where 1 is the lowest and 5 is the highest rating.
# If you are feeling bold, use a function to generate random data.
# There are different ways of doing this. If you are feeling adventurous, ask your family and friends about their ratings of movies and create a database with real data.

# Then, calculate the statistics of your data using the methods provided by pandas. You might have to do some research on this, use the documentation↗ as a starting point.

def generate_data():
    names = "john bob roberta liam donnie maxwell alina layla sharon marie frank"
    names = names.split()
    ratings = []
    for n in names:
        ratings.append(random.randint(1, 5))
    data = {"UserID": names, "Braveheart": ratings}
    return pd.DataFrame(data)


def main(df):
    print("  --Movie Ratings--")
    avg = []
    mean_rate = df["Braveheart"].mean()
    for n in range(df.shape[0]):
        avg.append(mean_rate)

    df.insert(2, "Average Rating", avg)
    print(df)


def test():
    main(generate_data())
    main(pd.read_csv('movie_ratings.csv')[["UserID", "Braveheart"]])



test()
