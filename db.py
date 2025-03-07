import psycopg2
import configparser

config = configparser.ConfigParser()
config.read("settings.ini")
database = config["Postgres"]["database"].strip()
login = config["Postgres"]["login"].strip()
password = config["Postgres"]["password"].strip()


def get_connection():
    return psycopg2.connect(database=database, user=login, password=password)


def drop_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
            DROP TABLE IF EXISTS word_list;
            """
            )


def create_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
            CREATE TABLE IF NOT EXISTS word_list(
                word_id SERIAL PRIMARY KEY,
                target_word VARCHAR(60) NOT NULL,
                russian_word VARCHAR(60) NOT NULL,
                other_words VARCHAR(255),
                user_id BIGINT
            );
            """
            )


def insert_words(target_word: str, russian_word: str, other_words: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
            INSERT INTO word_list (target_word, russian_word, other_words)
            VALUES (%s, %s, %s)
            RETURNING word_id;
            """,
                (target_word, russian_word, other_words),
            )
            show_word_id = cur.fetchone()[0]
            return show_word_id


def insert_words_from_user(target_word: str, russian_word: str, other_words: str, user_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
            INSERT INTO word_list (target_word, russian_word, other_words, user_id)
            VALUES (%s, %s, %s, %s)
            RETURNING word_id;
            """,
                (target_word, russian_word, other_words, user_id),
            )
            show_word_id = cur.fetchone()[0]
            return show_word_id


def show_words(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT word_id, target_word, russian_word, other_words
                FROM word_list
                WHERE user_id IS NULL OR user_id = %s;
            """,
                (user_id,),
            )
            rows = cur.fetchall()
            words = [
                {"word_id": row[0], "target_word": row[1], "russian_word": row[2], "other_words": row[3]}
                for row in rows
            ]
            return words


def count_words(user_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
            SELECT COUNT(target_word) FROM word_list
            WHERE user_id IS NULL OR user_id = %s;
            """,
                (user_id,),
            )
            result = cur.fetchone()[0]
            return result


def delete_word(russian_word: str, user_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            output = cur.execute(
                """
            DELETE FROM word_list
            WHERE russian_word = %s AND user_id = %s;
            """,
                (russian_word, user_id),
            )
            if output is not None:
                print(f"Word {russian_word} deleted for user {user_id}")
        return cur.rowcount > 0


# Инициализация таблицы
drop_table()
create_table()
insert_words("Peace", "Мир", "King, Break, Stop")
insert_words("Friend", "Друг", "Topic, Look, Drop")
insert_words("Love", "Любовь", "Heart, Feel, Passion")
insert_words("Sun", "Солнце", "Light, Day, Sky")
insert_words("Water", "Вода", "Ocean, River, Drink")
insert_words("Tree", "Дерево", "Forest, Leaf, Nature")
insert_words("Book", "Книга", "Read, Page, Story")
insert_words("Music", "Музыка", "Sound, Song, Melody")
insert_words("Time", "Время", "Clock, Moment, Hour")
insert_words("House", "Дом", "Apartment, Room, Building")
