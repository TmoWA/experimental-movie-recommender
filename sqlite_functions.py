import sqlite3
import re
import nltk

import pandas as pd
from nltk import word_tokenize, WordNetLemmatizer
from nltk.corpus import stopwords

conn = sqlite3.connect("movie-records.db")
cur = conn.cursor()
cur.execute("PRAGMA foreign_keys = 1")  # Necessary for the cascading delete of users and watch history.

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')


def generate_tables():
    # Table for user data
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users(id integer PRIMARY KEY,
                                username varchar(50) NOT NULL UNIQUE,
                                last_login datetime DEFAULT NULL);
        """)

    # Table for movie data
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS movies(id integer PRIMARY KEY,
                                poster_link text,
                                title varchar(100),
                                year integer,
                                certificate varchar(20),
                                runtime varchar(20),
                                genre varchar(100),
                                imdb_rating decimal(4,2),
                                overview text,
                                meta_score integer,
                                director varchar(100),
                                star1 varchar(100),
                                star2 varchar(100),
                                star3 varchar(100),
                                star4 varchar(100),
                                similarity_tags text);
        """)

    # Table for users' watch history
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS watch_history(user_id integer,
                                movie_id integer,
                                watched integer CHECK (watched IN (0, 1)),
                                liked integer CHECK (liked IN (0, 1)),
                                ignored integer CHECK (ignored IN (0, 1)),
                                creation_date datetime DEFAULT current_timestamp,
                                last_edited datetime default NULL,
                                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                                FOREIGN KEY(movie_id) REFERENCES movies(id) ON DELETE CASCADE,
                                PRIMARY KEY(user_id, movie_id));
        """)


# This function converts text to lowercase, removes punctuation and stopwords, and then lemmatizes everything else.
def clean_text_for_tags(text):
    text = text.lower()

    # Removes punctuation from the text using a regular expression
    text = re.sub(r'[^\w\s\d]', '', text)

    # Tokenizes the text into words and then removes the stopwords
    words = word_tokenize(text)
    words = [word for word in words if word not in set(stopwords.words('english'))]

    # Lemmatize each word
    words = [WordNetLemmatizer().lemmatize(word) for word in words]

    # Rebuilds a string from the cleaned and lemmatized words
    text = ' '.join(words)
    return text


# If the database is empty, this method will populate it from the chosen CSV file.
def load_movie_data():
    # Retrieves row 1 of the movies table. If there are no rows, it will return zero, meaning the table is empty.
    row_count = cur.execute("SELECT EXISTS (SELECT 1 FROM movies);").fetchone()[0]

    # If the movies table is empty, the following will populate it from a CSV and prepare a tags column for later.
    if row_count == 0:
        movies_data_csv = 'imdb_top_1000.csv'
        movies_headers = ['poster_link', 'title', 'year', 'certificate', 'runtime', 'genre', 'imdb_rating', 'overview',
                          'meta_score', 'director', 'star1', 'star2', 'star3', 'star4']
        movies_df = pd.read_csv(movies_data_csv, names=movies_headers, skiprows=1)
        movies_df['similarity_tags'] = movies_df['genre'] + ' ' + movies_df['overview']
        movies_df['similarity_tags'] = movies_df['similarity_tags'].apply(clean_text_for_tags)

        movies_df.to_sql('movies', conn, if_exists='append', index=False)


def login_user(username):
    cur.execute("UPDATE users "
                "SET last_login = CURRENT_TIMESTAMP "
                "WHERE username = ?",
                (username,))
    conn.commit()


def create_new_user(username):
    cur.execute("INSERT INTO users(username) "
                "VALUES(?)",
                (username,))
    conn.commit()


def delete_user(username):
    cur.execute("DELETE FROM users "
                "WHERE username = ? ",
                (username,))
    conn.commit()


def get_users():
    cur.execute("SELECT * FROM users")
    return cur.fetchall()


# This function selects movies whose titles are close enough to the searched term, excluding the user's ignored movies.
def select_movie(movie_title, user_id):
    cur.execute("SELECT m.id, m.title "
                "FROM movies m "
                "WHERE m.title LIKE ? AND "
                "NOT EXISTS "
                "(SELECT wh.movie_id "
                "FROM watch_history wh "
                "WHERE m.id = wh.movie_id AND ignored = 1 AND user_id = ?) "
                "LIMIT 10", ('%' + movie_title + '%', user_id))
    return cur.fetchall()


def insert_or_update_watch_history(user_data):
    cur.execute("INSERT INTO watch_history(user_id, movie_id, watched, liked, ignored, last_edited) "
                "VALUES(?, ?, ?, ?, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT (user_id, movie_id) DO UPDATE "
                "SET watched = ?, liked = ?, ignored = ?, last_edited = CURRENT_TIMESTAMP",
                (user_data[0], user_data[1], user_data[2], user_data[3], user_data[4],
                 user_data[2], user_data[3], user_data[4],))
    conn.commit()


def get_watch_history(user_id):
    cur.execute("SELECT m.id, m.title, wh.watched, wh.liked, wh.ignored "
                "FROM movies m "
                "INNER JOIN watch_history wh ON wh.movie_id = m.id "
                "WHERE wh.user_id = ? "
                "ORDER BY wh.last_edited DESC", (user_id,))
    return cur.fetchall()
