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
import glob
import datetime
import time
try:
    import pyodbc
except ImportError:
    raise ImportError("The module 'pyodbc' is not installed on your system")
import numpy as np

class DatabaseError(Exception):
    pass

class Database():
    def __init__(self, parent, network_database_directory, local_database_directory):
        self.parent  = parent

        self.parent.status.set("initializing database...")

        self.network_database_dir = self.__add_slash_to_dir(network_database_directory)
        self.local_database_dir = self.__add_slash_to_dir(local_database_directory)

        self.cross_check_program_databases()
        self.get_numpy_arrays()
        self.tidal_points = self.__get_tidal_points()

    def __get_tidal_points(self):
        '''get all tidal points from the database'''
        self.__open_db_connection()
        table_name = "TDP_Names"
        sql = "SELECT * FROM {table};".format(table=table_name)
        self.__execute_sql(sql)
        result = {}
        for r in self.__cur:
            result[r[1]] = r[0]
        self.__conn.close()
        return result

    def __monthdelta(self, date, delta):
        '''returns the date with an offset of delta months (1st day of month)'''
        m = (date.month+delta) % 12
        y = date.year + ((date.month)+delta) // 12
        if m == 0:
            m = 12
        d = 1
        return datetime.datetime(day=d, month=m, year=y)
        return date.replace(day=d,month=m, year=y)

    def get_numpy_arrays(self):
        '''gets all the tables into numpy arrays and store them in a dict'''
        self.tidal_data_arrays = {}
        db_rise_dir = self.__make_correct_path("tidal_rise",self.local_database_dir)
        #determine which year of data we need first. Data is taken from 1 month before
        #to 1 year after the current date
        first_date = self.__monthdelta(datetime.datetime.now(), -1)
        last_date = self.__monthdelta(datetime.datetime.now(), 12)
        #get paths of appropriate databases:
        db_rise_path = []
        for i in range(first_date.year, last_date.year + 1):
            db_rise_path.append("{dir}{y}.db3".format(dir=db_rise_dir, y=i))
        #loop databases:
        for path in db_rise_path:
            if not os.path.isfile(path):
                continue
            self.__open_db_connection(path)
            #get all tables:
            sql = "SELECT name FROM sqlite_master WHERE type='table'";
            tables= self.__execute_sql(sql, return_cursor=True)
            #loop tables in database:
            for table in tables:
                sql = "SELECT * FROM {table} WHERE datetime >= {first} AND datetime <= {last};"
                sql = sql.format(table=table[0],
                                 first=self.__since_epoch(first_date),
                                 last=self.__since_epoch(last_date))
                self.__execute_sql(sql)
                self.parent.status.set("loading tidal data for {table}".format(table=table[0]))
                data = list(self.__cur)
                n = np.array(data)

                if table[0] in self.tidal_data_arrays.keys():
                    #vstack numpy array to last
                    self.tidal_data_arrays[table[0]] = np.vstack((self.tidal_data_arrays[table[0]],n))
                else:
                    self.tidal_data_arrays[table[0]] = n
        self.__check_existence_of_tidal_data()
        self.parent.status.set("done!")

    def __check_existence_of_tidal_data(self):
        '''checks the existence of a tidal data point'''
        self.__open_db_connection()
        table_name = "TDP_Names"
        #set all data_exists fields to 0:
        self.__execute_sql("UPDATE {table} SET data_exists='0';".format(table=table_name))
        cursor = self.__execute_sql("SELECT id FROM {table};".format(table=table_name), return_cursor=True)
        for r in cursor:
            TDP_table_name = "TDP_{id}_Tidal_Data".format(id=r[0])
            if TDP_table_name in self.tidal_data_arrays.keys():
                self.__execute_sql("UPDATE {table} SET data_exists='1' WHERE id={id};".format(table=table_name, id=r[0]))

    def __add_slash_to_dir(self, dir):
        '''makes sure there is a slash at the end of dir'''
        if dir.endswith("\\"):
            return dir
        else:
            return dir + "\\"

    def import_access_database(self, access_database_path):
        """
        import an access database with tidal data

        connects to a given access database and imports the data in that
        database. The database must contain a table for every tidal point with
        the name of that tidal point as table name and have 2 columns:
            datetime (must contain datetime values)
            rise (must contain rise values)
        The database will be converted to a new sqlite database with the same
        columns.
        Datatime values will be converted into seconds since epoch (1-1-1970)
        Rise values will be rounded to 1 decimal.

        In the new database, an extra table will be created, holding
        info about the first and the last dates that the database holds information
        about. If the new data overlaps old data in any way, it will delete the
        old data.

        New database will be stored locally, and when finished, copied to network.
        """
        self.__transfer_tables_and_data(access_database_path)


    def __open_ADO_connection(self, path):
        '''open an ado connection with db'''
        odbc_conn_str = 'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + path + ';Trusted_Connection=yes'
        self.__ADO_conn = pyodbc.connect(odbc_conn_str)

    def __get_tidal_data_from_ACDB(self, table):
        '''Get tidal data from the access database'''
        sql= "SELECT * FROM {table} ORDER BY datetime;".format(table=table)
        cur = self.__ADO_conn.cursor()
        cur.execute(sql)
        data = list(cur)
        return data

    def __get_tidal_points_from_ACDB(self):
        '''Get table names from access db'''
        sql = "SELECT * FROM MSysObjects WHERE Type=1 AND Flags=0"
        cur = self.__ADO_conn.cursor()
        data=[]
        for row in cur.execute(sql):
            data.append(row.Name)
        return data

    def __transfer_tables_and_data(self, access_database_path):
        '''transfer the tables and all the data from access db (db1) to sqlite db(db2)'''
        print "getting table names..."
        self.__open_ADO_connection(access_database_path)
        tables = self.__get_tidal_points_from_ACDB()
        print "have tables names."
        for table in tables:
            data = self.__get_tidal_data_from_ACDB(table)
            self.__insert_tidal_data_into_db(data,table)
        self.__ADO_conn.close()

    def __since_epoch(self, dt):
        '''returns the seconds since epoch of a given datetime'''
        return (dt - datetime.datetime(1970, 1,1)).total_seconds()

    def __insert_tidal_data_into_db(self, data, table):
        '''Function to insert data (list) into sqlite db and table'''
        #get id of tidal point (stored in program database)
        id = self.__store_tidal_point_name(table)
        print "inserting {0} into database with id of {1}".format(table, id)
        year_of_data = None

        for i in range(0, len(data)):
            data[i][0] = self.__since_epoch(data[i][0])
            data[i][1] = round(data[i][1],1)
            if time.strftime("%Y", time.gmtime(data[i][0])) != year_of_data:
                if year_of_data != None:
                    #a year has been added, commit changes and close connection
                    self.__conn.commit()
                    self.__conn.close()
                #get year of data point
                year_of_data = time.strftime("%Y", time.gmtime(data[i][0]))
                print "found data for", year_of_data
                #find tidal database of this year (create if does not exists)
                dir = self.__make_correct_path("tidal_rise", self.local_database_dir)
                path = "{dir}{year}.db3".format(dir=dir, year=year_of_data)
                self.__open_db_connection(path)
                #find table of this tidal point id in database (create if it does not exists)
                table_name = "TDP_{id}_Tidal_Data".format(id=id)
                self.__execute_sql("CREATE TABLE IF NOT EXISTS {table} (datetime real, rise real);".format(table=table_name))
                #get current table data:
                self.__execute_sql("SELECT * FROM {table};".format(table=table_name))
                current_table_data = list(self.__cur)
                if len(current_table_data) > 0:
                    current_data = [x[0] for x in current_table_data]
                    max_datum = max(current_data)
                else:
                    current_data = []
                    max_datum = 0

            if data[i][0] < max_datum:
                try:
                    listindex = current_data.index(data[i][0])
                except:
                    listindex = None
                #datetime to insert is in the range currently in the database
                if listindex == None:
                    print "datetime not found"
                    sql = "INSERT INTO {table} (datetime, rise) VALUES ('{dt}', '{rise}');".format(table=table_name, dt=data[i][0], rise=data[i][1])
                    self.__execute_sql(sql, commit=False)
                elif data[i][1] != current_table_data[listindex][1]:
                    print "datetime found with different rise; updating"
                    sql = "UPDATE {table} SET rise='{rise}' WHERE datetime='{dt}';".format(table=table_name, dt=data[i][0], rise=data[i][1])
                    self.__execute_sql(sql, commit=False)
            else:
                sql = "INSERT INTO {table} (datetime, rise) VALUES ('{dt}', '{rise}');".format(table=table_name, dt=data[i][0], rise=data[i][1])
                self.__execute_sql(sql, commit=False)

##            if i > 10000:
##                self.__conn.commit()
##                self.__conn.close()
##                break
        #don't forget to commit the last entries:
        self.__conn.commit()
        self.__conn.close()

    def __store_tidal_point_name(self, table):
        '''store the name of the tidal point in the TDP_Names table and return the id'''
        self.__open_db_connection()
        table_name = "TDP_Names"
        #check if the name already exists:
        self.__execute_sql("SELECT * FROM {table} WHERE name='{name}';".format(table=table_name, name=table))
        result = None
        for r in self.__cur:
            result = r[1]
        #insert if name does not exist:
        if result == None:
            self.__execute_sql("INSERT INTO {table} (name) VALUES ('{name}');".format(table=table_name, name=table))
            result = self.__cur.lastrowid
        self.__conn.close()
        return result

    def cross_check_program_databases(self):
        """
        check the local and network database with program data

        Checks if the local and network databases are present, and copies the
        other if one is missing, or the moddate of one is newer, to keep them
        both up-to-date.

        Network database is not overwritten, but a new database is added with a
         higher number, to prevent problems when more machines try to implement
        new databases on the network. Old network databases are cleaned up, if
        more then 5 are present.

        will raise a DatabaseError if there is no database available (either
        no local and no network, or no local and no network connection) or no
        modification date could be established for both the local and the
        network database.
        """
        print "check for GNA network...",
        self.connected_to_gna_network = self.__gna_network_connection_check()
        if self.connected_to_gna_network:
            print "GNA network connection present"
            print "getting latest network database file...",
            self.network_program_database_path = self.__get_network_db_path(which_database="program")
        else:
            print "no GNA network connection present"
            self.parent.status.set("not connected to GNA network, run local")
            self.network_program_database_path = None

        if self.network_program_database_path != None:
            print "got it!"
            print "getting last modification date of network database...",
            try:
                self.network_database_moddate = self.__get_network_db_moddate()
                self.network_database_moddate_string = time.strftime("%d-%m-%y_%H%M", time.localtime(self.network_database_moddate))
                print "got it!"
            except:
                self.network_database_moddate = None
                print "failed!"
        else:
            print "no network database file"

        print "getting latest local database file...",
        self.local_program_database_path = self.__get_local_db_path(which_database="program")
        if self.local_program_database_path != None:
            print "got it!"
            print "getting last modification date of local database...",
            try:
                self.local_database_moddate  = self.__get_local_db_moddate()
                self.local_database_moddate_string = time.strftime("%d-%m-%y_%H%M", time.localtime(self.local_database_moddate))
                print "got it!"
            except:
                self.local_database_moddate = None
                print "failed!"
        else:
            print "no local database file"

        #NO CONNECTION AND NO LOCAL DATABASE
        if not self.connected_to_gna_network and self.local_program_database_path == None:
            self.parent.status.set("No database")
            raise DatabaseError("No database found; not connected to network and no local database present")
        #CONNECTION, BUT NO NETWORK DATABASE AND NO LOCAL DATABASE
        elif self.connected_to_gna_network and self.network_program_database_path == None and self.local_program_database_path == None:
            self.parent.status.set("No database")
            raise DatabaseError("No database found; connected to network, but no network and no local database present")
        #DATABASE ON THE NETWORK, BUT NOT LOCALLY
        elif (self.connected_to_gna_network and self.network_program_database_path != None and self.local_program_database_path == None):
            print "no local database found"
            self.parent.status.set("no local database, copying from network...")
            self.__copy_network_to_local(which_database="program")
        #DATABASE LOCAL, BUT NOT ON THE NETWORK
        elif self.connected_to_gna_network and self.network_program_database_path == None and self.local_program_database_path != None:
            print "no network database found"
            self.parent.status.set("no network database, copying from local...")
            self.__copy_local_to_network(which_database="program")
        #BOTH DATABASES EXIST, BUT NETWORK HOLDS A NEWER ONE:
        elif self.connected_to_gna_network and self.__network_db_is_newer():
            print "network holds a newer database"
            self.parent.status.set("local database outdated, copying newer version from network...")
            self.__copy_network_to_local(which_database="program")
        #BOTH DATABASES EXIST, BUT LOCAL HOLDS A NEWER ONE:
        elif self.connected_to_gna_network and self.__local_db_is_newer():
            print "local holds a newer database"
            self.parent.status.set("network database outdated, copying newer version from local...")
            self.__copy_local_to_network(which_database="program")
        #CONNECTION EXISTS, BOTH DATABASES ARE EQUAL:
        elif self.connected_to_gna_network:
            print "both databases are of equal date, no copy required"
        #NO CONNECTION, BUT LOCAL DATABASE EXISTS:
        elif not self.connected_to_gna_network and self.local_program_database_path != None:
            print "no network connection, found a local database"

        '''
        TODO: CLEAN DB FILES BOTH LOCAL AND NETWORK IF MORE THEN 5 EXISTS
        '''

    def __execute_sql(self, sql, return_cursor=False, commit=True):
        '''executes a sql string and commits. If cursor is set, it returns a cursor'''
        if return_cursor == False:
            self.__cur.execute(sql)
            if commit:
                self.__conn.commit()
        else:
            c = self.__conn.cursor()
            c.execute(sql)
            if commit:
                self.__conn.commit()
            return c

    def __open_db_connection(self, path=None):
        '''opens a connection to the database. If path is not set, it uses
        the local database'''
        if path == None:
            path = self.local_program_database_path
        self.__conn = sqlite3.connect(path)
        self.__cur = self.__conn.cursor()

    def __copy_local_to_network(self, which_database):
        '''copies the local database to the network'''
        print "copy local to network"
        dir = self.__make_correct_path(which_database, self.network_database_dir)
        savepath = "{dir}WespyDB_{mdate}.db3".format(dir=dir, mdate=self.local_database_moddate_string)
        shutil.copyfile(self.local_program_database_path, savepath)
        self.network_program_database_path = savepath

    def __copy_network_to_local(self, which_database):
        '''copies the network database to the local path'''
        print "copy network to local"
        dir = self.__make_correct_path(which_database, self.local_database_dir)
        savepath = "{dir}WespyDB_{mdate}.db3".format(dir=dir, mdate=self.network_database_moddate_string)
        shutil.copyfile(self.network_program_database_path, savepath)
        self.local_program_database_path = savepath

    def __get_network_db_moddate(self):
        self.__open_db_connection(self.network_program_database_path)
        self.__execute_sql("SELECT * FROM AUX_Info;")
        for r in self.__cur:
            network_moddate = r[0]
        self.__conn.close()
        return network_moddate

    def __get_local_db_moddate(self):
        self.__open_db_connection()
        self.__execute_sql("SELECT * FROM AUX_Info;")
        for r in self.__cur:
            network_moddate = r[0]
        self.__conn.close()
        return network_moddate

    def __network_db_is_newer(self):
        '''checks if the network db is newer then the local db'''
        if self.local_database_moddate == None and self.network_database_moddate == None:
            raise DatabaseError("have no valid modification dates for both local and network databases")
        elif self.network_database_moddate == None:
            print "could not establish the network database moddate, assuming local is newer"
            return False
        elif self.local_database_moddate == None:
            print "could not establish the local database moddate, assuming network is newer"
            return True
        else:
            return round(self.network_database_moddate - self.local_database_moddate, 2) > 0

    def __local_db_is_newer(self):
        '''checks if the local db is newer then the network db'''
        if self.local_database_moddate == None and self.network_database_moddate == None:
            raise DatabaseError("have no valid modification dates for both local and network databases")
        elif self.local_database_moddate == None:
            print "could not establish the local database moddate, assuming network is newer"
            return False
        elif self.network_database_moddate == None:
            print "could not establish the network database moddate, assuming local is newer"
            return True
        else:
            return round(self.local_database_moddate - self.network_database_moddate, 2) > 0

    def __make_correct_path(self, which_database, dir):
        if which_database == "program":
            db_dir = dir + "program_data\\"
        elif which_database == "tidal_rise":
            db_dir = dir + "tidal_data\\rise_values\\"
        elif which_database == "tidal_hw_lw":
            db_dir = dir + "tidal_data\\hw_lw\\"
        self.__make_dir_if_not_exists(db_dir)
        return db_dir

    def __get_network_db_path(self, which_database):
        '''will return the network db full path.

        which_database should be "program", "tidal_rise" or "tidal_hw_lw"
        '''
        path = self.__make_correct_path(which_database, self.network_database_dir)
        return self.__get_db_path(path)

    def __get_local_db_path(self, which_database):
        '''will return the local db full path.

        which_database should be "program", "tidal_rise" or "tidal_hw_lw"
        '''
        path = self.__make_correct_path(which_database, self.local_database_dir)
        return self.__get_db_path(path)

    def __get_db_path(self, dir):
        '''gets the newest db3 file from dir'''
        s = dir + "*.db3"
        try:
            f = max(glob.iglob(s), key=os.path.getmtime)
        except:
            return None
        return f

    def __make_dir_if_not_exists(self, dir):
        '''creates the dir (including subdirs) if it does not exists'''
        if not os.path.exists(dir):
            os.makedirs(dir)

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
    nw_db_path = r"\\srkgna\personal\GNA\databaseHVL\Wespy"

    db_name = "WespyDB.db3"

    s = object

    db = Database(s, nw_db_path, local_db_path)
##    db.import_access_database(r"Z:\Joos\programma Patrick\python\Jaartij-2014.accdb")
##    db.get_numpy_arrays()

if __name__ == '__main__':
    main()
