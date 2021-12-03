CREATE TABLE Caregivers (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Availabilities (
    Time date,
    Username varchar(255) REFERENCES Caregivers(Username), -- changed from `Username`
    PRIMARY KEY (Time, Username)
);

CREATE TABLE Vaccines (
    Name varchar(255),
    Doses int,
    PRIMARY KEY (Name)
);

CREATE TABLE Patients (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Appointments (
    id INT NOT NULL IDENTITY(1, 1),
    Time date,
    Caregiver varchar(255) REFERENCES Caregivers(Username),
    Patient varchar(255) REFERENCES Patients(Username),
    Vaccine varchar(255) REFERENCES Vaccines(Name), -- added
    PRIMARY KEY (id)
);