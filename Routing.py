'''
Created on 27 feb. 2014

@author: Joos
'''
import sqlite3
import os

class StoredRoutepoints():
    '''
    This class will interact with the general database.
    It will store routepoints if they are added, retreive them if they are asked for, and delete them if they are removed.
    '''

    def __init__(self, SQLitePath):
        '''
        Constructor
        '''
        self.__SQLite_path = SQLitePath
        self.route_points = {}
        self.connections = {}
        self.routes = {}
        #define database tables for Tresholds and Routes:
        self.__tables = {
            "routepoint_names":
                {
                "name":"TRH_Names",
                "columns":["id integer primary key autoincrement", "name text"]
                },
            "ingoing_depth":
                {
                "name":"TRH_Depth_In",
                "columns":["id int", "depth real"]
                },
            "outgoing_depth":
                {
                "name":"TRH_Depth_Out",
                "columns":["id int", "depth real"]
                },
            "deviation":
                {
                "name":"TRH_Deviation",
                "columns":["id int", "deviation_id int"]
                },
            "ukc_unit":
                {
                "name":"TRH_Def_UKC_unit",
                "columns":["id int", "ukc_unit_id int"]
                },
            "ukc_value":
                {
                "name":"TRH_Def_UKC_value",
                "columns":["id int", "ukc_value real"]
                },
            "speed":
                {
                "name":"TRH_Def_speed",
                "columns":["id int", "speed text"]
                },
            "tidal_point":
                {
                "name":"TRH_Tidal_Point",
                "columns":["id int", "tidal_point_id int"]
                },
            "connections":
                {
                "name":"TRH_Connections",
                "columns":["id integer primary key autoincrement", "treshold_1_id int", "treshold_2_id int", "distance real"]
                },
            "route_names":
                {
                "name":"RTE_Names",
                "columns":["id integer primary key autoincrement","name text", "is_ingoing int"]
                },
            "route_tresholds":
                {
                "name":"RTE_Tresholds",
                "columns":["id int", "follow_nr int", "treshold_id int", "ukc_unit_id int", "ukc_value real", "speed_id int"]
                }
            }

        self.__make_DB()
        self.__retreive_routepoints_from_DB()
        self.__check_tidal_points_of_existing_waypoints()
        self.__check_connections()
        self.__retreive_connection_data()
        self.__retreive_routes_from_database()

    def __table_does_not_exists(self, table):
        '''returns true if the given table does not exists'''
        self.__execute_sql("SELECT name FROM sqlite_master WHERE type='table' AND name='{0}';".format(table))
        if self.__cur.fetchone() == None:
            return True
        else:
            return False

    def __check_tidal_points_of_existing_waypoints(self):
        '''loops the existing waypoints and checks if the tidal points still exist in the database'''
        self.__open_db_connection()
        for wp in self.route_points.values():
            tp_id = wp.tidal_point_id
            self.__execute_sql("SELECT * FROM TDP_Names WHERE id='{id}' AND data_exists='1';".format(id=tp_id))
            if self.__cur.fetchone() == None:
                print "tidal data table with id '{id}' does not exist".format(id=tp_id)
                wp.tidal_point_id = "0"
        self.__conn.close()


    def edit_existing_waypoint(self, wp):
        '''edits an existing waypoint in the database'''
        self.__open_db_connection()
        wp.name = self.__validate_name(name=wp.name, id=wp.id,routepoint=True)
        self.__update_treshold_name(wp.name, wp.id)
        self.__insert_routepoint_in_database(wp)
        self.__retreive_routepoints_from_DB()
        self.__conn.close()

    def __validate_name(self, name, id=-1, routepoint=False, route=False):
        '''checks if name exists in the database, if it exists, it will add an integer to the end.'''
        if (not routepoint and not route) or (routepoint and route):
            return
        elif routepoint:
            table_name = self.__tables["routepoint_names"]["name"]
        else:
            table_name = self.__tables["route_names"]["name"]

        col = "name"
        if id == -1:
            sql = "SELECT * FROM '{table}' WHERE {col} = '{name}';".format(table=table_name, col=col, name="{name}")
        else:
            sql = "SELECT * FROM '{table}' WHERE {col} = '{name}' AND id IS NOT '{id}';".format(table=table_name, col=col, name="{name}", id=id)
        #try original name:
        c = self.__execute_sql(sql.format(name=name),True)
        if c.fetchone() == None:
            return name
        i = 0
        #add integers and test again
        while True:
            i += 1
            c = self.__execute_sql(sql.format(name=name+str(i)),True)
            if c.fetchone() == None:
                return name + str(i)

    def add_new_route_point(self,routepoint):
        '''
        Function will add a routepoint instance to the database (except the connections)
        '''
        self.__open_db_connection()
        routepoint.name = self.__validate_name(name=routepoint.name,routepoint=True)
        routepoint.id = self.__insert_name(name=routepoint.name, routepoint=True)
        self.__insert_routepoint_in_database(routepoint)
        self.__conn.close()
        #refresh stored data:
        self.__retreive_routepoints_from_DB()

    def add_new_route(self, route):
        '''Function will add a route to the database'''
        self.__open_db_connection()
        route.name = self.__validate_name(name=route.name, route=True)
        route.id = self.__insert_name(name=route.name, route=True)
        self.__insert_route_in_database(route)
        self.__retreive_routes_from_database()

    def __insert_routepoint_in_database(self,routepoint):
        '''insert data from the routepoint into the database'''
        self.__insert_table_data("deviation", routepoint.id, routepoint.deviation_id)
        self.__insert_table_data("ingoing_depth", routepoint.id, routepoint.depth_ingoing)
        self.__insert_table_data("ukc_value", routepoint.id, routepoint.UKC_value)
        self.__insert_table_data("ukc_unit", routepoint.id, routepoint.UKC_unit_id)
        self.__insert_table_data("tidal_point", routepoint.id, routepoint.tidal_point_id)
        self.__insert_table_data("outgoing_depth", routepoint.id, routepoint.depth_outgoing)
        self.__insert_table_data("speed", routepoint.id, routepoint.speed_id)

    def __insert_route_in_database(self, route):
        '''inserts data from the route into the database (name is already inserted and id is set)'''
        table_name = self.__tables["route_tresholds"]["name"]
        self.__open_db_connection()
        id = route.id
        for follow_nr in range(1, route.amount_of_routepoints +1):
            treshold_id = route.routepoints[follow_nr]["id"]
            ukc_unit_id = route.routepoints[follow_nr]["UKC_unit_id"]
            ukc_value = route.routepoints[follow_nr]["UKC_value"]
            speed_id = route.routepoints[follow_nr]["speed_id"]
            sql= "INSERT INTO {table} VALUES ('{id}','{f_nr}','{trh_id}','{ukc_u}','{ukc_v}','{speed}');"
            sql = sql.format(table=table_name, id=id,f_nr=follow_nr,trh_id=treshold_id,ukc_u=ukc_unit_id,ukc_v=ukc_value,speed=speed_id)
            self.__execute_sql(sql)
        self.__conn.close()

    def __update_treshold_name(self, name, id):
        '''updates a tresholds name in the database'''
        table_name = self.__tables["routepoint_names"]["name"]
        col = "name"
        self.__execute_sql("UPDATE {table} SET {col} = '{name}' WHERE id = {id};".format(table=table_name, col=col, name=name, id=id))

    def __insert_name(self, name, routepoint=False, route=False):
        '''inserts a name into the database, returs the id'''
        if (not routepoint and not route) or (routepoint and route):
            return
        elif routepoint:
            table_name = self.__tables["routepoint_names"]["name"]
        else:
            table_name = self.__tables["route_names"]["name"]
        col = "name"
        self.__execute_sql("INSERT INTO {0} ('{1}') VALUES ('{2}');".format(table_name, col, name))
        return self.__cur.lastrowid

    def __insert_table_data(self, table, id, data):
        '''inserts data into table.'''
        table_name = self.__tables[table]["name"]
        #delete first, in case of update
        self.__execute_sql("DELETE FROM {table} WHERE id='{id}';".format(table=table_name, id=id))

        values = "'{0}', '{1}'".format(id, data)
        self.__execute_sql("INSERT INTO {0} VALUES ({1});".format(table_name, values))

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

    def delete_route_from_database(self, route_name):
        '''deletes a route from the database'''
        route = self.routes[route_name]
        route_id = route.id
        name_table_name = self.__tables["route_names"]["name"]
        rp_table_name = self.__tables["route_tresholds"]["name"]
        self.__open_db_connection()
        self.__execute_sql("DELETE FROM {table} WHERE id={id};".format(table=name_table_name, id=route_id))
        self.__execute_sql("DELETE FROM {table} WHERE id={id};".format(table=rp_table_name, id=route_id))
        self.__conn.close()

    def delete_waypoint_from_database(self, routepoint_id):
        '''delete a waypoint from the database'''
        self.__open_db_connection()
        self.__delete_table_data("routepoint_names", routepoint_id)
        self.__delete_table_data("deviation", routepoint_id)
        self.__delete_table_data("ingoing_depth",routepoint_id)
        self.__delete_table_data("outgoing_depth",routepoint_id)
        self.__delete_table_data("ukc_value", routepoint_id)
        self.__delete_table_data("ukc_unit",routepoint_id)
        self.__delete_table_data("tidal_point",routepoint_id)
        self.__delete_table_data("speed", routepoint_id)
        self.__delete_connection_data(routepoint_id)
        self.__conn.close()
        self.__retreive_routepoints_from_DB()
        self.__check_connections()
        self.__retreive_connection_data()

    def __delete_connection_data(self, id):
        '''deletes all connection data from table'''
        table_name = self.__tables["connections"]["name"]
        self.__execute_sql("DELETE FROM {table} WHERE treshold_1_id = '{id}' OR treshold_2_id = '{id}';".format(table=table_name, id=id))

    def __delete_table_data(self, table, id):
        '''deletes data from table, with id'''
        table_name = self.__tables[table]["name"]
        self.__execute_sql("DELETE FROM {table} WHERE id = '{id}';".format(table=table_name, id=id))

    def __retreive_routepoints_from_DB(self):
        '''retreives all tresholds from the database and store them in a list (as Treshold classes)'''
        self.route_points = {}
        self.__open_db_connection()
        name_table_name = self.__tables["routepoint_names"]["name"]
        self.__execute_sql("SELECT * FROM {0}".format(name_table_name))
        for r in self.__cur:
            wp = Treshold()
            wp.id = r[0]
            wp.name = r[1]
            wp.deviation_id = self.__retreive_table_data("deviation",wp.id)
            wp.depth_ingoing = self.__retreive_table_data("ingoing_depth",wp.id)
            wp.UKC_value = self.__retreive_table_data("ukc_value",wp.id)
            wp.UKC_unit_id = self.__retreive_table_data("ukc_unit",wp.id)
            wp.tidal_point_id = self.__retreive_table_data("tidal_point",wp.id)
            wp.depth_outgoing = self.__retreive_table_data("outgoing_depth",wp.id)
            wp.speed_id = self.__retreive_table_data("speed",wp.id)
            self.route_points[wp.name] = wp
        self.__conn.close()

    def __retreive_connection_data(self):
        '''retreives all connection data'''
        self.__open_db_connection()
        table_name = self.__tables["connections"]["name"]
        self.__execute_sql("SELECT * FROM {table};".format(table=table_name))
        self.connections = {}
        for r in self.__cur:
            id = r[0]
            l = []
            for i in range(1, len(r)):
                l.append(r[i])
            self.connections[id] = l
        self.__conn.close()

    def __retreive_routes_from_database(self):
        '''retreives all routes from the database'''
        self.routes = {}
        self.__open_db_connection()
        table_name = self.__tables["route_names"]["name"]
        self.__execute_sql("SELECT * FROM {table};".format(table=table_name))
        for r in self.__cur:
            id = r[0]
            route_name = r[1]
            route_is_ingoing = r[2]
            self.routes[route_name] = self.__retreive_route_data(id, route_name, route_is_ingoing)

    def __retreive_route_data(self, id, name, is_ingoing):
        '''retreives all routepoints of the given route. connection is already open'''
        route = Route()
        route.name = name
        route.id = id
        route.route_is_ingoing = is_ingoing
        table_name = self.__tables["route_tresholds"]["name"]
        c = self.__execute_sql("SELECT * FROM {table} WHERE id={id} ORDER BY follow_nr ASC;".format(table=table_name, id=id), True)
        for wp in c:
            route.add_routepoint(wp[2],wp[3],wp[4],wp[5])
        return route

    def edit_existing_connection(self, treshold_id_1, treshold_id_2, distance):
        '''edits an exitisting connection'''
        self.delete_connection(treshold_id_1,treshold_id_2)
        self.__open_db_connection()
        table_name = self.__tables["connections"]["name"]
        col = "treshold_1_id, treshold_2_id, distance"
        val = "'{t1id}', '{t2id}', '{dist}'".format(t1id=treshold_id_1, t2id=treshold_id_2, dist=distance)
        self.__execute_sql("INSERT INTO {table} ({col}) VALUES ({val});".format(table=table_name, col=col, val=val))
        self.__conn.close()
        self.__retreive_connection_data()

    def add_connection(self, treshold_1_id, treshold_2_id, distance):
        '''adds a connection to the database'''
        self.__open_db_connection()
        table_name = self.__tables["connections"]["name"]
        col = "treshold_1_id, treshold_2_id, distance"
        val = "'{t1id}', '{t2id}', '{dist}'".format(t1id=treshold_1_id, t2id=treshold_2_id, dist=distance)
        self.__execute_sql("INSERT INTO {table} ({col}) VALUES ({val});".format(table=table_name, col=col, val=val))
        self.__conn.close()
        self.__retreive_connection_data()

    def delete_connection(self, treshold_1_id, treshold_2_id):
        '''deletes a connection from the database'''
        self.__open_db_connection()
        table_name = self.__tables["connections"]["name"]
        sql = "DELETE FROM {table} WHERE treshold_1_id = {val1} AND treshold_2_id = {val2}".format(table=table_name, val1=treshold_1_id, val2=treshold_2_id)
        self.__execute_sql(sql)
        self.__conn.close()
        self.__retreive_connection_data()

    def __check_connections(self):
        '''checks all connections'''
        #check if all waypoints still exist
        waypoint_id_list = []
        for wp in self.route_points.values():
            waypoint_id_list.append(wp.id)
        self.__open_db_connection()
        table_name = self.__tables["connections"]["name"]
        sql = "SELECT * FROM {table};".format(table=table_name)
        c = self.__execute_sql(sql=sql, return_cursor=True)
        for r in c:
            if not r[1] in waypoint_id_list or not r[2] in waypoint_id_list:
                print "deleting connections with id: ",
                print r[0]
                self.delete_connection(r[1],r[2])

    def __retreive_table_data(self, table, id):
        '''retreives all data from a given table with a given id'''
        table_name = self.__tables[table]["name"]
        c = self.__execute_sql("SELECT * FROM {0} WHERE id ='{1}';".format(table_name, id),True)
        for r in c:
            for i in range(1, len(r)):
                return r[i]

    def __create_table(self, name, columns):
        '''creates a table if it does not exits'''
        sql = "CREATE TABLE IF NOT EXISTS {0} (".format(name)
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

class Treshold():
    '''
    Class that represents a treshold in a route.
    '''
    def __init__(self):
        '''Stores information that defines a Treshold'''
        self.id = None
        self.name = None
        self.UKC_unit_id = None
        self.UKC_value = None
        self.speed_id = None
        self.depth_ingoing = None
        self.depth_outgoing = None
        self.deviation_id = None
        self.tidal_point_id = None

class Route():
    '''Class that represents a route'''
    def __init__(self):
        self.id = None
        self.name = None
        self.routepoints = {}
        self.amount_of_routepoints = 0
        self.route_is_ingoing = None

    def add_routepoint(self, id, UKC_unit_id, UKC_value, speed_id):
        '''adds a routepoint to the dict'''
        rp = {}
        rp["id"] = id
        rp["UKC_unit_id"] = UKC_unit_id
        rp["UKC_value"] = UKC_value
        rp["speed_id"] = speed_id
        #increment amount of routepoints, then add the routepoint. The dictionary will then keep track (allthough unsorted)
        self.amount_of_routepoints += 1
        self.routepoints[self.amount_of_routepoints] = rp

    def route_holds_wp_id(self, id):
        '''returns true if the route holds the waypoint'''
        if self.amount_of_routepoints == 0: return False
        for i in range(1, self.amount_of_routepoints):
            rp = self.routepoints[i]
            if rp["id"] == id: return True
        return False

if __name__ == "__main__":
    dir = "{0}\jzz_pWesp".format(os.environ["LOCALAPPDATA"])
    if not os.path.exists(dir):
        os.makedirs(dir)
    SQLiteDBPath= dir + '\Jzz_Tijpoorten_python.db3'
    rps = StoredRoutepoints(SQLiteDBPath)
##    wp = Treshold()
##    wp.name = "Deurganckdok Ingang"
##    wp.depth_ingoing = 143
##    wp.depth_outgoing = 143
##    wp.deviation_id = 1
##    wp.speed_id = 4
##    wp.tidal_point_id = 7
##    wp.UKC_unit_id = 1
##    wp.UKC_value = 10
##    rps.AddRoutePoint(wp)
##    rps.delete_waypoint_from_database(2)
##    print rps.route_points
##    print rps.connections

