import sqlite3

class sqliteConnection:

    def sqlite_connect(self):
        conn = sqlite3.connect("as400_db2.db")

        return conn


if __name__ == 'main':

    conn = sqliteConnection()