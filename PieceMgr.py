from typing import Optional
import sqlite3
import config
import logging

TABLE_USERS = "users"
TABLE_PCS = "art_pieces"
TABLE_TRANS = "transactions"


class PieceMgr:

    __db: sqlite3.Connection
    __cursor: sqlite3.Cursor

    def __init__(self, filename: str) -> None:
        self.__db = sqlite3.connect(filename)
        self.__cursor = self.__db.cursor()

        for tab in [TABLE_PCS, TABLE_TRANS, TABLE_USERS]:
            try:
                self.__cursor.execute(f"select * from {tab}")

            except sqlite3.OperationalError:
                logging.warning(f"Table '{tab}' not found, creating it")
                if tab == TABLE_USERS:
                    self.__cursor.execute(f"create table {TABLE_USERS}(\
                                name     text not null,\
                                user_id  int unsigned not null)")

                elif tab == TABLE_PCS:
                    self.__cursor.execute(f"create table {TABLE_PCS}(\
                                name         text not null,\
                                piece_uid    text not null,\
                                creator_id   int unsigned not null,\
                                owner_id     int unsigned not null,\
                                on_sale      bool not null)")

                elif tab == TABLE_TRANS:
                    self.__cursor.execute(f"create table {TABLE_TRANS}(\
                                piece_uid    text not null,\
                                old_owner_id int unsigned not null,\
                                new_owner_id int unsigned not null,\
                                dt           datetime not null)")

            except sqlite3.DatabaseError:
                logging.error(
                    f"Invalid db file: {filename}, check or remove it.")
                raise Exception("DB file is invalid")

    def newUser(self, name: str) -> Optional[int]:
        """
        Creates a new user in the database and returns the new user ID.
        If the maximum user ID is reached, it returns None.

        :param name: The name of the user to create.
        :return: The new user ID as an integer, or None if the maximum ID is reached.
        """
        self.__cursor.execute(f"select MAX(user_id) from {TABLE_USERS}")
        user_id = self.__cursor.fetchone()[0]
        if user_id is None:  # If no users exist, start from 1
            user_id = 0
        user_id += 1

        if user_id >= config.MAX_USER_ID:
            logging.error("Maximum user ID reached, cannot create new user")
            return None

        self.__cursor.execute(f"insert into {TABLE_USERS}(name, user_id) values(?, ?)",
                              (name, user_id))
        self.__db.commit()
        return user_id

    def findUserIdByName(self, name: str) -> Optional[int]:
        """
        Finds a user ID by username.

        :param name: The username to search for.
        :return: The user ID if found, otherwise None.
        """
        self.__cursor.execute(
            f"select user_id from {TABLE_USERS} where name = ?", (name,))
        result = self.__cursor.fetchone()
        return result[0] if result else None

    def findUserNameById(self, user_id: int) -> Optional[str]:
        """
        Finds a username by user ID.

        :param user_id: The ID of the user to check.
        :return: True if the user exists, otherwise False.
        """
        self.__cursor.execute(
            f"select name from {TABLE_USERS} where user_id = ?", (user_id,))
        result = self.__cursor.fetchone()
        return result[0] if result else None

    def findPieceByUid(self, piece_uid: str) -> Optional[dict]:
        """
        Finds an art piece by its tag UID.

        :param piece_uid: The tag UID of the art piece.
        :return: A dictionary containing the piece details if found, otherwise None.
        """
        self.__cursor.execute(
            f"select * from {TABLE_PCS} where piece_uid = ?", (piece_uid,))
        result = self.__cursor.fetchone()

        return {
            "name": result[0],
            "piece_uid": result[1],
            "creator": self.findUserNameById(result[2]),
            "owner": self.findUserNameById(result[3]),
            "on_sale": result[4]
        } if result else None

    def markOnSale(self, piece_uid: str, is_on_sale: bool) -> bool:
        """
        Marks an art piece as on sale.

        :param piece_uid: The tag UID of the art piece.
        :return: True if the operation was successful, otherwise False.
        """
        self.__cursor.execute(
            f"update {TABLE_PCS} set on_sale = ? where piece_uid = ?", (is_on_sale, piece_uid))
        self.__db.commit()
        return self.__cursor.rowcount > 0

    def registerNewPiece(self, name: str, piece_uid: str, creator_id: int) -> bool:
        """
        Registers a new art piece created.

        :param name: The name of the art piece.
        :param piece_uid: The tag UID of the art piece.
        :param creator_id: The ID of the user who created the art piece.
        :return: True if the operation was successful, otherwise False.
        """
        if (self.findPieceByUid(piece_uid)):
            return False

        self.__cursor.execute(f"insert into {TABLE_PCS}(name, piece_uid, creator_id, owner_id, on_sale) \
                                values(?, ?, ?, ?, ?)", (name, piece_uid, creator_id, creator_id, False))
        self.__db.commit()
        return True

    def getTransactions(self, piece_uid: str) -> Optional[list]:
        """
        Retrieves the transaction history of an art piece.

        :param piece_uid: The tag UID of the art piece.
        :return: A list of transactions if found, otherwise None.
        """
        self.__cursor.execute(
            f"select * from {TABLE_TRANS} where piece_uid = ?", (piece_uid,))

        if self.__cursor.rowcount == 0:
            return None

        transactions = []
        for row in self.__cursor.fetchall():
            transactions.append({
                "old_owner": self.findUserNameById(row[1]),
                "new_owner": self.findUserNameById(row[2]),
                "dt": row[3]
            })

        return transactions

    def getCreatorPieces(self, creator_id: int) -> Optional[list]:
        """
        Retrieves all art pieces info created by a specific user.

        :param creator_id: The ID of the user who created the art pieces.
        :return: A list of art piece info if found, otherwise None.
        """
        self.__cursor.execute(
            f"select * from {TABLE_PCS} where creator_id = ?", (creator_id,))

        if self.__cursor.rowcount == 0:
            return None

        pieces = []
        for row in self.__cursor.fetchall():
            pieces.append({
                "name": row[0],
                "piece_uid": row[1],
                "creator": self.findUserNameById(row[2]),
                "owner": self.findUserNameById(row[3]),
                "on_sale": row[4]
            })

        return pieces
