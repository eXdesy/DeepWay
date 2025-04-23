CREATE DATABASE IF NOT EXISTS `deepway_db`;
USE `deepway_db`;

CREATE TABLE IF NOT EXISTS `users` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `telegram_id` BIGINT,
    `current_telegram_id` BIGINT,
    `username` VARCHAR(255),
    `password` VARCHAR(255),
    `status` VARCHAR(25),
    `verification` BOOLEAN,
    `backup_code` VARCHAR(25),
    `token` VARCHAR(255),
    `created_date` TIMESTAMP DEFAULT NOW(),
    UNIQUE (`telegram_id`)
);

CREATE TABLE IF NOT EXISTS `boosts` (
    `boost_id` INT AUTO_INCREMENT PRIMARY KEY,
    `buyer_id` BIGINT,
    `subscription_date` TIMESTAMP DEFAULT NOW(),
    `expire_date` TIMESTAMP DEFAULT NULL,
    `boost_status` VARCHAR(25),
    FOREIGN KEY (buyer_id) REFERENCES users(telegram_id)
);

CREATE TABLE IF NOT EXISTS `subscriptions` (
    `subscription_id` INT AUTO_INCREMENT PRIMARY KEY,
    `buyer_id` BIGINT,
    `media_id` BIGINT,
    `subscription_date` TIMESTAMP DEFAULT NOW(),
    `expire_date` TIMESTAMP DEFAULT NULL,
    `link` VARCHAR(50),
    `media_type` VARCHAR(25),
    FOREIGN KEY (buyer_id) REFERENCES users(telegram_id)
);

CREATE TABLE IF NOT EXISTS `profiles` (
    `profile_id` INT AUTO_INCREMENT PRIMARY KEY,
    `owner_id` BIGINT,
    `media_id` BIGINT,
    `name` VARCHAR(50),
    `description` VARCHAR(255),
    `photo` MEDIUMBLOB,
    `category` VARCHAR(50),
    `subcategory` VARCHAR(50),
    `plan1_price` REAL,
    `plan3_price` REAL,
    `plan6_price` REAL,
    `plan12_price` REAL,
    `plan_price` REAL,
    `verification` BOOLEAN,
    `added_time` TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (owner_id) REFERENCES users(telegram_id)
);

CREATE TABLE IF NOT EXISTS `channels` (
    `channel_id` INT AUTO_INCREMENT PRIMARY KEY,
    `owner_id` BIGINT,
    `media_id` BIGINT,
    `name` VARCHAR(50),
    `description` VARCHAR(255),
    `photo` MEDIUMBLOB,
    `category` VARCHAR(50),
    `subcategory` VARCHAR(50),
    `plan1_price` REAL,
    `plan3_price` REAL,
    `plan6_price` REAL,
    `plan12_price` REAL,
    `plan_price` REAL,
    `verification` BOOLEAN,
    `added_time` TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (owner_id) REFERENCES users(telegram_id)
);

CREATE TABLE IF NOT EXISTS `groups` (
    `group_id` INT AUTO_INCREMENT PRIMARY KEY,
    `owner_id` BIGINT,
    `media_id` BIGINT,
    `name` VARCHAR(50),
    `description` VARCHAR(255),
    `photo` MEDIUMBLOB,
    `category` VARCHAR(50),
    `subcategory` VARCHAR(50),
    `plan1_price` REAL,
    `plan3_price` REAL,
    `plan6_price` REAL,
    `plan12_price` REAL,
    `plan_price` REAL,
    `verification` BOOLEAN,
    `added_time` TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (owner_id) REFERENCES users(telegram_id)
);

CREATE TABLE IF NOT EXISTS `supports` (
    `support_id` INT AUTO_INCREMENT PRIMARY KEY,
    `telegram_id` BIGINT,
    `username` VARCHAR(255),
    `description` VARCHAR(255),
    `support_status` VARCHAR(25),
    `created_date` TIMESTAMP DEFAULT NOW(),
    `closed_date` TIMESTAMP DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS `reports_media` (
    `report_media_id` INT AUTO_INCREMENT PRIMARY KEY,
    `reporter_telegram_id` BIGINT,
    `username` VARCHAR(255),
    `media_id` BIGINT,
    `report_description` VARCHAR(255),
    `media_type` VARCHAR(25),
    `report_status` VARCHAR(25),
    `created_date` TIMESTAMP DEFAULT NOW(),
    `closed_date` TIMESTAMP DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS `log_users` (
    `log_user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `current_telegram_id` BIGINT,
    `telegram_id` BIGINT,
    `action` VARCHAR(25),
    `enter_status` BOOLEAN,
    `logged_data` TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS `log_states` (
    `log_state_id` INT AUTO_INCREMENT PRIMARY KEY,
    `current_telegram_id` BIGINT,
    `current_message_id` VARCHAR(50),
    `current_language` VARCHAR(25),
    `current_state` VARCHAR(50),
    `temporal_state` VARCHAR(50),
    `current_action` VARCHAR(50),
    `current_media_id` VARCHAR(50),
    `current_media_type_id` VARCHAR(50),
    `current_media_type` VARCHAR(50),
    `current_media_data` VARCHAR(50),
    `current_media_index` VARCHAR(50),
    `logged_data` TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS `log_media` (
    `log_media_id` INT AUTO_INCREMENT PRIMARY KEY,
    `owner_id` BIGINT,
    `media_id` BIGINT,
    `bot_status` VARCHAR(25),
    `media_type` VARCHAR(25),
    `update_data` TIMESTAMP DEFAULT NOW(),
    `logged_data` TIMESTAMP DEFAULT NOW()
);
