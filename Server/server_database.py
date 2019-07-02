import sqlite3
from os import path, makedirs
from configparser import ConfigParser
from os.path import isfile
from hashlib import sha256
from random import choice
from string import ascii_letters, punctuation, digits

class SqlInterface:
    def __init__(self, dbname=None):
        self.connection = None
        self.cursor = None
        if dbname:
            self.create_database(dbname)
    
    def connect(self, dbname):
        try:
            self.connection = sqlite3.connect(dbname, check_same_thread=False)
            self.cursor = self.connection.cursor()
            return True
        except sqlite3.Error as e:
            print('Error to open database.')
            self.close()
            return False
    
    def create_database(self, dbname):
        if not self.connect(dbname):
            self.connect(dbname)
            self.close()
            return True
        else:
            self.connect(dbname)
            return False
    
    def create_table(self, table_name, table_columns):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS %s (%s);' % (table_name, table_columns))
        self.connection.commit()
    
    def delete_table(self, table_name):
        self.cursor.execute('DROP TABLE %s' % table_name)
        self.connection.commit()
    
    def get(self, table_name, columns, limit=None):
        self.cursor.execute('SELECT %s from %s;' % (columns, table_name))
        data = self.cursor.fetchall()
        return [elt[0] for elt in data]
    
    def table_list(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        data = self.cursor.fetchall()
        return [elt[0] for elt in data]

    def table_exists(self, table_name):
        pass

    def fetch_all(self, table_name):
        self.cursor.execute("SELECT * FROM %s;" % table_name)
        data = self.cursor.fetchall()
        return [list(elt) for elt in data]

    def find(self, table_name, parameter, value):
        query = 'SELECT * FROM %s WHERE "%s" = ?;' % (table_name, parameter)
        self.cursor.execute(query, [value])
        data = self.cursor.fetchall()
        return [list(elt) for elt in data]
    
    def insert(self, table_name, columns, data):
        query_val = "?,"*len(data)
        query = 'INSERT INTO %s (%s) VALUES (%s);' % (table_name, columns, query_val[:len(query_val)-1])
        self.cursor.execute(query, data)
        self.connection.commit()
    
    def update(self, table_name, columns, values):
        cols = columns.replace(" ", "").split(",")
        query = 'UPDATE %s SET %s WHERE "id" = ?;' % (table_name, ' = ?, '.join(cols) + ' = ?')
        self.cursor.execute(query, values)
        self.connection.commit()
    
    def delete(self, table_name, id):
        query = 'DELETE FROM %s WHERE id = ?;' % table_name
        self.cursor.execute(query, str(id))
        self.connection.commit()
    
    def query(self, sql):
        self.cursor.execute(sql)
        self.connection.commit()
    
    def close(self):
        if self.connection:
            self.connection.commit()
            self.cursor.close()
            self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, ex_type, ex_value, traceback):
        self.close()

class ServerDatabase(SqlInterface):
    def __init__(self):
        self.data_path = 'Data/'
        self.database_path = self.data_path + "server_database.db"

        if not path.exists(self.data_path):
            makedirs(self.data_path)

        self.create_database(self.database_path)
        self.create_table("users", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT, password TEXT, verification INTEGER, invite_word TEXT")
        self.create_table("invite_keys", "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT, invite_hash TEXT")

    def __generate_key(self, length):
        return ''.join(choice(ascii_letters + digits + punctuation) for i in range(length))

    def is_user_already_exist(self, username):
        return True if len(self.find("users", "username", username)) > 0 else False
    
    def is_user_verificated(self, username):
        return True if self.find("users", "username", username)[0][3] == 1 else False
    
    def is_passwords_match(self, username, password_hash):
        return True if password_hash in self.find("users", "username", username)[0] else False
        
    def is_invite_hash_match(self, username, invite_hash):
        return True if self.find("invite_keys", "username", username)[0][2] == invite_hash else False
    
    def get_user_id(self, table_name, username):
        return self.find(table_name, "username", username)[0][0]
    
    def make_hash(self, string):
        return sha256(string.encode('utf-8')).hexdigest()
    
    def add_user_without_verification(self, username, password):
        self.insert("users", "username, password, verification", (username, password, True))
    
    def add_user_with_verification(self, username, password):
        word = self.__generate_key(32)
        self.insert("users", "username, password, verification, invite_word", (username, password, False, word))
        invite_hash = sha256(word.encode('utf-8')).hexdigest()
        self.insert("invite_keys", "username, invite_hash", (username, invite_hash))
    
    def verificate_user(self, username, invite_hash):
        if self.is_invite_hash_match(username, invite_hash):
            self.update("users", "verification", [True, self.get_user_id("users", username)])
            self.update("invite_keys", "invite_hash", ['VERIFICATED', self.get_user_id("invite_keys", username)])
            return True
        else:
            return False

class ServerSettings:
    def __init__(self):
        self.config = ConfigParser()
        self.config_path = 'config.ini'
        self.server_ip = '0.0.0.0'
        self.server_port = 9191
        self.maximum_users = 100
        self.enable_password = False
        self.enable_whitelist = False
        self.whitelist = []
        self.server_rooms = ['guest' ,'proggers', 'russian', 'pole']

        if isfile(self.config_path):
            self.load()
        else:
            self.save()
    
    def save(self):
        self.config["NET"] = {"server_ip" : self.server_ip, "server_port" : self.server_port}
        self.config["SETTINGS"] = {"max_slots" : self.maximum_users, "enable_password" : self.enable_password, "server_password" : self.server_password, "enable_whitelist" : self.enable_whitelist,
                                   "white_list" : self.whitelist, "rooms" : self.server_rooms}

        with open(self.config_path, "w") as config_file:
            self.config.write(config_file)
    
    def update_password(self, new_password):
        self.server_password = sha256(new_password.encode('utf-8')).hexdigest()
        self.save()
    
    def getlist(self, string):
        return (''.join(i for i in string if not i in ['[', ']', '\'', ' '])).split(',')

    def load(self):
        self.config.read(self.config_path)
        self.server_ip = self.config["NET"].get("server_ip")
        self.server_port = self.config["NET"].getint("server_port")
        self.maximum_users = self.config["SETTINGS"].getint("max_slots")
        self.enable_password = self.config["SETTINGS"].getboolean('enable_password')
        self.enable_whitelist = self.config["SETTINGS"].getboolean('enable_whitelist')
        self.whitelist = self.getlist(self.config["SETTINGS"].get('white_list'))
        self.server_rooms = self.getlist(self.config["SETTINGS"].get('rooms'))