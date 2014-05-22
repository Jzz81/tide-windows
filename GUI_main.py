'''
Created on 4 mrt. 2014

@author: Joos
'''

import Routing
import tkFileDialog
import tkMessageBox
import os
import Database
import GUI_helper
import Tkinter as tk
import Misc_classes
import Tidal_calculations
import datetime

class Application(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        self.parent = parent
        #set path for SQLite db:
        dir = "{0}\Wespy".format(os.environ["LOCALAPPDATA"])
        self.local_db_directory = dir
        if not os.path.exists(self.local_db_directory):
            os.makedirs(self.local_db_directory)
        self.nw_db_directory = r"\\srkgna\personal\GNA\databaseHVL\Wespy"

        self.load_login_toplevel()

        self.__initDB()

        self.misc_data = Misc_classes.misc_data(self.database.local_program_database_path)
        self.routing_data = Routing.StoredRoutepoints(self.database.local_program_database_path)

        self.__initUI()

##        self.make_tidal_calculations()

    def __initUI(self):

        self.parent.title("GNA Tijpoorten")

        menubar = GUI_helper.MenuBar(self)
        self.parent.config(menu=menubar)

        self.waypointframe = GUI_helper.Waypointframe(self)
        self.connections_frame = GUI_helper.ConnectionsFrame(self)
        self.routes_frame = GUI_helper.RoutesFrame(self)
        self.tidal_calculations_frame = GUI_helper.Find_Tidal_window_frame(self)
        self.tidal_grapth_frame = GUI_helper.TidalWindowsGraphFrame(self)


    def __initDB(self):
        '''initializes the database and, if nessesary, converts the Access DB to import data'''
        self.database = Database.Database(self, self.nw_db_directory, self.local_db_directory)
        print "Tidal data available"

    def set_user(self, user):
        '''set the user to admin or user'''
        self.user = user
        self.top.destroy()
        if self.user == "admin":
            self.parent.title("GNA Tijpoorten *** ADMIN ***")
        else:
            self.parent.title("GNA Tijpoorten")


    def calculate_first_possible_window(self,
                                        ship_type,
                                        draught,
                                        route,
                                        eta,
                                        time_window_before_eta,
                                        time_window_after_eta,
                                        deviations):
        '''call the tidal calculations'''
        td_calc = Tidal_calculations.Tidal_calc(parent=self,
                                                route=route,
                                                waypoints=self.routing_data.route_points,
                                                connections=self.routing_data.connections,
                                                ukc_units=self.misc_data.UKC_units,
                                                speeds=self.misc_data.speeds,
                                                deviations=deviations,
                                                ship_type=ship_type,
                                                draught=draught,
                                                ETA=eta,
                                                min_tidal_window_before_ETA=time_window_before_eta,
                                                min_tidal_window_after_ETA=time_window_after_eta,
                                                numpy_dict=self.database.tidal_data_arrays)
        td_calc.calculate_first_possible_ETA()
        td_calc.get_global_window()
        self.tidal_grapth_frame.fill_tidal_graph(td_calc)
        return td_calc.global_window

#fill listboxes
    def fill_connections_listbox(self):
        '''fill the connections listbox with data'''
        self.connections_frame.clear_listbox()
        route_points = self.routing_data.route_points
        connections = self.routing_data.connections

        self.connections_frame.fill_listbox(route_points,connections)

    def fill_routes_listbox(self):
        '''fill the routes listbox with data'''
        self.routes_frame.fill_routes_listbox(self.routing_data.routes, self.routing_data.route_points, self.routing_data.connections)

    def fill_waypoint_listbox(self):
        '''fill the waypoint listbox with data'''
        self.config_frame.clear_tresholds_listbox(self.user)
        route_points = self.routing_data.route_points
        if self.user == "admin":
            ukc_units = self.misc_data.UKC_units
            deviations = self.misc_data.deviations
            speeds = self.misc_data.speeds
            tidal_points = self.database.tidal_points

            self.config_frame.fill_tresholds_admin_listbox(route_points,ukc_units,deviations,speeds, tidal_points)
        else:
            self.config_frame.fill_tresholds_user_listbox(route_points)


#display / hide section
    def display_config_screen(self):
        '''display a toplevel that holds the config screen'''
        self.config_frame = GUI_helper.config_screen_frame(self, self.user)
        self.config_frame.grid()
        self.fill_waypoint_listbox()

    def display_routes_frame(self):
        '''display the routes frame'''
        self.routes_frame.grid()
        self.fill_routes_listbox()

    def hide_routes_frame(self):
        '''hides the routes frame'''
        self.routes_frame.grid_forget()

    def display_connections_frame(self):
        '''display the connections frame'''
        self.connections_frame.grid()
        self.fill_connections_listbox()

    def hide_connections_frame(self):
        '''hides the connections frame'''
        self.connections_frame.grid_forget()

    def display_waypoint_frame(self):
        '''display the waypoints listbox frame'''
        self.waypointframe.grid()
        self.fill_waypoint_listbox()

    def hide_waypoint_frame(self):
        '''hide the waypoints listbox frame'''
        self.waypointframe.grid_forget()

    def display_tidal_calculations_frame(self):
        self.tidal_calculations_frame.grid()
        self.tidal_calculations_frame.fill_data(routes=self.routing_data.routes,
                                                deviations=self.misc_data.deviations,
                                                ship_types=self.misc_data.ship_types)
        self.tidal_grapth_frame.grid()

    def hide_tidal_calculations_frame(self):
        self.tidal_calculations_frame.grid_forget()


    def onExit(self):
        print "exit menu button clicked"
        self.parent.destroy()

#add section
    def add_waypoint(self):
        '''adds a waypoint to the database'''
        self.modify_waypoint("Nieuwe drempel")
        self.fill_waypoint_listbox()
        self.make_top_modal()

    def add_route(self):
        self.load_routes_toplevel("Nieuwe route")

    def add_connection(self):
        '''add a connection'''
        self.load_connection_toplevel("Nieuwe connectie")

#edit / modify section
    def edit_route(self):
        pass

    def edit_connection(self):
        '''edit a connection'''
        #get waypoints and distance from the listbox
        i = self.selected_connection_index()
        if i == None: return
        waypoint_1_name = self.connections_frame.lb.get(i)[0]
        waypoint_2_name = self.connections_frame.lb.get(i)[1]
        distance = self.connections_frame.lb.get(i)[2]

        #load toplevel and set data from listbox
        self.load_connection_toplevel("Connectie aanpassen")
        self.top.Treshold_1.set(waypoint_1_name)
        self.top.Treshold_2.set(waypoint_2_name)
        self.top.distance_entry.insert(0,distance)
        #hide cancel button
        self.top.cancel_button.grid_forget()
        self.top.ok_button.configure(text="Opslaan")

        #delete connection from listbox and database
        self.delete_connection()
        self.make_top_modal()

    def selected_route_index(self):
        '''returns the index of the selected route in the routeframe'''
        if len(self.routes_frame.route_lb.curselection()) > 0:
            return self.routes_frame.route_lb.curselection()

    def selected_connection_index(self):
        '''returns the index of the selected waypoint in the waypointframe'''
        if len(self.connections_frame.lb.curselection()) > 0:
            return  self.connections_frame.lb.curselection()[0]

#delete section
    def delete_connection(self):
        '''deletes a connection from the listbox and the database'''
        i = self.selected_connection_index()
        if i == None: return
        waypoint_1_name = self.connections_frame.lb.get(i)[0]
        waypoint_2_name = self.connections_frame.lb.get(i)[1]
        wp1 = self.routing_data.route_points[waypoint_1_name]
        wp2 = self.routing_data.route_points[waypoint_2_name]

        self.routing_data.delete_connection(wp1.id,wp2.id)
        self.delete_connection_from_listbox()

    def delete_waypoint_from_listbox(self):
        '''deletes the selected waypoint from the listbox'''
        i = self.selected_waypoint_index()
        if i == None: return
        if self.user == "admin":
            self.config_frame.tresholds_admin_listbox.delete(i)
        else:
            self.config_frame.tresholds_user_listbox.delete(i)

    def delete_waypoint_from_database(self, id):
        '''deletes a waypoint from the database'''
        self.routing_data.delete_waypoint_from_database(id)

    def delete_waypoint(self):
        '''deletes a waypoint from listbox and database'''
        i = self.selected_waypoint_index()
        if i == None: return
        selected_wp_name = self.selected_waypoint_name(i)
        self.wp = self.routing_data.route_points[selected_wp_name]
        id = self.wp.id
        self.delete_waypoint_from_listbox()
        self.delete_waypoint_from_database(id)

    def delete_route_from_listbox(self):
        i= self.selected_route_index()
        if i == None: return
        self.routes_frame.route_lb.delete(i)
        self.routes_frame.clear_routepoints_listbox()

    def delete_route(self):
        i = self.selected_route_index()
        if i == None: return
        route_name = self.routes_frame.route_lb.get(i)
        self.routing_data.delete_route_from_database(route_name)
        self.delete_route_from_listbox()

    def delete_connection_from_listbox(self):
        '''deletes the selected waypoint from the listbox'''
        i = self.selected_connection_index()
        if i == None: return
        self.connections_frame.lb.delete(i)
        self.make_top_modal()

#load toplevel section
    def load_login_toplevel(self):
        self.top = GUI_helper.login_screen_toplevel(self)
        self.make_top_modal(150,100)

    def load_routes_toplevel(self, title):
        waypoints = self.routing_data.route_points
        connections = self.routing_data.connections
        speeds = self.misc_data.speeds
        UKCs = self.misc_data.UKC_units

        self.top = GUI_helper.modify_route_toplevel(self, title, waypoints, connections, Routing.Route(), speeds, UKCs)
        self.make_top_modal()

    def load_connection_toplevel(self, title):
        '''gets called from 'edit connection' and 'add connection'''
        waypoints = self.routing_data.route_points
        self.top = GUI_helper.modify_connection_toplevel(self, title, waypoints)
        self.make_top_modal()

    def save_route(self, route):
        '''function that passes the route to the Routing, to add it to the database'''
        self.routing_data.add_new_route(route)
        self.top.destroy()
        self.fill_routes_listbox()

    def insert_connection_data(self):
        '''function gets called from the toplevel'''
        wp1_name = self.top.Treshold_1.get()
        wp2_name = self.top.Treshold_2.get()
        distance = self.top.distance_entry.get()
        if distance == '':
            return

        wp1 = self.routing_data.route_points[wp1_name]
        wp2 = self.routing_data.route_points[wp2_name]

        #check if connection exists
        for con in self.routing_data.connections.values():
            if (con[0] == wp1.id or con[0] == wp2.id) and (con[1] == wp1.id or con[1] == wp2.id):
                #connection exists already.
                title = "duplicaat"
                if float(con[2]) == float(distance):
                    message = "Er is al een connectie tusen deze drempels, met dezelfde afstand."
                    tkMessageBox.showwarning(title,message)
                    return
                else:
                    message = "Er is al een connectie gevonden tussen deze drempels, maar met een afstand van {dist}. Wilt u deze vervangen?".format(dist=con[2])
                    replace_connection = tkMessageBox.askyesno(title,message)
                    if replace_connection:
                        self.routing_data.edit_existing_connection(wp1.id, wp2.id, distance)
                        self.top.destroy()
                        self.fill_connections_listbox()
                    return

        self.routing_data.add_connection(wp1.id, wp2.id, distance)
        self.top.destroy()
        self.fill_connections_listbox()

    def modify_waypoint(self, title):
        ukc_units  = self.misc_data.UKC_units
        deviations = self.misc_data.deviations
        tidal_points = self.database.tidal_points
        speeds = self.misc_data.speeds

        self.top = GUI_helper.modify_waypoint_toplevel(self, self.user, title, ukc_units, deviations, tidal_points, speeds)

    def insert_waypoint_data(self):
        self.wp = Routing.Treshold()
        self.retreive_wp_data_from_form()

        self.routing_data.add_new_route_point(self.wp)
        self.fill_waypoint_listbox()
        self.top.destroy()

    def validate_waypoint_data(self):
        '''validated data inputed by user'''
        if self.top.wp_name_entry.get() and \
           self.top.wp_depth_ingoing_entry.get() and \
           self.top.wp_depth_outgoing_entry.get() and \
           self.top.wp_UKC_value_entry.get():
            return True

    def selected_waypoint_index(self):
        '''returns the index of the selected waypoint in the waypointframe'''
        if self.user == "admin":
            if len(self.config_frame.tresholds_admin_listbox.curselection()) > 0:
                return  self.config_frame.tresholds_admin_listbox.curselection()[0]
        else:
            if len(self.config_frame.tresholds_user_listbox.curselection()) > 0:
                return  self.config_frame.tresholds_user_listbox.curselection()[0]


    def retreive_wp_data_from_form(self):
        #retreive values from form:
        ukc_units  = self.misc_data.UKC_units
        deviations = self.misc_data.deviations
        tidal_points = self.database.tidal_points
        speeds = self.misc_data.speeds

        self.wp.name = self.top.wp_name_entry.get()
        self.wp.speed_id = speeds.keys()[speeds.values().index(self.top.Default_speed.get())]
        self.wp.depth_outgoing = self.top.wp_depth_outgoing_entry.get()
        self.wp.depth_ingoing = self.top.wp_depth_ingoing_entry.get()
        self.wp.deviation_id = deviations.keys()[deviations.values().index(self.top.deviation.get())]
        self.wp.UKC_unit_id = ukc_units.keys()[ukc_units.values().index(self.top.Default_UKC.get())]
        self.wp.UKC_value = self.top.wp_UKC_value_entry.get()
        self.wp.tidal_point_id = tidal_points.keys()[tidal_points.values().index(self.top.tidal_point.get())]

    def selected_waypoint_name(self, index):
        if self.user == "admin":
            return self.config_frame.tresholds_admin_listbox.get(index)[0]
        else:
            return self.config_frame.tresholds_user_listbox.get(index)[0]

    def update_waypoint(self):
        '''receives updated waypoint data from the edit window'''
        self.retreive_wp_data_from_form()

        self.routing_data.edit_existing_waypoint(self.wp)

        self.wp = None

        self.fill_waypoint_listbox()
        self.top.destroy()

    def edit_waypoint(self):
        '''edits an exitsting waypoint'''
        i = self.selected_waypoint_index()
        if i == None: return
        #load toplevel
        self.modify_waypoint("Drempel aanpassen")

        selected_wp_name = self.selected_waypoint_name(i)
        self.wp = self.routing_data.route_points[selected_wp_name]

        ukc_units  = self.misc_data.UKC_units
        deviations = self.misc_data.deviations
        tidal_points = self.database.tidal_points
        speeds = self.misc_data.speeds

        #set values from wp:
        self.top.wp_name_entry.insert(0,self.wp.name)
        self.top.wp_depth_outgoing_entry.insert(0,self.wp.depth_outgoing)
        self.top.wp_depth_ingoing_entry.insert(0,self.wp.depth_ingoing)
        if self.user == "admin":
            self.top.Default_speed.set(speeds[int(self.wp.speed_id)])
            self.top.deviation.set(deviations[int(self.wp.deviation_id)])
            self.top.Default_UKC.set(ukc_units[int(self.wp.UKC_unit_id)])
            self.top.wp_UKC_value_entry.insert(0,self.wp.UKC_value)
            self.top.tidal_point.set(tidal_points[int(self.wp.tidal_point_id)])

        #hide cancel button
        self.top.cancel_button.grid_forget()
        self.top.ok_button.configure(text="Opslaan", command=self.update_waypoint)

        self.delete_waypoint_from_listbox()
        self.make_top_modal()

    def make_top_modal(self, width=300, height=400):
        '''make the toplevel window modal'''
        xoffset = 200
        yoffset = 100
        self.top.geometry("%dx%d%+d%+d" % (width, height, xoffset, yoffset))
        self.top.focus_set()
        self.top.grab_set()
        self.top.transient(self)
        self.wait_window(self.top)



if __name__ == "__main__":
    #start GUI:
    root = tk.Tk()
    #set maximized:
    #root.wm_state('zoomed')
    #pass to Window class
    Application(root).pack()
    #'send' program into gui loop (to keep program in gui)
    root.mainloop()


