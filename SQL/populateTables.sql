-- ========================================
--  Door Hardware Compatibility Database
-- ========================================
show databases;
USE doorhardwarevv;

-- ---------- Populate Lookup Tables ----------

INSERT INTO DoorMaterial (name) VALUES 
 ('Wood'), ('MDF'), ('Glass'), ('Metal');

INSERT INTO FrameMaterial (name) VALUES 
 ('Steel'), ('Wood'), ('Aluminum'), ('None');

INSERT INTO StrikeType (name) VALUES 
 ('Standard Strike 12V'), ('Mortise Strike 24V'), ('Magnetic Lock');

INSERT INTO ADOType (name) VALUES 
 ('LH'), ('LH Reverse'), ('RH'), ('RH Reverse'),
 ('Maglock'), ('Electrical Crashbar'), ('Not Opening'), ('None');

INSERT INTO HardwareType (name) VALUES
 ('None'), ('Standard Strike'), ('Mortise Lock'), ('Electric Lockset'),
 ('Maglock'), ('Electric Crashbar'), ('Panic Bar');

INSERT INTO VoltageType (name) VALUES 
 ('12V DC'), ('24V AC'), ('24V DC');

INSERT INTO IntegrationUnit (name, description) VALUES
 ('CX-33', 'Camden Door Controls CX-33 door control relay/sequencer'),
 ('CX-EL331', 'Camden door operator power supply and relay interface'),
 ('Securitron TS-12', 'Touch sense bar controller'),
 ('None', 'No integration unit required');

-- ---------- Sample Compatibility Rows ----------
INSERT INTO Compatibility (
  door_material_id, frame_material_id, strike_type_id, ado_type_id,
  existing_hardware_id, proposed_hardware_id, voltage_id, integration_unit_id,
  door_swing, door_selection, door_location, fire_rating,
  door_contact, request_to_exit, notes
)
VALUES
  (1,1,1,1, 1,4,1,4, 'Left', 'Single', 'Front', 'Yes', 'Yes', 'Yes', 'Installed in lobby'),
  (1,1,2,2, 3,4,2,1, 'Right', 'Double', 'Rear', 'No', 'No', 'Yes', NULL),
  (3,3,3,5, 5,5,1,3, 'None', 'Single', 'Office', 'No', 'Yes', 'No', 'Glass door with maglock'),
  (2,2,1,3, 2,6,2,2, 'Left Reverse', 'Single', 'Side', 'Yes', 'Yes', 'Yes', 'Fire rated door with crashbar');
