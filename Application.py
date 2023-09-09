import mysql
import mysql
from mysql.connector import connection
from database_Connect import connectDB

def main():
    userInputList = []
    print("Answer numbers for selecting an option. ")
    print("Door?       1.MDF   2.Wood")
    userInputList.append(input(">> "))
    print("Frame? ???????????")
    userInputList.append("1")
    print("Strike?      1.Standard 12V  2.Mortise 24V")
    userInputList.append(input(">> "))
    print("ADO?     1.LH 2.LH Rev 3.RH 4.RH Rev 5.Maglock 6.Electric Crashbar 7.Not Opening 8.None ")
    userInputList.append(input(">> "))

    print(userInputList)

   # checkDB(userInputList)

    # Create the connection object    IF ERROR ADD PASSWORD
    myconn = mysql.connector.connect(host='localhost', database='DoorHardwareVV', user='root', password='')

    # printing the connection object
    # print(myconn)

    # creating the cursor object
    cursor = myconn.cursor()

    # print(cursor)

    print("LINE 29")
    cursor.execute(
        """SELECT * FROM compatability where Door = "%s" AND Frame = "%s" AND Strike = "%s" and ADO = "%s" """ % (
        int (userInputList[0]), int (userInputList[1]), int (userInputList[2]), int (userInputList[3])))
    #records = cursor.fetchall()
    records = None

    if records == (None):
        print("No compatability.")
    else: print("Database says these components should work together. >>" + str(records))
if __name__ == '__main__':
    main()
