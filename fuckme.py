import sqlite3
import logging
import bottle
from enum import Enum
from typing import Any

MAX_USER_ID = 114514

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

DB_FILENAME = "shit.db"
TABLE_USERS = "users"
TABLE_PCS = "art_pieces"
TABLE_TRANS = "transactions"

db = sqlite3.connect(DB_FILENAME)
cursor = db.cursor()

for tab in [TABLE_PCS, TABLE_TRANS, TABLE_USERS]:
    try:
        cursor.execute(f"select * from {tab}")

    except sqlite3.OperationalError:
        logging.warning(f"Table '{tab}' not found, creating it")
        if tab == TABLE_USERS:
            cursor.execute(f"create table {TABLE_USERS}(\
                           name     text not null,\
                           user_id  int unsigned not null)")

        elif tab == TABLE_PCS:
            cursor.execute(f"create table {TABLE_PCS}(\
                           name         text not null,\
                           piece_uid    text not null,\
                           creator_id   int unsigned not null,\
                           owner_id     int unsigned not null,\
                           on_sale      bool not null)")

        elif tab == TABLE_TRANS:
            cursor.execute(f"create table {TABLE_TRANS}(\
                           piece_uid    text not null,\
                           old_owner_id int unsigned not null,\
                           new_owner_id int unsigned not null,\
                           dt           datetime not null)")

    except sqlite3.DatabaseError:
        logging.error(f"Invalid db file: {DB_FILENAME}, check or remove it.")
        exit(1)


class Status(Enum):
    OK = 0
    NOT_FOUND = 1
    ALREADY_EXISTS = 2
    VALUE_ERROR = 3


def genReturnValue(status: Status, value: Any) -> str:
    """
    Generates a standardized return value in the form of a string.
    The return value is a serialized dictionary(or JSON) containing the status and value.

    :param status: The status of the operation, as a Status enum.
    :param value: The value to return, or an error message if the operation failed.

    :return: A string representation of the return value dictionary.
    """

    foo = {'status': status.value, 'value': value}
    return str(foo)


def genId() -> int:
    """
    Generates a new user ID by finding the maximum user_id in the users table
    and incrementing it by one. If the maximum user_id is reached, it returns -1.
    If the table is empty, it returns 1.

    :return: The new user ID as an integer, or -1 if the maximum ID is reached.
    """
    cursor.execute(f"SELECT MAX(user_id) FROM {TABLE_USERS}")
    id = cursor.fetchone()[0]
    if id == None:
        return 1

    if id >= MAX_USER_ID:
        logging.error("Maximum user ID reached, cannot create new user")
        return -1

    return id+1


@bottle.route("/")
def index() -> str:
    """ The handler for the root path, which is useless. """
    return "<b>WTF are you looking for?</b>"


@bottle.route("/get_user_id")
def get_user_id() -> str:
    """ The handler for request of getting user ID by username.
    It expects a query parameter 'username'.
    If the user does not exist, it creates a new user with a generated ID.

    :return: Status and the user ID.
    """
    username = bottle.request.query.username  # type: ignore
    if not username:
        return genReturnValue(Status.VALUE_ERROR, "Name parameter is required")

    cursor.execute(
        f"select user_id from {TABLE_USERS} where name = ?", (username,))
    result = cursor.fetchone()

    if result:
        return genReturnValue(Status.OK, str(result[0]))
    else:
        userId = genId()
        logging.info(f"User '{username}' not found, creating new user")
        cursor.execute(f"insert into {TABLE_USERS}(name, user_id) values(?, ?)",
                       (username, userId))
        return genReturnValue(Status.OK, str(userId))


@bottle.route("/new_piece", method="POST")
def new_piece() -> str:
    """
    The handler for request of creating a new art piece.
    It expects the following form parameters:
    - user_id: The ID of the user creating the art piece.
    - piece_name: The name of the art piece.
    - piece_uid: The tag UID of the art piece.

    :return: Status only
    """
    args = bottle.request.forms
    user_id = args["user_id"]  # type: ignore
    piece_name = args["piece_name"]  # type: ignore
    piece_uid = args["piece_uid"]  # type: ignore

    # Parameter validation
    if not user_id or not piece_name or not piece_uid:
        return genReturnValue(Status.VALUE_ERROR,
                              "Parameters user_id, piece_name, and piece_uid are required")

    # Check if the user exists
    cursor.execute(f"select * from {TABLE_USERS} where user_id = ?",
                   (user_id,))
    if not cursor.fetchone():
        return genReturnValue(Status.NOT_FOUND, "User not found")

    # Check if the art piece already exists
    cursor.execute(f"select * from {TABLE_PCS} where piece_uid = ?",
                   (piece_uid,))
    if cursor.fetchone():
        return genReturnValue(Status.ALREADY_EXISTS, "Art piece with this UID already exists")

    # Insert the new art piece into the database and return success
    cursor.execute(f"insert into {TABLE_PCS}(name, piece_uid, creator_id, owner_id, on_sale) \
                   values(?, ?, ?, ?, ?)", (piece_name, piece_uid, user_id, user_id, False))
    db.commit()
    return genReturnValue(Status.OK, "0")


@bottle.route("/get_piece_info")
def get_piece_info() -> str:
    """
    The handler for request of getting information about an art piece.
    It expects a query parameter 'piece_uid'.

    :return: Status and the art piece information.
    """
    piece_uid = bottle.request.query.piece_uid  # type: ignore

    # Parameter validation
    if not piece_uid:
        return genReturnValue(Status.VALUE_ERROR, "piece_uid parameter is required")

    # Check if the art piece exists
    cursor.execute(
        f"select * from {TABLE_PCS} where piece_uid = ?", (piece_uid,))
    result = cursor.fetchone()
    if not result:
        return genReturnValue(Status.NOT_FOUND, "Art piece not found")
    
    # Return the art piece information
    piece_info = {
        "name": result[0],
        "creator_id": result[2],
        "owner_id": result[3],
        "on_sale": result[4]
    }
    return genReturnValue(Status.OK, piece_info)


# This will block the main thread until the server is stopped
bottle.run(host="0.0.0.0", port=2333)

db.close()
exit()
