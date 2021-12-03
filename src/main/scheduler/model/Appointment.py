import sys
sys.path.append("../util/*")
sys.path.append("../db/*")
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql


class Appointment:
    def __init__(self, id, date=None, Caregiver=None, Patient=None, Vaccine=None):
        self.id = id
        self.date = date
        self.Caregiver = Caregiver
        self.Patient = Patient
        self.Vaccine = Vaccine

    def get(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.sursor(as_dict=True)

        get_appt_details = "SELECT * FROM Appointments WHERE id = %s"

        try:
            cursor.execute(get_appt_details, self.id)
            for row in cursor:
                self

        except pymssql.Error:
            print("Error occurred when getting Appointments")
            cm.close_connection()
        cm.close_connection()
        return None

    def get_appointment_id(self):
        return self.id

    def get_date(self):
        return self.date

    def get_caregiver(self):
        return self.Caregiver

    def get_patient(self):
        return self.Patient

    def get_vaccine(self):
        return self.Vaccine

    def save_to_db(self):
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()

        add_appointment = "INSERT INTO Appointments VALUES (%s, %s, %s, %s, %s)"

        # try:
        #     cursor.execute(add_appointment, (self.username, self.salt, self.hash))
        #     conn.commit()
        # except pymssql.Error as db_error:
        #     print("Error occurred when inserting Patients")
        #     sqlrc = str(db_error.args[0])
        #     print("Exception code:" + str(sqlrc))
        #     cm.close_connection()
        # cm.close_connection()