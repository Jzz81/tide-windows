#-------------------------------------------------------------------------------
# Name:        Database.py
# Purpose:     Hold code to do all database works
#
# Author:      Joos Dominicus
#
# Created:     01-05-2014
#-------------------------------------------------------------------------------
import os
import shutil
import sqlite3

class DatabaseError(Exception):
    pass

class Database():
    def __init__(self, parent, network_database_directory, local_database_directory, database_name):
        self.parent  = parent
        if network_database_directory.endswith("\\"):
            self.network_database_path = "{dir}{file}".format(dir=network_database_directory, file=database_name)
        else:
            self.network_database_path = "{dir}\{file}".format(dir=network_database_directory, file=database_name)

        if local_database_directory.endswith("\\"):
            self.local_database_path = "{dir}{file}".format(dir=local_database_directory, file=database_name)
        else:
            self.local_database_path = "{dir}\{file}".format(dir=local_database_directory, file=database_name)

        print self.local_database_path
        print self.network_database_path

        self.connected_to_gna_network = self.__gna_network_connection_check()

        #NO CONNECTION AND NO LOCAL DATABASE
        if not self.connected_to_gna_network and not self.__local_database_exists():
            raise DatabaseError("No database found; not connected to network and no local database present")
        #CONNECTION, BUT NO NETWORK DATABASE AND NO LOCAL DATABASE
        elif self.connected_to_gna_network and not self.__network_database_exists() and not self.__local_database_exists():
            raise DatabaseError("No database found; connected to network, but no network and no local database present")
        #DATABASE ON THE NETWORK, BUT NOT LOCALLY
        elif self.__network_database_exists() and not self.__local_database_exists():
            self.__copy_network_to_local()
        #DATABASE LOCAL, BUT NOT ON THE NETWORK
        elif self.__local_database_exists() and not self.__network_database_exists():
            self.__copy_local_to_network()

        self.tidal_points = self.__get_tidal_points()
        print self.tidal_points


    def __get_tidal_points(self):
        '''get all tidal points from the database'''
        self.__open_db_connection()
        table_name = "TDP_Names"
        sql = "SELECT * FROM {table} WHERE table_exists='1';".format(table=table_name)
        self.__execute_sql(sql)
        result = {}
        for r in self.__cur:
            result[r[0]] = r[1]
        self.__conn.close()
        return result

    def __execute_sql(self, sql, return_cursor=False):
        '''executes a sql string and commits. If cursor is set, it returns a cursor'''
        if return_cursor == False:
            self.__cur.execute(sql)
            self.__conn.commit()
        else:
            c = self.__conn.cursor()
            c.execute(sql)
            self.__conn.commit()
            return c

    def __open_db_connection(self):
        '''opens a connection to the database'''
        self.__conn = sqlite3.connect(self.local_database_path)
        self.__cur = self.__conn.cursor()

    def __copy_local_to_network(self):
        '''copies the local database to the network'''
        shutil.copyfile(self.local_database_path, self.network_database_path)

    def __copy_network_to_local(self):
        '''copies the network database to the local path'''
        shutil.copyfile(self.network_database_path, self.local_database_path)

    def __network_database_exists(self):
        '''checks if the network database exists'''
        return os.path.isfile(self.network_database_path)

    def __local_database_exists(self):
        '''checks if the local database exists'''
        return os.path.isfile(self.local_database_path)

    def __gna_network_connection_check(self):
        '''checks if the gna network is connected'''
        #HARDCODED PATH, TO PREVENT MISTAKES. IT IS TRIVIAL THAT THE SKRGNA NETWORK IS CHECKED HERE
        return os.path.exists(r"\\srkgna\personal")

def main():
##    print internet_on()
    dir = "{0}\Wespy".format(os.environ["LOCALAPPDATA"])
    local_db_path = dir
    if not os.path.exists(local_db_path):
        os.makedirs(local_db_path)
#Y:\databaseHVL\Wespy
    nw_db_path = r"\\srkgna\personal\GNA\databaseHVL\Wespy"

    db_name = "WespyDB.db3"

    s = object

    db = Database(s, nw_db_path, local_db_path, db_name)

if __name__ == '__main__':
    main()
