-- ========================================
--  Door Hardware Compatibility Database - CREATE TABLES
-- ========================================

CREATE DATABASE IF NOT EXISTS doorhardwarevv;
USE doorhardwarevv;

-- ---------- Lookup Tables ----------

CREATE TABLE DoorMaterial (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL
);

CREATE TABLE FrameMaterial (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL
);

CREATE TABLE StrikeType (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL
);

CREATE TABLE ADOType (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL
);

CREATE TABLE HardwareType (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL
);

CREATE TABLE VoltageType (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL
);

CREATE TABLE IntegrationUnit (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  description VARCHAR(255)
);

-- ---------- Main Compatibility Table ----------

CREATE TABLE Compatibility (
  id INT PRIMARY KEY AUTO_INCREMENT,
  door_material_id INT,
  frame_material_id INT,
  strike_type_id INT,
  ado_type_id INT,
  existing_hardware_id INT,
  proposed_hardware_id INT,
  voltage_id INT,
  integration_unit_id INT,
  door_swing VARCHAR(100),
  door_selection VARCHAR(255),
  door_location VARCHAR(100),
  fire_rating VARCHAR(100),
  door_contact VARCHAR(100),
  request_to_exit VARCHAR(100),
  notes VARCHAR(500),
  FOREIGN KEY (door_material_id) REFERENCES DoorMaterial(id),
  FOREIGN KEY (frame_material_id) REFERENCES FrameMaterial(id),
  FOREIGN KEY (strike_type_id) REFERENCES StrikeType(id),
  FOREIGN KEY (ado_type_id) REFERENCES ADOType(id),
  FOREIGN KEY (existing_hardware_id) REFERENCES HardwareType(id),
  FOREIGN KEY (proposed_hardware_id) REFERENCES HardwareType(id),
  FOREIGN KEY (voltage_id) REFERENCES VoltageType(id),
  FOREIGN KEY (integration_unit_id) REFERENCES IntegrationUnit(id)
);
