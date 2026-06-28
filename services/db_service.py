import sqlite3


def get_connection():
    return sqlite3.connect("database.db")


def save_file(user_id, filename, cloud_provider, file_size):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
INSERT INTO files
(
    user_id,
    filename,
    cloud_provider,
    file_size
)
VALUES (?, ?, ?, ?)
""",
(
    user_id,
    filename,
    cloud_provider,
    file_size
))

    conn.commit()
    conn.close()


def get_user_files(user_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM files
        WHERE user_id = ?
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    return rows
def search_user_files(user_id, search):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM files
        WHERE user_id = ?
        AND filename LIKE ?
        """,
        (user_id, "%" + search + "%")
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


def get_file_owner(filename):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id
        FROM files
        WHERE filename = ?
        """,
        (filename,)
    )

    row = cursor.fetchone()

    conn.close()

    return row

def delete_file_record(filename):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM files
        WHERE filename = ?
        """,
        (filename,)
    )

    conn.commit()
    conn.close()
    
def get_cloud_provider(filename):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT cloud_provider
        FROM files
        WHERE filename = ?
        """,
        (filename,)
    )

    row = cursor.fetchone()

    conn.close()

    return row