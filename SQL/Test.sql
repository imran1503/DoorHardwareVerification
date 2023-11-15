show databases;
use doorhardwarevv;
show tables in doorhardwarevv;
-- create table Compatability(
-- 	Door varchar(255),    -- WOOD, MDF
-- 	Frame varchar(255),   -- ?????????
--     Strike varchar(255),  -- Std 12V, Mortise 24V 
--     ADO varchar(255)      -- LH, LH Rev, RH, RH Rev, None, Maglock, Elec Crashbar, Not Opening
-- );
-- create table DoorType(
-- 	id int,
--     name varchar(255)
-- );
-- create table FrameType(
-- 	id int,
--     name varchar(255)
-- );
-- create table StrikeType(
-- 	id int,
--     name varchar(255)
-- );
-- create table ADOType(
-- 	id int,
--     name varchar(255)
-- ); LH, LH Rev, RH, RH Rev, None, Maglock, Elec Crashbar, Not Opening
-- insert into ADOType values (1,"LH");
-- insert into ADOType values (2,"LH Reverse");
-- insert into ADOType values (3,"RH");
-- insert into ADOType values (4,"RH Reverse");
-- insert into ADOType values (5,"Maglock");
-- insert into ADOType values (6,"Electrical Crashbar");
-- insert into ADOType values (7,"Not Opening");
-- insert into ADOType values (8,"None");

-- insert into StrikeType values (1,"Standard 12V");
-- insert into StrikeType values (2,"Mortise 24V");
-- insert into compatability values(2,1,2, 5);
-- insert into frametype values (1, "Left hand leaf");
-- insert into frametype values (2, "Right hand leaf");
-- drop table compatability;
-- create table Compatability(
-- 	id int primary key,
--     Door_Type varchar(225),                  -- Employee, Visitor, Emp/Vis
--     Door_Swing varchar(225),				 -- Right hand Leaf, Left hand Leaf
-- 	Door_Material varchar(255),              -- WOOD, MDF, Glass
--     Door_Selection varchar(255),             -- single, double, in swing, out swing, medium height turnstile, full height turnstile, optical turnsile, parking gate
--     Door_Location varchar(255),              -- ext, int
--     Fire_Rated_Door Varchar(255),            -- fire rated, required fire exit, required fire rated exit (BOTH)
--  	Frame_Material varchar(255),             -- wood, metal, none
--     Existing_Hardware varchar(255),          -- None, Standard Strike, Mortise Strike, Knob Set, Deadbolt, Magnetic Surface, Magnetic Shear, Electric Lockset, Mechanical exit bar, Maglock
--     Proposed_Hardware varchar(255),          -- None, Standard Strike, Mortise Strike, Knob set, Deadbolt, Magnetic Surface, Magnetic Shear, Electric Lockset, Mechanical Exit bar, Maglock,
--     Proposed_Voltage_Required varchar(255),  -- 12 AC, 12 DC, 24 AC, 24 DC
--     ADO varchar(255),                        -- LH, LH Rev, RH, RH Rev, None, Not Opening
--     Secure_Integration varchar(255),         -- cx33, none
--     Door_Contact varchar(255),               -- resessed, surface, built into lock, none
--     Request_To_Exit varchar(225),            -- wave to open, push button, touch sensitive bar, mechanical exit bar 
-- );

 select * from compatability;

-- select count(*) from compatability where Door = 1 AND Frame = 1 AND Strike = 1 and ADO = 0 ;


