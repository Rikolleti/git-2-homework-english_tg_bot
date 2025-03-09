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
            cur.execute("DROP TABLE IF EXISTS userwords;")
            cur.execute("DROP TABLE IF EXISTS words;")
            cur.execute("DROP TABLE IF EXISTS users;")


def create_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users(
                    id BIGINT PRIMARY KEY
                );

                CREATE TABLE IF NOT EXISTS userwords(
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    translate VARCHAR(255) NOT NULL,
                    user_id BIGINT REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS words(
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    translate VARCHAR(255) NOT NULL
                );
                """
            )

def insert_words(words):
    with get_connection() as conn:
        with conn.cursor() as cur:
            word_ids = []
            for word in words:
                cur.execute(
                    """
                    INSERT INTO words (title, translate)
                    VALUES (%s, %s)
                    RETURNING id;
                    """,
                    word,
                )
                word_id = cur.fetchone()[0]
                word_ids.append(word_id)
            return word_ids

def insert_words_from_user(title: str, translate: str, user_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            user_exists = cur.fetchone()
            if not user_exists:
                cur.execute("""INSERT INTO users (id) VALUES (%s) ;""", (user_id,))
                conn.commit()
            cur.execute(
                """
            INSERT INTO userwords (title, translate, user_id)
            VALUES (%s, %s, %s)
            RETURNING user_id;
            """,
                (title, translate, user_id),
            )
            show_user_id = cur.fetchone()[0]
            return show_user_id


def show_words(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
            SELECT title, translate FROM userwords WHERE user_id = %s
            UNION
            SELECT title, translate FROM words;
            """,
                (user_id,),
            )
            words = cur.fetchall()
            return words


def count_words(user_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
            SELECT COUNT(title) FROM userwords WHERE user_id = %s
            """,
                (user_id,),
            )
            user_words_count = cur.fetchone()[0]
            cur.execute(
                """
                SELECT COUNT(title) FROM words;
                """
            )
            all_words_count = cur.fetchone()[0]
            total_words = user_words_count + all_words_count
            return total_words


def delete_word(translate: str, user_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
            DELETE FROM userwords
            WHERE translate = %s AND user_id = %s;
            """,
                (translate, user_id),
            )
            if cur.rowcount > 0:
                print(f"Word {translate} deleted for user {user_id}")
        return cur.rowcount > 0


# Инициализация таблицы
if __name__ == "__main__":
    drop_table()
    create_table()
    words_data = [
        ("Peace", "Мир"),
        ("Friend", "Друг"),
        ("Love", "Любовь"),
        ("Sun", "Солнце"),
        ("Water", "Вода"),
        ("Tree", "Дерево"),
        ("Book", "Книга"),
        ("Music", "Музыка"),
        ("Time", "Время"),
    ]
    inserted_words = insert_words(words_data)
