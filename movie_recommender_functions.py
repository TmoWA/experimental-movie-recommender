import random
import sqlite3
import pandas as pd

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# This function vectorizes the text and then calculates the cosine similarity.
def calculate_cosine_similarity(dataframe):
    cv = CountVectorizer(max_features=10000, stop_words='english')
    vectorized_text = cv.fit_transform(dataframe['similarity_tags'].values.astype('U')).toarray()
    return cosine_similarity(vectorized_text)


# This function returns a list of recommended movies for a given user.
def get_recommended_movies(movie_id, user_id, quantity):
    conn = sqlite3.connect("movie-records.db")
    
    # This query will select all movies except those that the user has ignored and/or already watched.
    # The searched movie is also needed when calculating similarities, so that one is also retrieved.
    df = pd.read_sql('SELECT m.* '
                     'FROM movies m '
                     'WHERE m.id = :movie_id '
                     'OR NOT EXISTS (SELECT wh.movie_id '
                     'FROM watch_history wh '
                     'WHERE m.id = wh.movie_id AND user_id = :user_id AND (wh.watched = 1 OR wh.ignored = 1)) ',
                     con=conn, params={"movie_id": movie_id, "user_id": user_id})

    quantity += 1  # Quantity is incremented once since we always skip the first result, which is the searched movie.

    # Find the index of the given movie in the DataFrame
    index = df[df['id'] == movie_id].index[0]

    # Calculate similarity scores and then puts them into a sorted list of descending similarity.
    similarity = calculate_cosine_similarity(df)
    distance = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda vector: vector[1])

    # Gets the movie IDs and titles
    # The .item() call is to get the int value instead of the np int64 type.
    movie_ids = [df.iloc[i[0]].id.item() for i in distance[1:quantity]]
    titles = [df.iloc[i[0]].title for i in distance[1:quantity]]

    return movie_ids, titles


def recommend_based_on_watch_history(user_id):
    conn = sqlite3.connect("movie-records.db")
    cur = conn.cursor()
    # An inner join is used because we only want rows that have a match on both tables.
    # The ORDER BY is constructed to select the most recently liked movies, with nulls put at the end (if present).
    cur.execute("SELECT m.title, m.id "
                "FROM movies m "
                "INNER JOIN watch_history u ON m.id = u.movie_id "
                "WHERE u.liked = 1 AND u.ignored = 0 AND u.user_id = ? "
                "ORDER BY last_edited IS NOT NULL DESC", (user_id,))
    rec_list = []
    liked_movies = cur.fetchall()

    for movie in liked_movies:
        recs = get_recommended_movies(movie[1], user_id, 3)

        for index, rec_movie in enumerate(recs[1]):
            # This appends the recommended movie's title, the reason for the recommendation, and the movie's ID.
            rec_list.append([rec_movie, ' similar to movie "' + movie[0] + '".', recs[0][index]])

    if len(rec_list) < 6:
        # This IF fills in any remaining list slots with random top ten movies after excluding ignored ones.
        limit = 6 - len(rec_list)

        cur.execute("SELECT m.id, m.title "
                    "FROM movies m "
                    "WHERE NOT EXISTS (SELECT wh.movie_id  "
                    "FROM watch_history wh "
                    "WHERE m.id = wh.movie_id AND wh.user_id = ? AND (watched = 1 OR ignored = 1)) "
                    "ORDER BY m.id "
                    "LIMIT 10", (user_id,))
        top_ten_movies = cur.fetchall()
        random.shuffle(top_ten_movies)

        for i in range(limit):
            rec_list.append([top_ten_movies[i][1], " because it's a top ten movie.", top_ten_movies[i][0]])

    # The list is shuffled to prevent the exact same recommended movies appearing every time.
    random.shuffle(rec_list)
    return rec_list[0:6]
