'''
Created on 27 feb. 2014

@author: Joos
'''
try:
    import pyodbc
except ImportError:
    raise ImportError("The module 'pyodbc' is not installed on your system")
import sqlite3
import os
import numpy
import pandas
import pandas.io.sql as panda_sql
import datetime

class AccessSQLiteConvert():
    '''
    Class that will convert the given Access Database to a SQLite database.
    By default, the class will create a SQLite database in the TEMP directory.
    If the SQLite database already exists it will check the moddate of the Access DB and compare it with a stored value in the SQLite DB.
    If the moddate is the same as the stored date, it will not convert.
    The method 'GetSQLitePath' will return the correct path of the SQLite DB.
    '''


    def __init__(self, SQLitePath):
        '''
        Constructor
        '''
        self.__SQLite_path = SQLitePath
        self.AccDBPath = self.__get_acc_db_path()
        self.__tables = {
            "tidal_point_names":
                {
                "name":"TDP_Names",
                "columns":["id integer primary key autoincrement", "name text", "table_exists int"]
                },
            "aux_info":
                {
                "name":"AUX_Info",
                "columns":["access_db_moddate real", "access_db_path text"]
                }
            }
        self.__make_DB()
        self.tidal_points = self.__get_tidal_points()
        self.__fill_mem_db() #DEBUG
##        self.__fill_tidal_dict() #DEBUG
        self.__fill_panda_series()


    def __fill_panda_series(self):
        '''create panda series with tidal data'''
        self.memory_tidal_dict = {}
        tidal_tables = self.__get_existing_tidal_tables()
        self.__open_db_connection()
        for name, table_name in tidal_tables.iteritems():
            print "loading tidal data of:", name
            sql =  "SELECT * FROM {table} ORDER BY datetime;".format(table=table_name)
            tf = panda_sql.read_sql(sql, con=self.__conn)#, index_col="datetime")
##            self.__execute_sql(sql)
##            dates = []
##            rises = []
##            for r in self.__cur:
##                dates.append(r[0])
##                rises.append(r[1])
##            ts = pandas.Series(rises, index=pandas.to_datetime(dates))
##            ts.sort()
            self.memory_tidal_dict[table_name] = tf

    def __make_datetime_from_db_val(self, time):
        '''returns a datetime value'''
        return datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")


    def __fill_tidal_dict(self):
        '''create a dictionary with tidal data to keep in memory'''
        self.memory_tidal_dict = {}
        tidal_tables = self.__get_existing_tidal_tables()
        self.__open_db_connection()
        for name, table_name in tidal_tables.iteritems():
            print "loading tidal data of:", name
            sql =  "SELECT * FROM {table};".format(table=table_name)
            self.__execute_sql(sql)
            self.memory_tidal_dict[table_name] = list(self.__cur)


    def __fill_mem_db(self):
        '''create memory database with tidal data'''
        self.memory_tidal_database = sqlite3.connect(":memory:")
        return
        c = self.memory_tidal_database.cursor()
        c.execute("attach database '" + self.__SQLite_path + "' as attached_db")
        dumptables = self.__get_existing_tidal_tables()
        for name, table_to_dump in dumptables.iteritems():
            c.execute("select sql from attached_db.sqlite_master "
                       "where type='table' and name='" + table_to_dump + "'")
            sql_create_table = c.fetchone()[0]
            sql_create_table = sql_create_table
            c.execute(sql_create_table);
            c.execute("insert into " + table_to_dump +
                       " select * from attached_db." + table_to_dump)
            self.memory_tidal_database.commit()
        c.execute("detach database attached_db")

    def __get_existing_tidal_tables(self):
        '''retreive all table names that exist'''
        self.__open_db_connection()
        table_name = self.__tables["tidal_point_names"]["name"]
        self.__execute_sql("SELECT * FROM {table} WHERE table_exists=1;".format(table=table_name))
        tidal_tables = {}
        for table in self.__cur:
            id = table[0]
            name = table[1]
            tidal_tables[name] = "TDP_{id}_Tidal_Data".format(id=id)
        self.__conn.close()
        return tidal_tables


    def __open_db_connection(self):
        '''opens a connection to the database'''
        self.__conn = sqlite3.connect(self.__SQLite_path)
        self.__cur = self.__conn.cursor()

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

    def __create_table(self, name, columns):
        '''creates a table if it does not exits'''
        sql = "CREATE TABLE IF NOT EXISTS {table} (".format(table=name)
        sql = sql + ", ".join(columns)
        sql = sql + ");"
        self.__execute_sql(sql)

    def __make_DB(self):
        '''create all tables needed for tresholds'''
        self.__open_db_connection()
        for key in self.__tables:
            name = self.__tables[key]["name"]
            columns = self.__tables[key]["columns"]
            self.__create_table(name, columns)
        self.__conn.close()

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

    def __get_acc_db_path(self):
        '''tries to get the access db path from the sqlite db and returns the path (validated)'''
        self.__open_db_connection()
        p = ""
        try:
            self.__execute_sql("SELECT access_db_path FROM AUX_Info")
            for row in self.__cur:
                p =  row[0]
        except:
            pass
        if self.__file_exists(p):
            self.__conn.close()
            return p
        else:
            self.__execute_sql("DELETE FROM AUX_Info;")
            #try, because it is possible that the table does not exist.
            try:
                self.__execute_sql("UPDATE TDP_Names SET table_exists=0;")
            except:
                pass
            self.__conn.close()
            return ""

    def __open_ADO_connection(self):
        """open an ado connection with db"""
        odbc_conn_str = 'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + self.AccDBPath + ';Trusted_Connection=yes'
        self.__ADO_conn = pyodbc.connect(odbc_conn_str)

    def __get_tidal_data_from_ACDB(self, table):
        """Get tidal data from the access database"""
        sql="select * from "+table
        self.__open_ADO_connection()
        cur = self.__ADO_conn.cursor()
        cur.execute(sql)
        data = list(cur)
        self.__ADO_conn.close()
        return data

    def __get_tidal_points_from_ACDB(self):
        """Get table names from access db"""
        sql = "SELECT * FROM MSysObjects WHERE Type=1 AND Flags=0"
        self.__open_ADO_connection()
        cur = self.__ADO_conn.cursor()
        data=[]
        for row in cur.execute(sql):
            data.append(row.Name)
        self.__ADO_conn.close()
        return data

    def __create_aux_info_table(self):
        """create a table in db with only one column and one row, store moddate in it"""
        self.__open_db_connection()
        table_name = self.__tables["aux_info"]["name"]
        col = ", ".join(self.__tables["aux_info"]["columns"])
        self.__execute_sql("CREATE TABLE IF NOT EXISTS {table} ({col});".format(table=table_name, col=col))
        self.__execute_sql("DELETE FROM {table};".format(table=table_name))
        sql = "INSERT INTO {table}(access_db_moddate, access_db_path) values({moddate}, '{path}');".format(table=table_name, moddate=os.path.getmtime(self.AccDBPath), path=self.AccDBPath)
        self.__execute_sql(sql)
        self.__conn.close()

    def __store_tidal_point_name(self, table):
        """store the name of the tidal point in the TDP_Names table and return the id"""
        self.__open_db_connection()
        table_name = self.__tables["tidal_point_names"]["name"]
        #check if the name already exists:
        self.__execute_sql("SELECT * FROM {table} WHERE name='{name}';".format(table=table_name, name=table))
        result = None
        for r in self.__cur:
            result = r[0]
        #insert if name does not exist:
        if result == None:
            self.__execute_sql("INSERT INTO {table} (name, table_exists) VALUES ('{name}', 1);".format(table=table_name, name=table))
            result = self.__cur.lastrowid
        else:
            self.__execute_sql("UPDATE {table} SET table_exists = 1 WHERE id={id};".format(table=table_name,id=result))
        self.__conn.close()
        return result

    def __transfer_tables_and_data(self):
        """transfer the tables and all the data from access db (db1) to sqlite db(db2)"""
        print "getting table names..."
        tables = self.__get_tidal_points_from_ACDB()
        print "have tables names."
        for table in tables:
            data = self.__get_tidal_data_from_ACDB(table)
            self.__insert_tidal_data_into_db(data,table)
        self.__create_aux_info_table()

    def __insert_tidal_data_into_db(self, data, table):
        """Function to insert data (list) into sqlite db and table"""
        id = self.__store_tidal_point_name(table)
        print "inserting {0} into database with id of {1}".format(table, id)
        self.__open_db_connection()
        #tidal data table names are formatted like: TDP_xxx_Tidal_Data
        self.__execute_sql("CREATE TABLE TDP_{id}_Tidal_Data (datetime datetime, rise real);".format(id=id))
        c = self.__conn.cursor()
        sql = "INSERT INTO TDP_{id}_Tidal_Data VALUES (?,?);".format(id=id)
        c.executemany(sql, data)
        self.__conn.commit()
        self.__conn.close()

    def __file_exists(self, path):
        return os.path.isfile(path)

    def __db_is_right_version(self):
        """returns true is moddate is stored in AUX_info"""
        self.__open_db_connection()
        B = False
        self.__execute_sql("SELECT access_db_moddate FROM AUX_Info")
        try:
            for row in self.__cur:
                B = abs(os.path.getmtime(self.AccDBPath) - row[0]) < 0.01
        except:
            print "no moddate found"
            pass
        if B:
            return True
        else:
            return False
        self.__conn.close()

    def __remove_tidal_data_tables(self):
        """removes the tidal data tables (TDP_*) from the database, except for the names table (TDP_Names)"""
        self.__open_db_connection()
        self.__execute_sql("SELECT name FROM sqlite_master WHERE type='table';")
        #get table names:
        tables = list(self.__cur)
        for t in tables:
            if t[0].startswith("TDP_") and not t[0] == "TDP_Names":
                print "deleting table: " + t[0]
                self.__execute_sql("DROP TABLE '%s';" %t[0])
        self.__conn.close()

    def convert_accessDB_to_SQLite(self):
        """Converts the AccessPath to a SQLite database. Returns true if success"""
        if self.__db_is_right_version():
            print "SQLite database exists with right timestamp"
        else:
            print "Access database needs to be re-imported"
            print "removing old data..."
            self.__remove_tidal_data_tables()
            print "done!"
            print "Start transfer tables:"
            self.__transfer_tables_and_data()
            print "done!"
        self.tidal_points = self.__get_tidal_points()
        return True


if __name__ == "__main__":
    pass