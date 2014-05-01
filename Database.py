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
    def __init__(self, parent, network_database_path, local_database_path, database_name):
        self.parent  = parent
        self.network_database_path = network_database_path
        self.local_database_path = local_database_path
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


    def __get_tidal_points(self):
        '''get all tidal points from the database'''
        self.__open_db_connection()
        table_name = self.__tables["tidal_point_names"]["name"]
        sql = "SELECT * FROM {table} WHERE table_exists='1';".format(table=table_name)
        self.__execute_sql(sql)
        result = {}
        for r in self.__cur:
            result[r[0]] = r[1]
        self.__conn.close()
        return result

    def __open_db_connection(self):
        '''opens a connection to the database'''
        self.__conn = sqlite3.connect(self.local_database_path)
        self.__cur = self.__conn.cursor()

    def __copy_local_to_network():
        '''copies the local database to the network'''
        shutil.copyfile(self.local_database_path, self.network_database_path)

    def __copy_network_to_local():
        '''copies the network database to the local path'''
        shutil.copyfile(self.network_database_path, self.local_database_path)

    def __network_database_exists(self):
        '''checks if the network database exists'''
        return os.path.exists(self.network_database_path)

    def __local_database_exists(self):
        '''checks if the local database exists'''
        return os.path.exists(self.local_database_path)

    def __gna_network_connection_check():
        '''checks if the gna network is connected'''
        #HARDCODED PATH, TO PREVENT MISTAKES. IT IS TRIVIAL THAT THE SKRGNA NETWORK IS CHECKED HERE
        return os.path.exists(r"\\srkgna\personal")

def main():
##    print internet_on()
    dir = "{0}\jzz_pWesp".format(os.environ["LOCALAPPDATA"])
    csv_repo_path = dir + "\\tidal_data_repo"
    if not os.path.exists(csv_repo_path):
        os.makedirs(csv_repo_path)

if __name__ == '__main__':
    main()
