import mysql
from mysql.connector import connection
from database_Connect import connectDB


class checkDB:
    list = [-1,-1,-1,-1]
    def __init__(self, userNameList):
        self.list = userNameList
        print(" CHECKDB CONSTRUCTOR")

    doorInput = list[0]
    frameInput = list[1]
    strikeInput = list[2]
    adoInput = list[3]

    # Create the connection object    IF ERROR ADD PASSWORD
    myconn = mysql.connector.connect(host='localhost', database='DoorHardwareVV', user='root', password='')

    # printing the connection object
    #print(myconn)

    # creating the cursor object
    cursor = myconn.cursor()

    #print(cursor)

    print("LINE 29")
    cursor.execute("""SELECT * FROM compatability where Door = "%s" AND Frame = "%s" AND Strike = "%s" and ADO = "%s" """ %(doorInput, frameInput, strikeInput, adoInput))
    records = cursor.fetchall()
    print(records)
    if records == (None):
        print("No compatability.")
    print(records)

