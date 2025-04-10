# © 2025 eXdesy — All rights reserved.
# This code is for educational use only.
# Do not reuse, copy, modify, or redistribute.
import os
from dotenv import load_dotenv
import mysql.connector
from languages import language_es, language_uk, language_us, language_ru

load_dotenv()
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

db_connection = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = db_connection.cursor()
languages = {
    'language_us': language_us,
    'language_ru': language_ru,
    'language_es': language_es,
    'language_uk': language_uk
}

# users
def fetch_user_token(telegram_id):
    cursor.execute('SELECT token FROM `users` WHERE current_telegram_id = %s',
                   (telegram_id,))
    result = cursor.fetchone()
    return result[0] if result else False

def fetch_user_telegram_id(username, cell_data, cell):
    cursor.execute(f'SELECT telegram_id FROM `users` WHERE username = %s AND {cell} = %s',
                   (username, cell_data))
    result = cursor.fetchone()
    return result[0] if result else False

def verify_user(telegram_id):
    cursor.execute('SELECT 1 FROM `users` WHERE telegram_id = %s',
                   (telegram_id,))
    result = cursor.fetchone()
    return result[0] if result else False

def register_user(telegram_id, username, password, status, verification, backup_code, token, created_date):
    cursor.execute('''
        INSERT INTO users (telegram_id, current_telegram_id, username, password, status, verification, backup_code, token, created_date) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                   (telegram_id, telegram_id, username, password, status, verification, backup_code, token, created_date))
    db_connection.commit()
    return

def login_and_update_user_session(telegram_id, username, token, password, old_username):
    cursor.execute('UPDATE `users` SET current_telegram_id = NULL WHERE telegram_id = %s',
                   (telegram_id,))
    db_connection.commit()
    cursor.execute('UPDATE `users` SET current_telegram_id = %s, username = %s, token = %s WHERE password = %s AND username = %s',
                   (telegram_id, username, token, password, old_username))
    db_connection.commit()
    return

def verify_user_data(telegram_id, validate_data, cell_data):
    cursor.execute(f'SELECT {cell_data} FROM `users` WHERE current_telegram_id = %s',
                   (telegram_id,))
    result = cursor.fetchone()
    return True if result and validate_data == result[0] else False

def update_user_data(telegram_id, update_data, cell_data):
    cursor.execute(f'UPDATE `users` SET {cell_data} = %s WHERE current_telegram_id = %s',
                   (update_data, telegram_id))
    db_connection.commit()
    return

def restore_user_account(telegram_id, token, backup_code):
    cursor.execute('SELECT telegram_id FROM `users` WHERE backup_code = %s',
                   (backup_code,))
    result = cursor.fetchone()

    cursor.execute('UPDATE `users` SET current_telegram_id = NULL, token = NULL WHERE current_telegram_id = %s OR telegram_id = %s',
                   (telegram_id, result[0]))
    db_connection.commit()

    cursor.execute('UPDATE `users` SET current_telegram_id = %s, token = %s WHERE backup_code = %s',
                   (telegram_id, token, backup_code))
    db_connection.commit()
    return

def clear_user_session(telegram_id):
    cursor.execute('UPDATE `users` SET token = NULL WHERE current_telegram_id = %s',
                   (telegram_id,))
    db_connection.commit()
    return

# boosts
def create_boosts(buyer_id, subscription_date, expire_date, boost_status):
    cursor.execute('INSERT INTO boosts (buyer_id, subscription_date, expire_date, boost_status) '
                   'VALUES (%s, %s, %s, %s)',
                   (buyer_id, subscription_date, expire_date, boost_status))
    db_connection.commit()
    return

# log_users
def create_log_users(current_telegram_id, telegram_id, enter_status, action, logged_data):
    cursor.execute('INSERT INTO log_users (current_telegram_id, telegram_id, enter_status, action, logged_data) '
                   'VALUES (%s, %s, %s, %s, %s)',
                   (current_telegram_id, telegram_id, enter_status, action, logged_data))
    db_connection.commit()
    return

# log_states
def create_log_states(current_telegram_id, current_message_id, current_language, current_state, temporal_state, current_action, current_media_id, current_media_type_id, current_media_type, current_media_data, current_media_index, logged_data):
    cursor.execute('INSERT INTO `log_states` (current_telegram_id, current_message_id, current_language, current_state, temporal_state, current_action, current_media_id, current_media_type_id, current_media_type, current_media_data, current_media_index, logged_data) '
                   'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                   (current_telegram_id, current_message_id, current_language, current_state, temporal_state, current_action, current_media_id, current_media_type_id, current_media_type, current_media_data, current_media_index, logged_data))
    db_connection.commit()
    return

def update_log_states_data(current_telegram_id, update_data, cell_data):
    cursor.execute(f'UPDATE `log_states` SET {cell_data} = %s WHERE current_telegram_id = %s',
                   (update_data, current_telegram_id))
    db_connection.commit()
    return

def fetch_log_states_data(current_telegram_id, cell_data):
    cursor.execute(f'SELECT {cell_data} FROM `log_states` WHERE current_telegram_id = %s',
                   (current_telegram_id,))
    result = cursor.fetchone()
    if cell_data == 'current_language':
        return languages.get(result[0]) if result else False
    else:
        return result[0] if result else False

# media
def create_media(telegram_id, user_data, added_time, media_type):
    cursor.execute(f'''
        INSERT INTO `{media_type}` (owner_id, media_id, name, description, photo, category, subcategory, plan1_price, plan3_price, plan6_price, plan12_price, plan_price, verification, added_time) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                   (telegram_id, user_data['media_id'], user_data['name'], user_data['description'], user_data['photo'], user_data['category'], user_data['subcategory'], user_data['plan1_price'], user_data['plan3_price'], user_data['plan6_price'], user_data['plan12_price'], user_data['plan_price'], False, added_time))
    db_connection.commit()
    return

def fetch_all_media_id(media_type):
    cursor.execute(f'SELECT media_id, category  FROM `{media_type}`')
    result = cursor.fetchall()
    return result if result else []

def fetch_media_by_id(media_type, media_id):
    cursor.execute(f'SELECT * FROM `{media_type}` WHERE media_id = %s',
                   (media_id,))
    result = cursor.fetchall()
    return result if result else False

def fetch_media_by_id_and_category(subcategory, media_type, media_id):
    cursor.execute(f'SELECT * FROM `{media_type}` WHERE subcategory = %s AND media_id = %s',
                   (subcategory, media_id))
    result = cursor.fetchall()
    return result if result else False

def fetch_media_price(media_id, media_type):
    cursor.execute(f'SELECT plan1_price, plan3_price, plan6_price, plan12_price, plan_price FROM `{media_type}` WHERE media_id = %s',
                   (media_id,))
    result = cursor.fetchone()
    return result

# user media
def fetch_user_media(telegram_id, media_type, media_id):
    cursor.execute(f'SELECT * FROM `{media_type}` WHERE media_id = %s AND owner_id = %s',
                   (media_id, telegram_id))
    result = cursor.fetchall()
    return result

def fetch_user_unregistered_media(telegram_id, media_type):
    id_key = media_type.rstrip('s')
    cursor.execute(f'SELECT media_id FROM `log_media` WHERE owner_id = %s AND media_type = %s AND media_id NOT IN (SELECT media_id FROM `{media_type}`)',
                   (telegram_id, id_key))
    result = cursor.fetchall()
    return result

def update_user_media_data(telegram_id, media_type_id, media_type, cell, cell_data):
    id_key = media_type.rstrip('s')
    cursor.execute(f'UPDATE `{media_type}` SET {cell} = %s WHERE {id_key}_id = %s AND owner_id = %s',
                   (cell_data, media_type_id, telegram_id))
    db_connection.commit()
    return

def delete_user_media(telegram_id, media_id, media_type):
    cursor.execute(f'DELETE FROM `{media_type}` WHERE media_id = %s AND owner_id = %s',
                   (media_id, telegram_id))
    db_connection.commit()

def count_user_media(telegram_id, media_type):
    cursor.execute(f'SELECT COUNT(*) FROM `{media_type}` WHERE owner_id = %s', (telegram_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

# subscriptions
def create_subscription(telegram_id, media_id, datetime, expire_date, link, media_type):
    cursor.execute(f'''
        INSERT INTO `subscriptions` (buyer_id, media_id, subscription_date, expire_date, link, media_type) 
        VALUES (%s, %s, %s, %s, %s, %s)''',
                   (telegram_id, media_id, datetime, expire_date, link, media_type))
    db_connection.commit()
    return

def verify_user_subscription(telegram_id, media_id):
    cursor.execute('SELECT 1 FROM `subscriptions` WHERE buyer_id = %s AND media_id = %s',
                   (telegram_id, media_id))
    result = cursor.fetchone()
    return result

def fetch_user_subscriptions(telegram_id, media_type):
    cursor.execute('SELECT media_id, subscription_date, expire_date, link FROM `subscriptions` WHERE buyer_id = %s AND media_type = %s',
                   (telegram_id, media_type))
    result = cursor.fetchall()
    return result

def count_user_subscriptions(telegram_id):
    cursor.execute('''
        SELECT u.username, COUNT(s.subscription_id) AS subscription_count FROM `users` u
        LEFT JOIN `subscriptions` s ON u.current_telegram_id = s.buyer_id
        WHERE u.current_telegram_id = %s GROUP BY u.username''',
                   (telegram_id,))
    result = cursor.fetchone()
    return result

# reports_media
def create_media_report(reporter_telegram_id, username, media_id, report_description, media_type, created_date):
    cursor.execute('''
        INSERT INTO `reports_media` (reporter_telegram_id, username, media_id, report_description, media_type, report_status, created_date) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                   (reporter_telegram_id, username, media_id, report_description, media_type, 'PROCESSING', created_date))
    db_connection.commit()
    return

def count_media_report_status(media_id, report_status):
    cursor.execute('SELECT COUNT(*) FROM reports_media WHERE media_id = %s AND report_status = %s',
                   (media_id, report_status))
    result = cursor.fetchone()
    return result[0] if result else 0

# log_media
def create_log_media(owner_id, media_id, bot_status, media_type, logged_data, update_data):
    cursor.execute('INSERT INTO log_media (owner_id, media_id, bot_status, media_type, update_data, logged_data) '
                   'VALUES (%s, %s, %s, %s, %s, %s)',
                   (owner_id, media_id, bot_status, media_type, logged_data, update_data))
    db_connection.commit()
    return

def update_log_media_status(new_status, owner_id, media_type, media_id, update_data):
    cursor.execute('UPDATE log_media SET bot_status = %s, owner_id = %s, media_type = %s update_data = %s WHERE media_id = %s',
                   (new_status, owner_id, media_type, media_id, update_data))
    db_connection.commit()
    return

def verify_log_media(media_id):
    cursor.execute('SELECT 1 FROM log_media WHERE media_id = %s',
                   (media_id,))
    result = cursor.fetchone()
    return result

# support
def create_support_request(telegram_id, username, description, created_date):
    cursor.execute('''
        INSERT INTO supports (telegram_id, username, description, support_status, created_date) 
        VALUES (%s, %s, %s, %s, %s)''',
                   (telegram_id, username, description, 'PROCESSING', created_date))
    db_connection.commit()
    return

# Recommendations
def fetch_user_subscription_category(telegram_id, media_type):
    cursor.execute(f'SELECT DISTINCT mt.category FROM `{media_type}` mt INNER JOIN subscriptions s ON mt.media_id = s.media_id WHERE s.buyer_id = %s',
                   (telegram_id,))
    result = cursor.fetchall()
    return result

def fetch_verified_user_media(media_type):
    cursor.execute(f'SELECT mt.media_id FROM `{media_type}` mt INNER JOIN users u ON mt.owner_id = u.telegram_id WHERE u.verification = True')
    result = cursor.fetchall()
    return result

def fetch_boosted_media(media_type):
    cursor.execute(f'SELECT mt.media_id FROM `{media_type}` mt INNER JOIN boosts b ON mt.owner_id = b.buyer_id WHERE b.boost_status  = True')
    result = cursor.fetchall()
    return result

def count_media_subscriptions(media_type):
    cursor.execute(f'''
        SELECT mt.media_id, COUNT(s.subscription_id) AS total_subscriptions
        FROM `{media_type}` mt
        LEFT JOIN subscriptions s ON mt.media_id = s.media_id
        GROUP BY mt.media_id''')
    result = cursor.fetchall()
    return result

def count_media_reports(media_type):
    cursor.execute(f'''
        SELECT media_id, COUNT(report_media_id) AS total_reports
        FROM reports_media
        WHERE media_type = %s AND report_status = 'ALERT'
        GROUP BY media_id''', (media_type,))
    result = cursor.fetchall()
    return result

def fetch_recent_media_ids(media_type):
    cursor.execute(f'SELECT media_id, added_time FROM `{media_type}` WHERE added_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)')
    result = cursor.fetchall()
    return result
