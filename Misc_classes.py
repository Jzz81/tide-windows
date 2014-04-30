#-------------------------------------------------------------------------------
# Name:        Misc_classes
# Purpose:     Misc classes that help the program.
#
# Author:      Joos Dominicus
#
# Created:     24-03-2014
#-------------------------------------------------------------------------------
import os #Debug
import sqlite3

class misc_data:
    def __init__(self, SQLitePath):
        self.SQLitePath = SQLitePath
        self.misc_tables = {
            "ukc_units":
                {
                "name":"UKC_units",
                "columns":["id integer primary key autoincrement", "unit text"]
                }, \
            "deviations":
                {
                "name":"DEV_Names",
                "columns":["id integer primary key autoincrement", "name text"]
                }, \
            "speeds":
                {
                "name":"SPD_Names",
                "columns":["id integer primary key autoincrement", "name text"]
                }, \
            "ship_types":
                {
                "name":"SHP_Types",
                "columns":["id integer primary key autoincrement", "name text"]
                } \
            }
        self.default_ukc_units = ["%", "m"]
        self.default_deviations = ["Vlissingen", "Bath"]
        self.default_speeds = ["Zee", "Rivier", "Intermediate", "Haven"]
        self.default_ship_types = [["Container",15,13,9,6],["Bulk",13,12,8,5]]
        self.MakeDB()

    def open_db_connection(self):
        '''opens a connection to the database'''
        self.conn = sqlite3.connect(self.SQLitePath)
        self.cur = self.conn.cursor()

    def execute_sql(self, sql, return_cursor=False):
        '''executes a sql string and commits. If Cursor is set, it returns a cursor'''
        if return_cursor == False:
            self.cur.execute(sql)
            self.conn.commit()
        else:
            c = self.conn.cursor()
            c.execute(sql)
            self.conn.commit()
            return c

    def get_SPD_values(self):
        '''Retreives the speed values'''
        table = self.misc_tables["speeds"]["name"]
        self.execute_sql("SELECT * FROM {0};".format(table))
        result = {}
        for r in self.cur:
            result[r[0]]= r[1]
        return result

    def get_UKC_units(self):
        '''Retreives the possible UKC units from the database'''
        table = self.misc_tables["ukc_units"]["name"]
        self.execute_sql("SELECT * FROM {0};".format(table))
        result = {}
        for r in self.cur:
            result[r[0]] = r[1]
        return result

    def get_DEV_units(self):
        '''Retreives the possible UKC units from the database'''
        table = self.misc_tables["deviations"]["name"]
        self.execute_sql("SELECT * FROM {0};".format(table))
        result = {}
        for r in self.cur:
            result[r[0]] = r[1]
        return result

    def get_ship_types(self):
        '''Retreives the possible UKC units from the database'''
        table = self.misc_tables["ship_types"]["name"]
        self.execute_sql("SELECT * FROM {0};".format(table))
        result = {}
        for r in self.cur:
            result[r[0]] = r
        return result

    def delete_speed_columns(self, columns):
        '''creates a new speed table with columns given'''
        table = self.misc_tables["ship_types"]["name"]
        col = ", ".join(columns)
        print col
        #the following creates a temporary table holding the columns to preserve, deletes the original table,
        #and creates the original table again as a carbon copy of the temp table. Then the temp table is deleted
        #note that the columns do not get a data type with this method (they are not supplied). But SQLite is
        #mild on datatypes.
        self.execute_sql("CREATE TEMPORARY TABLE temp_backup({0});".format(col))
        self.execute_sql("INSERT INTO temp_backup SELECT {0} FROM {1};".format(col,table))
        self.execute_sql("DROP TABLE {0};".format(table))
        self.execute_sql("CREATE TABLE {0}({1});".format(table,col))
        self.execute_sql("INSERT INTO {0} SELECT {1} FROM temp_backup;".format(table, col))
        self.execute_sql("DROP TABLE temp_backup;")

    def check_speed_columns_in_ship_types(self):
        '''appends the desired columns to the ships types table and drops columns no longer applicable'''
        #get names of all columns; store them in 'names':
        table = self.misc_tables["ship_types"]["name"]
        self.execute_sql("SELECT * FROM {0};".format(table))
        names = list(map(lambda x: x[0], self.cur.description))
        old_amount = len(names)
        #check which name is still applicable; remove from list if not
        for i in range(2,len(names)):
            if not names[i] in self.speeds.values():
                names.remove(names[i])
        #check if anything is deleted; if yes, make it so:
        if len(names) < old_amount:
            self.delete_speed_columns(names)
        #check if anything is added, if yes, make it so:
        for item in self.speeds.itervalues():
            if not item in names:
                self.execute_sql("ALTER TABLE {0} ADD COLUMN {1} real;".format(table, item))

    def fill_SPD_table_defaults(self):
        '''fills the speeds table with default data'''
        table = self.misc_tables["speeds"]["name"]
        for spd in self.default_speeds:
            self.execute_sql("INSERT INTO {0} ('name') VALUES ('{1}');".format(table, spd))

    def fill_SHP_types_table_defaults(self):
        '''fills the UKC_unit table with default data'''
        table = self.misc_tables["ship_types"]["name"]
        for unit in self.default_ship_types:
            self.execute_sql("INSERT INTO {0}  VALUES (NULL, '{1}', {2}, {3}, {4}, {5});".format(table,  unit[0], unit[1],unit[2],unit[3], unit[4]))

    def fill_DEV_table_defaults(self):
        '''fills the UKC_unit table with default data'''
        table = self.misc_tables["deviations"]["name"]
        for unit in self.default_deviations:
            col = 'name'
            self.execute_sql("INSERT INTO {0} ({1}) VALUES ('{2}');".format(table, col, unit))

    def fill_UKC_table_defaults(self):
        '''fills the UKC_unit table with default data'''
        table = self.misc_tables["ukc_units"]["name"]
        for unit in self.default_ukc_units:
            col = 'unit'
            self.execute_sql("INSERT INTO {0} ({1}) VALUES ('{2}');".format(table, col, unit))

    def create_table(self, name, columns):
        '''creates a table if it does not exits'''
        table = self.misc_tables[name]["name"]
        sql = "CREATE TABLE {0} (".format(table)
        sql = sql + ", ".join(columns)
        sql = sql + ");"
        self.execute_sql(sql)

    def table_does_not_exists(self, table):
        '''returns true if the given table does not exists'''
        table = self.misc_tables[table]["name"]
        self.execute_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='{0}';".format(table))
        if self.cur.fetchone() == None:
            return True
        else:
            return False

    def MakeDB(self):
        '''create all tables needed'''
        self.open_db_connection()

        #speeds:
        if self.table_does_not_exists("speeds"):
            columns = self.misc_tables["speeds"]["columns"]
            self.create_table("speeds", columns)
            self.fill_SPD_table_defaults()
        self.speeds = self.get_SPD_values()

        #ship types
        if self.table_does_not_exists("ship_types"):
            columns = self.misc_tables["ship_types"]["columns"]
            self.create_table("ship_types", columns)
            self.check_speed_columns_in_ship_types()
            self.fill_SHP_types_table_defaults()
        else:
            self.check_speed_columns_in_ship_types()
        self.ship_types = self.get_ship_types()

        #deviations
        if self.table_does_not_exists("deviations"):
            columns = self.misc_tables["deviations"]["columns"]
            self.create_table("deviations", columns)
            self.fill_DEV_table_defaults()
        self.deviations = self.get_DEV_units()

        #UKC_units
        if self.table_does_not_exists("ukc_units"):
            columns = self.misc_tables["ukc_units"]["columns"]
            self.create_table("ukc_units", columns)
            self.fill_UKC_table_defaults()
        self.UKC_units = self.get_UKC_units()

        self.conn.close()

def main():
    dir = "{0}\jzz_pWesp".format(os.environ["LOCALAPPDATA"])
    if not os.path.exists(dir):
        os.makedirs(dir)
    SQLiteDBPath= dir + '\Jzz_Tijpoorten_python.db3'
    m = misc_data(SQLiteDBPath)
    print m.UKC_units
    print m.deviations
    print m.ship_types
    print m.speeds


if __name__ == '__main__':
    main()
