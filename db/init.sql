USE pool_monitor_vc01;

CREATE TABLE History(
id INT AUTO_INCREMENT PRIMARY KEY,
Date DATETIME,
ph_value FLOAT(2,1),
chlorine_ppm FLOAT(2,1),
ph_plus FLOAT(2,2),
ph_min FLOAT(2,2),
chlorine FLOAT(2,2)
);

CREATE TABLE Settings(
id INT AUTO_INCREMENT PRIMARY KEY,
pool_volume INT,
ph_desired FLOAT,
chlorine_desired FLOAT,
ph_plus_dose FLOAT,
ph_min_dose FLOAT,
chlorine_dose FLOAT,
notification INT,
email_receiver varchar(128)
);