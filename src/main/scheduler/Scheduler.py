import sys
from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    """
    TODO
    Creates a patient: <username> <password>
    :param tokens: list of strings
    """

    if len(tokens) != 3:
        print("Please try again!")
        return
    username = tokens[1]
    password = tokens[2]

    # check 2: check if username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the patient
    try:
        patient = Patient(username, salt=salt, hash=hash)  # caregiver object created
        # save to caregiver information to our database
        patient.save_to_db()
        print(" *** Account created successfully *** ")
    except pymssql.Error:
        print("Create failed")
        return


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    try:
        caregiver = Caregiver(username, salt=salt, hash=hash)
        # save to caregiver information to our database
        try:
            caregiver.save_to_db()
        except:
            print("Create failed, Cannot save")
            return
        print(" *** Account created successfully *** ")
    except pymssql.Error:
        print("Create failed")
        return


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error:
        print("Error occurred when checking username")
        cm.close_connection()
    cm.close_connection()
    return False


def username_exists_patient(username):
    """
    :param username: string
    :return: boolean
    """
    cm = ConnectionManager()
    conn = cm.create_connection()

    # SQL statement to check if username is in database
    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        row = cursor.fetchone()
        if row == None:
            return False
    except pymssql.Error:
        print("Error occurred when checking username")
        cm.close_connection()
    cm.close_connection()
    return True


def login_patient(tokens):
    """
    TODO: Part 1
    """
    # login <username> <password>
    # check 1: if logged in, log out first
    global current_patient
    if current_patient is not None or current_caregiver is not None:
        print("Already logged-in!")
        return

    # check 2: length of tokens == 3
    if len(tokens) != 3:
        print("Please try again!")
        return
    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error:
        print("Error occurred when logging in")

    # check if the login was successful:
    if patient is None:
        print("Please try again!")
    else:
        print("Patient logged in as: " + username)
        current_patient = patient


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("Already logged-in!")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        try:
            caregiver = Caregiver(username, password=password).get()
        except:
            print("Get Failed")
            return
    except pymssql.Error:
        print("Error occurred when logging in")

    # check if the login was successful
    if caregiver is None:
        print("Please try again!")
    else:
        print("Caregiver logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    """
    TODO
    Outputs username of caregiver for date/time & number of doses
    left for each vaccine
    tokens: <date>
    """
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    d = None
    try:
        d = datetime.datetime(year, month, day)
    except ValueError:
        print("Please enter a valid date!")
    except pymssql.Error as db_err:
        print("Error occurred when uploading availability")

    cm = ConnectionManager()
    conn = cm.create_connection()
    # SQL statement to check if username is in database
    get_caregiver_availabilities = "SELECT Username FROM Availabilities a WHERE a.Time = %s"
    get_vaccine_availabilities = "SELECT * FROM Vaccines"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(get_caregiver_availabilities, d)
        one_care_row = cursor.fetchone()
        if one_care_row is None:
            print("There are no availabilities for the given date!")
            return
        cursor2 = conn.cursor(as_dict=True)
        cursor2.execute(get_vaccine_availabilities)
        for care_row in cursor:
            for vax_row in cursor2:
                print("Caregiver: " + str(care_row['Username']) + ", Vaccine: " + str(vax_row['Name'])
                  + ", available_doses: " + str(vax_row['Doses']))
    except pymssql.Error:
        print("Error occurred when getting availabilities")
        cm.close_connection()
    cm.close_connection()


def reserve(tokens):
    """
    TODO: Part 2
    Allows a logged in patient to reserve vaccine appointment
    tokens: <date> <vaccine>
    """
    if len(tokens) != 3:
        print("Please try again!")
        return

    # ensure current user is logged in as a patient:
    global current_caregiver
    global current_patient
    if current_caregiver is not None:
        print("Currently logged in as a caregiver! Please log out and login as "
              "a patient to reserve an appointment.")
        return
    if current_patient is None:
        print("Not currently logged in as a patient! Please login as a patient"
              "to reserve an appointment")
    # make sure date is valid
    # make sure there is availability on date:
    # add appointment to `Appointments` table
    # update number of available_doses in `Vaccines` table
    # randomly assign caregiver
    # remove availability for date from Availabilities table for caregiver
    """
        except ValueError:
        print("Please enter a valid date!")
    """


def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = str(tokens[1])
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        # check if current caregiver already has availability on date
        check_availability = "SElECT * FROM Availabilities WHERE Time = %s AND Username = %s"
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(check_availability, (d, current_caregiver.get_username()))
            one_row = cursor.fetchone()
            if one_row is not None:
                print("There is already availability for the provided date!")
                return
        except pymssql.Error:
            print("Error occurred when checking availabilities")
            cm.close_connection()

        # upload availability if not already there
        try:
            current_caregiver.upload_availability(d)
        except:
            print("Upload Availability Failed")
        print("Availability uploaded!")
    except ValueError:
        print("Please enter a valid date!")
    except pymssql.Error as db_err:
        print("Error occurred when uploading availability")


def cancel(tokens):
    """
    TODO: Extra Credit
    """
    pass


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = str(tokens[1])
    doses = int(tokens[2])
    vaccine = None
    try:
        try:
            vaccine = Vaccine(vaccine_name, doses).get()
        except:
            print("Failed to get Vaccine!")
            return
    except pymssql.Error:
        print("Error occurred when adding doses")

    # check 3: if getter returns null, it means that we need to create the vaccine and insert it into the Vaccines
    #          table

    if vaccine is None:
        try:
            vaccine = Vaccine(vaccine_name, doses)
            try:
                vaccine.save_to_db()
            except:
                print("Failed To Save")
                return
        except pymssql.Error:
            print("Error occurred when adding doses")
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            try:
                vaccine.increase_available_doses(doses)
            except:
                print("Failed to increase available doses!")
                return
        except pymssql.Error:
            print("Error occurred when adding doses")

    print("Doses updated!")


def show_appointments(tokens):
    '''
    TODO: Part 2
    Output scheduled appointments for the current user
    '''
    if len(tokens) != 1:
        print("Uh oh, too many parameters! Only need to type 'show_appointments'"
              " to show all current appointments!")
        return

    # make sure the user is logged in
    global current_caregiver
    global current_patient
    if current_patient is None and current_patient is None:
        print("Cannot show appointments if you are not logged in! Please login"
              "as a caregiver or patient.")
        return
    cm = ConnectionManager()
    conn = cm.create_connection()
    # for caregivers: appointment ID, vaccine name, date, patient name
    if current_caregiver is not None:
        username = current_caregiver.get_username()
        get_appointments = "SELECT id, Vaccine, Time, Patient FROM Appointments WHERE Caregiver = %s"
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(get_appointments, username)
            for row in cursor:
                print("Appointment ID: " + str(row['id']) + "Vaccine: " + str(row['Vaccine'])
                      + "Date: " + str(row['Time']) + "Patient: " + str(row['Patient']))
        except pymssql.Error:
            print("Error occurred when showing appointments")
            cm.close_connection()

    # for patients: appointment ID, vaccine name, date, caregiver name
    if current_patient is not None:
        username = current_patient.get_username()
        get_appointments = "SELECT id, Vaccine, Time, Caregiver FROM Appointments WHERE Patient = %s"
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(get_appointments, username)
            for row in cursor:
                print("Appointment ID: " + str(row['id']) + "Vaccine: " + str(row['Vaccine'])
                      + "Date: " + str(row['Time']) + "Caregiver: " + str(row['Caregiver']))
        except pymssql.Error:
            print("Error occured when showing appointments")
            cm.close_connection()
    cm.close_connection()


def logout(tokens):
    """
    TODO: Part 2
    """
    if len(tokens) != 1:
        print("Uh oh, too many parameters! Only need to type 'logout' to log out!")
        return
    global current_caregiver
    global current_patient
    if current_patient is None and current_caregiver is None:
        print("Not currently logged in!")
        return
    if current_caregiver is not None:
        print("Successfully logged out:", current_caregiver.get_username())
        current_caregiver = None
        return
    if current_patient is not None:
        print("Successfully logged out:", current_patient.get_username())
        current_patient = None
        return


def start():
    stop = False
    while not stop:
        print()
        print(" *** Please enter one of the following commands *** ")
        print("> create_patient <username> <password>")  # //DONE TODO: implement create_patient (Part 1)
        print("> create_caregiver <username> <password>")
        print("> login_patient <username> <password>")  #// DONE TODO: implement login_patient (Part 1)
        print("> login_caregiver <username> <password>")
        print("> search_caregiver_schedule <date (MM-DD-YYYY)>")  #// TODO: implement search_caregiver_schedule (Part 2)
        print("> reserve <date> <vaccine>") #// TODO: implement reserve (Part 2)
        print("> upload_availability <date (MM-DD-YYYY)>")
        print("> cancel <appointment_id>") #// TODO: implement cancel (extra credit)
        print("> add_doses <vaccine> <number>")
        print("> show_appointments")  #// TODO: implement show_appointments (Part 2)
        print("> logout") #// DONE TODO: implement logout (Part 2)
        print("> Quit")
        print()
        response = ""
        print("> Enter: ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Type in a valid argument")
            break

        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Try Again")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == cancel:
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Thank you for using the scheduler, Goodbye!")
            stop = True
        else:
            print("Invalid Argument")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
