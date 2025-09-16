import os
import mysql.connector
from dotenv import load_dotenv

def restart():
    print("input is not a number.")
    print("Please Try Again. >>\n\n")
    main()

def check_user_input(userInput):
    try:
        # Convert it into integer
        val = int(userInput)
        print("Input is an integer number. Number = ", val)

        if userInput > 10 or userInput < 0:
            restart()
    except ValueError:
        restart()


def main():
    load_dotenv()
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    userInputList = []
    print("Answer numbers for selecting an option. ")

    print("Door Material?      1.MDF  2.Wood")
    DoorMatInput = (input(">> "))
    check_user_input(DoorMatInput)
    userInputList.append(int(DoorMatInput))

    print("Door is on the _____ of the frame?      1.Left hand leaf  2.Right hand leaf")
    userInputList.append("1")
    print("Strike?      1.Standard 12V  2.Mortise 24V")
    StrikeInput = (input(">> "))
    check_user_input(StrikeInput)
    userInputList.append(int(StrikeInput))
    print("ADO?     1.LH  2.LH  Rev  3.RH  4.RH Rev  5.Maglock  6.Electric Crashbar  7.Not Opening  8.None ")
    ADOInput = (input(">> "))
    check_user_input(ADOInput)
    userInputList.append(int(ADOInput))

    # Create the connection object    IF ERROR ADD PASSWORD
    myconn = mysql.connector.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password= DB_PASSWORD)
    cursor = myconn.cursor()
    cursor.execute(
        """SELECT count(*) FROM compatability where Door = "%s" AND Frame = "%s" AND Strike = "%s" and ADO = "%s"; """
        % (int(userInputList[0]), int(userInputList[1]), int(userInputList[2]), int(userInputList[3]))
    )
    result = cursor.fetchone()

    if str(result) == "(0,)":
        restart()

    else:
        print("Database says these components should work together.")
        exit(0)

if __name__ == '__main__':
    main()
