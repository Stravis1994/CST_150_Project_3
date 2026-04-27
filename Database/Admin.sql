-- Seed admin login record(s) for the Admin table.
-- Active: 1775526151868@@127.0.0.1@3306@tgc_store
-- Insert the default admin account used by /admin/login.
INSERT INTO Admin (username, password_hash) VALUES ('admin1', '$argon2id$v=19$m=65536,t=3,p=4$8KzgFZwWMxXLZLheRqaVdA$HkKA6HVZUYbfaoPBQ4O2kjuSTKBvGvqV1M94ZBtpkRk');