import mysql
import mysql
from mysql.connector import connection
from database_Connect import connectDB


def main():
    userInputList = []
    print("Answer numbers for selecting an option. ")
    print("Door Material?      1.MDF  2.Wood")
    userInputList.append(input(">> "))
    print("Door is on the _____ of the frame?      1.Left hand leaf  2.Right hand leaf")
    userInputList.append("1")
    print("Strike?      1.Standard 12V  2.Mortise 24V")
    userInputList.append(input(">> "))
    print("ADO?     1.LH  2.LH  Rev  3.RH  4.RH Rev  5.Maglock  6.Electric Crashbar  7.Not Opening  8.None ")
    userInputList.append(input(">> "))

    print("DEBUG USERINPUTLIST: "+ str(userInputList))

    # checkDB(userInputList)

    # Create the connection object    IF ERROR ADD PASSWORD
    myconn = mysql.connector.connect(host='localhost', database='DoorHardwareVV', user='root', password='')

    # printing the connection object
    # print(myconn)

    # creating the cursor object
    cursor = myconn.cursor()

    cursor.execute(
        """SELECT count(*) FROM compatability where Door = "%s" AND Frame = "%s" AND Strike = "%s" and ADO = "%s"; """
        % (int(userInputList[0]), int(userInputList[1]), int(userInputList[2]), int(userInputList[3]))
    )
    result = cursor.fetchone()
    print("DEBUG result: " + str(result))

    if str(result) == "(0,)":
        print("No compatability.")
        print("Please Try Again. >>\n\n")
        main()
    else:
        print("Database says these components should work together.")

        exit(0)


if __name__ == '__main__':
    main()
