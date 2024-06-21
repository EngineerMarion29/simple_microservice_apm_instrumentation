CREATE DATABASE testdb;

USE testdb;

CREATE TABLE professionals (
    name VARCHAR(50),
    profession VARCHAR(50),
    years_of_experience INT
);

INSERT INTO professionals (name, profession, years_of_experience) VALUES
('Marion', 'Engineer', 7),
('Aslan', 'Doctor', 10),
('Mufasa', 'Lawyer', 8);

