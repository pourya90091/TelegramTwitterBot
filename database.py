from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).parent.resolve()

con = sqlite3.connect(f"{BASE_DIR}/db.sqlite3",
                      check_same_thread=False,
                      detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
cur = con.cursor()

def init():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS replies (
            reply_content VARCHAR(256) NOT NULL,
            reply_url VARCHAR(128) NOT NULL,
            tweet_url VARCHAR(128) NOT NULL,
            tweet_owner VARCHAR(128) NOT NULL
        );
    """)
    con.commit()


def add_reply(reply_content, reply_url, tweet_url, tweet_owner):
    cur.execute(f"""INSERT INTO replies VALUES ("{reply_content}", "{reply_url}", "{tweet_url}", "{tweet_owner}");""")
    con.commit()


def is_tweet_exists(tweet_url):
    # Check if this tweet has already been replied to.
    tweet = cur.execute(f"""SELECT tweet_owner FROM replies WHERE tweet_url = "{tweet_url}";""").fetchone()

    return True if tweet else False


def export_all_replies():
    replies = cur.execute(f"""SELECT * FROM replies;""").fetchall()
    file_name = "replies.csv"

    with open(f"{BASE_DIR}/{file_name}", "w", encoding="utf-8") as file:
        file.write("reply_content, reply_url, tweet_url, tweet_owner\n")
        for reply in replies:
            reply_content = reply[0]
            reply_url = reply[1]
            tweet_url = reply[2]
            tweet_owner = reply[3]
            file.write(f"{reply_content}, {reply_url}, {tweet_url}, {tweet_owner}\n")

    return file_name
