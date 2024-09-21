# experimental-movie-recommender
A movie recommendation system built in Python. It connects to a SQLite database and provides an interface for the user to search for movies, manage watch history, and get recommendations for movies. The recommendation logic relies on content-based filtering. Additionally, the movies database was built using a CSV of the top 1000 movies from the Internet Movie Database
Future considerations: If I were to enhance this project in the future (or if it were intended to be a commercial application), I would introduce some level of security so that each user cannot log-in as or delete any other user without appropriate privileges. Currently, the user system allows unrestrained freedom and is essentially just a logging system. Additionally, in the current form, the same recommendation can appear multiple times if multiple watched movies are similar to it, but I chose to ignore this since the project is small in scale. Similarly, if the scale of this project was greater, I would pay much closer attention to fine-tuning the SQL queries to maximize performance. Currently, this is not a concern due to this project's size, but could prove troublesome if it were bigger. 
