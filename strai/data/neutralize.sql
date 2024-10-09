-- set system parameter "database.is_neutralized" in all cases - both in sh (automatic) and in localhost (this one)
-- DO $$
-- BEGIN
--     IF EXISTS (SELECT 1 FROM ir_config_parameter WHERE key = 'database.is_neutralized') THEN
--         UPDATE ir_config_parameter SET value = 'True' WHERE key = 'database.is_neutralized';
--     ELSE
--         INSERT INTO ir_config_parameter (key, value, create_uid, write_uid, create_date, write_date) VALUES ('database.is_neutralized', 'True', 1, 1, NOW(), NOW());
--     END IF;
-- END $$;

-- neutralization flag for the database
-- copy from base. this is not runned when restoring locally
INSERT INTO ir_config_parameter (key, value)
VALUES ('database.is_neutralized', true)
    ON CONFLICT (key) DO
       UPDATE SET value = true;
