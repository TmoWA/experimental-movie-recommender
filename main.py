import sqlite3

import numpy as np

import movie_recommender_functions
import sqlite_functions
import pandas as pd


def main():
    sqlite_functions.generate_tables()
    sqlite_functions.load_movie_data()
    print("Welcome to the Movie Browser System.")

    # current_user is a tuple for user ID, username, and last active.
    current_user = manage_users()

    user_logged_in = current_user is not None
    while user_logged_in:
        user_id = current_user[0]
        username = current_user[1]
        print("\nHello,", username)
        print("To look up a movie, enter 1.")
        print("To see recommended movies, enter 2.")
        print("To see your watch history, enter 3.")
        print("To change users, enter 4.")
        print("Enter anything else to exit the program.")
        selected_menu_number = input("Enter your choice: ")

        if selected_menu_number == "1":
            # movie_lookup() returns a movie ID and movie title.
            selected_movie_data = movie_lookup(user_id)

            if selected_movie_data is not None:
                handle_user_movie_selection(user_id, movie_id=selected_movie_data[0],
                                            movie_title=selected_movie_data[1])

        elif selected_menu_number == "2":
            print('\nHere are the recommended movies for "' + username + '" based on watch history:')
            recommended_movies = movie_recommender_functions.recommend_based_on_watch_history(user_id)

            for index, movie in enumerate(recommended_movies, start=1):
                print("\t", index, ' - ', movie[0] + movie[1])

            selection = get_valid_int_input(len(recommended_movies))
            if selection != 0:
                handle_user_movie_selection(user_id, movie_id=recommended_movies[selection - 1][2],
                                            movie_title=recommended_movies[selection - 1][0])

        elif selected_menu_number == "3":
            watch_history = sqlite_functions.get_watch_history(current_user[0])
            history_df = pd.DataFrame(watch_history,
                                      columns=['id', '-Movie Title-', '-Watched-', '-Liked-', '-Ignored-'])
            if history_df.empty:
                print('No watch history for "' + username + '".')
            else:
                history_df.index = np.arange(1, len(history_df) + 1)  # This line sets the indexes to begin from 1.

                # Replaces all 1 and 0 in the latter 3 columns with yes and no for improved readability.
                history_df = history_df.replace({1: 'yes', 0: 'no'})

                print('\nHere is the watch history for "' + username + '":')
                # The following prints all columns except the movie's ID.
                print(history_df[['-Movie Title-', '-Watched-', '-Liked-', '-Ignored-']])

                if input("Would you like to edit items in watch history? Enter y to confirm: ") == "y":
                    selected_index = get_valid_int_input(len(watch_history))
                    handle_user_movie_selection(user_id, watch_history[selected_index-1][0],
                                                watch_history[selected_index-1][1])

        elif selected_menu_number == "4":
            if input('\nLog out from current user "' + username + '"?\nEnter y to confirm: ') == "y":
                print("Logging out...\n")
                current_user = manage_users()
                user_logged_in = current_user is not None
        else:
            print("\nGoodbye. Shutting down...")
            user_logged_in = False


def manage_users():
    while True:
        print("To create a new user, enter 1.")
        print("To manage existing users, enter 2.")
        print("Enter anything else to exit the program.")
        user_menu_selection = input("Enter your choice: ")

        if user_menu_selection == "1":
            # The loop here is to ensure the user is only transferred after a valid username or from canceling creation.
            # If they enter something invalid, they will instead be prompted to try again due to the loop.
            while True:
                print("\nTo create a new user, please enter a unique username.")
                print("To return to the previous menu, enter 0.")
                new_username = input("Enter your choice: ")

                if new_username == "0":
                    break

                try:
                    print('This will create a new user with the username "' + new_username + '".')

                    if input("Enter y to confirm or anything else to cancel: ") == "y":
                        sqlite_functions.create_new_user(new_username)
                        print('New user "' + new_username + '" created successfully.')
                    break
                except sqlite3.IntegrityError:
                    print("That username already exists. Please choose a different one.")

        elif user_menu_selection == "2":
            users = sqlite_functions.get_users()

            if len(users) == 0:
                print("No existing users.")
            else:
                print("Here are the existing users:")
                for index, row in enumerate(users, start=1):
                    print("\t", index, ' - ', row[1])

                selection = get_valid_int_input(len(users))
                if selection != 0:
                    username = users[selection - 1][1]
                    login_or_delete = input("Enter 1 to log in as the selected user, "
                                            "enter 2 to delete the selected user, "
                                            "or enter anything else to cancel selection.")

                    if login_or_delete == "1":
                        print('Logging in as user "' + username + '".')
                        sqlite_functions.login_user(username)
                        return users[selection - 1]

                    elif login_or_delete == "2":
                        print('You have selected to delete the user "' + username + '".')
                        creation_confirmation = input("Enter y to confirm, or anything else to cancel:")
                        if creation_confirmation == "y":
                            sqlite_functions.delete_user(username)
                            print('Successfully deleted the user "' + username + '".')
        else:
            print("\nGoodbye. Shutting down...")
            return None
        print("")


def movie_lookup(user_id):
    while True:
        movie_name = input("Please enter the name of the movie you want to find: ")
        results = sqlite_functions.select_movie(movie_name, user_id)

        if len(results) > 0:
            break
        else:
            print("No results for that search. Please try again")

    print('Here are the first 10 closest results to "' + movie_name + '":')

    for index, row in enumerate(results, start=1):
        print("\t", index, ' - ', row[1])

    selection = get_valid_int_input(len(results))
    if selection == 0:
        return None

    # Returns an object with the selected movie's ID and title.
    return [results[selection - 1][0], results[selection - 1][1]]


def get_valid_int_input(limit):
    print("To select one of the results, enter the number to its left, or "
          "enter 0 to return to the previous menu.")
    valid_input = False
    selection = 0
    while not valid_input:
        selection = input("Enter your selection: ")

        try:
            selection = int(selection)
        except ValueError:
            print("Please enter an integer.")
            continue

        if selection > limit or selection < 0:
            print("Please enter a number that matches one of the options.")
        else:
            valid_input = True

    return selection


def get_user_review(user_id, movie_id, movie_title):
    response = input("\nHave you watched " + movie_title + "? Enter y for yes, n for no: ")
    while response != "y" and response != "n":
        response = input("Please enter y or n.")
    watched = 1 if response == "y" else 0

    response = input("Did you like " + movie_title + "? Enter y for yes, n for no: ")
    while response != "y" and response != "n":
        response = input("Please enter y or n.")
    liked = 1 if response == "y" else 0

    response = input("Would you like to ignore " + movie_title + " in future searches? Enter y for yes, n for no: ")
    while response != "y" and response != "n":
        response = input("Please enter y or n.")
    ignored = 1 if response == "y" else 0

    return [user_id, movie_id, watched, liked, ignored]


# This function is for figuring out if the user wants to "watch" a movie or find similar movies after a selection.
def handle_user_movie_selection(user_id, movie_id, movie_title):
    while True:
        print('\nYou have selected the movie "' + movie_title + '".')
        print("Enter 1 to update watch history for this movie, enter 2 to find similar movies, "
              "or enter 0 to return to the main menu.")
        user_selection = get_valid_int_input(2)

        # Option 0 exits the loop
        if user_selection == 0:
            break

        # Option 1 gets user data for the selection and then adds it to the database.
        elif user_selection == 1:
            rename_me_later = get_user_review(user_id, movie_id, movie_title)
            sqlite_functions.insert_or_update_watch_history(rename_me_later)
            print('Watch history for "' + movie_title + '" successfully updated.')
            break

        # Option 2 finds similar movies to the selected one
        elif user_selection == 2:
            print('Here are movies similar to "' + movie_title + '"')

            similar_movies = movie_recommender_functions.get_recommended_movies(movie_id,
                                                                                user_id,
                                                                                6)
            for index, movie in enumerate(similar_movies[1], start=1):
                print("\t", index, ' - ', movie)

            selection = get_valid_int_input(len(similar_movies[1]))

            if selection == 0:
                break
            else:
                movie_id = similar_movies[0][selection - 1]
                movie_title = similar_movies[1][selection - 1]


if __name__ == '__main__':
    main()
