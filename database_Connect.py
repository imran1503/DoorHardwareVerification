import mysql.connector

# Create the connection object    IF ERROR ADD PASSWORD
myconn = mysql.connector.connect(host='localhost', database='DoorHardwareVV', user='root',password='')

# printing the connection object
print(myconn)

# creating the cursor object
cur = myconn.cursor()

print(cur)