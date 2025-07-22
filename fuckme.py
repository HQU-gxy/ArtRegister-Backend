import PieceMgr
import logging
import bottle
from enum import Enum
from typing import Any
import config


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


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


pieceMgr = PieceMgr.PieceMgr(config.DB_FILENAME)


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
        logging.error("Username parameter is missing")
        return genReturnValue(Status.VALUE_ERROR, "Name parameter is required")

    userId = pieceMgr.findUserIdByName(username)

    if not userId:
        logging.info(f"User '{username}' not found, creating new user")
        userId = pieceMgr.newUser(username)
        if not userId:
            return genReturnValue(Status.VALUE_ERROR, "Failed to create new user")

    logging.debug(f"User ID for '{username}' is {userId}")
    return genReturnValue(Status.OK, userId)

@bottle.route("/check_user_exist")
def check_user_exist() -> str:
    """
    The handler for request of checking if a user exists.
    It expects a query parameter 'username'.

    :return: Status and the user ID if found, otherwise NOT_FOUND.
    """
    username = bottle.request.query.username  # type: ignore

    # Parameter validation
    if not username:
        return genReturnValue(Status.VALUE_ERROR, "username parameter is required")

    userId = pieceMgr.findUserIdByName(username)

    if not userId:
        return genReturnValue(Status.NOT_FOUND, "User not found")

    return genReturnValue(Status.OK, userId)

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
    piece_name = args.getunicode("piece_name")  # type: ignore
    piece_uid = args["piece_uid"]  # type: ignore

    print(piece_name)
    # Parameter validation
    if not user_id or not piece_name or not piece_uid:
        return genReturnValue(Status.VALUE_ERROR,
                              "Parameters user_id, piece_name, and piece_uid are required")

    # Check if the user exists
    if pieceMgr.findUserNameById(int(user_id)) is None:
        return genReturnValue(Status.NOT_FOUND, "User not found")

    # Check if the art piece already exists
    if (not pieceMgr.registerNewPiece(piece_name, piece_uid, int(user_id))):
        logging.error(f"Art piece with UID {piece_uid} already exists")
        return genReturnValue(Status.ALREADY_EXISTS, "Art piece with this UID already exists")

    logging.debug(
        f"New art piece '{piece_name}' with UID {piece_uid} created by user ID {user_id}")
    return genReturnValue(Status.OK, 0)


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

    result = pieceMgr.findPieceByUid(piece_uid)
    # Check if the art piece exists
    if not result:
        return genReturnValue(Status.NOT_FOUND, "Art piece not found")

    return genReturnValue(Status.OK, result)


@bottle.route("/mark_on_sale", method="POST")
def mark_on_sale() -> str:
    """
    The handler for request of marking an art piece as on sale.
    It expects the following form parameters:
    - user_id: The ID of the user who owns the art piece.
    - piece_uid: The tag UID of the art piece.

    :return: Status only
    """
    args = bottle.request.forms
    user_id = args["user_id"]  # type: ignore
    piece_uid = args["piece_uid"]  # type: ignore
    is_on_sale = args["on_sale"]  # type: ignore

    # Parameter validation
    if not user_id or not piece_uid or not is_on_sale:
        return genReturnValue(Status.VALUE_ERROR,
                              "Parameters user_id, piece_uid, and on_sale are required")

    # Check if the user exists
    if not pieceMgr.findUserNameById(int(user_id)):
        return genReturnValue(Status.NOT_FOUND, "User not found")

    # Check if the art piece is owned by the user
    piece_info = pieceMgr.findPieceByUid(piece_uid)
    if not piece_info:
        return genReturnValue(Status.NOT_FOUND, "Art piece not found")
    if piece_info["owner_id"] != int(user_id):
        return genReturnValue(Status.VALUE_ERROR, "User does not own this art piece")

    # Update the art piece's on_sale status
    is_on_sale = is_on_sale.lower() == 'true'
    pieceMgr.markOnSale(piece_uid, is_on_sale)
    logging.debug(
        f"Art piece with UID {piece_uid} marked as {'not' if not is_on_sale else ''} on sale by user ID {user_id}")
    return genReturnValue(Status.OK, 0)


@bottle.route("/get_piece_transactions")
def get_piece_transactions() -> str:
    """
    The handler for request of getting transactions of an art piece.
    It expects a query parameter 'piece_uid'.

    :return: Status and the list of transactions.
    """
    piece_uid = bottle.request.query.piece_uid  # type: ignore

    # Parameter validation
    if not piece_uid:
        return genReturnValue(Status.VALUE_ERROR, "piece_uid parameter is required")

    result = pieceMgr.getTransactions(piece_uid)
    # Check if the art piece exists
    if not result:
        return genReturnValue(Status.NOT_FOUND, "No transactions found for this art piece")

    return genReturnValue(Status.OK, result)


@bottle.route("/new_transaction", method="POST")
def new_transaction() -> str:
    """
    The handler for request of creating a new transaction for an art piece.
    It expects the following form parameters:
    - old_owner_id: The ID of the user who is the old owner of the art piece.
    - new_owner_id: The ID of the user who is the new owner of the art piece.
    - piece_uid: The tag UID of the art piece.

    :return: Status only
    """
    args = bottle.request.forms
    old_owner_id = args["old_owner_id"]  # type: ignore
    new_owner_id = args["new_owner_id"]  # type: ignore
    piece_uid = args["piece_uid"]  # type: ignore
    # Parameter validation
    if not old_owner_id or not new_owner_id or not piece_uid:
        return genReturnValue(Status.VALUE_ERROR,
                              "Parameters old_owner_id, new_owner_id, and piece_uid are required")

    # Check if the old owner exists
    if not pieceMgr.findUserNameById(int(old_owner_id)):
        return genReturnValue(Status.NOT_FOUND, "Old owner not found")

    # Check if the new owner exists
    if not pieceMgr.findUserNameById(int(new_owner_id)):
        return genReturnValue(Status.NOT_FOUND, "New owner not found")

    if pieceMgr.newTransaction(piece_uid, int(old_owner_id), int(new_owner_id)):
        logging.debug(
            f"New transaction created for piece UID {piece_uid} from old owner ID {old_owner_id} to new owner ID {new_owner_id}")
        return genReturnValue(Status.OK, 0)

    logging.error(
        f"Failed to create transaction for piece UID {piece_uid} from old owner ID {old_owner_id} to new owner ID {new_owner_id}")
    return genReturnValue(Status.VALUE_ERROR, "User does not own this art piece or piece UID is invalid")


@bottle.route("/creator_get_pieces")
def creator_get_pieces() -> str:
    """
    The handler for request of getting all art pieces created by a specific user.
    It expects a query parameter 'user_id'.

    :return: Status and the list of art pieces.
    """
    user_id = bottle.request.query.user_id  # type: ignore

    # Parameter validation
    if not user_id:
        return genReturnValue(Status.VALUE_ERROR, "user_id parameter is required")

    result = pieceMgr.getCreatorPieces(int(user_id))
    # Check if the user exists
    print(result)
    if not result:
        return genReturnValue(Status.NOT_FOUND, "No art pieces found for this user")

    return genReturnValue(Status.OK, result)


# This will block the main thread until the server is stopped
bottle.run(host="0.0.0.0", port=2333)
