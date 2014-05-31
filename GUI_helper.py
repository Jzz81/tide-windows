#-------------------------------------------------------------------------------
# Name:        GUI_helper
# Purpose:     provide helper classes for the GUI
#
# Author:      Jzz
#
# Created:     20-03-2014
#-------------------------------------------------------------------------------

import Tkinter as tk
import ttk
import datetime
import calendar
import pytz

def convert_UTC_to_local_time(utc):
    '''converts the utc time to a local time (amsterdam)'''
    utc_time = pytz.utc.localize(utc)
    return utc_time.astimezone(pytz.timezone("Europe/Amsterdam")).replace(tzinfo=None)

def convert_local_time_to_UTC(localtime):
    '''converts the local time to utc'''
    localized_time = pytz.timezone("Europe/Amsterdam").localize(localtime)
    return localized_time.astimezone(pytz.utc).replace(tzinfo=None)

class config_screen_frame(tk.Frame):
    def __init__(self, parent, user, *args, **kwargs):
        tk.Frame.__init__(self,parent, *args, **kwargs)
        self.parent = parent

        self.relief = tk.RAISED

        tabs = ttk.Notebook(self)
        #TRESHOLDS TAB:
        self.treshold_tab = ttk.Frame(tabs)
        self.tresholds_admin_listbox = MultiListbox(self.treshold_tab, (('Naam', 20), \
                                     ('snelheid', 12), \
                                     ('waterdiepte Afvaart', 10), \
                                     ('waterdiepte Opvaart', 10), \
                                     ('afwijking waterstand', 7), \
                                     ('UKC', 10), \
                                     ('getijdetabel', 12)))
        self.tresholds_user_listbox = MultiListbox(self.treshold_tab, (("Naam", 20), \
                                     ('waterdiepte Afvaart', 10), \
                                     ('waterdiepte Opvaart', 10)))
        if user == "admin":
            self.tresholds_admin_listbox.grid()
        else:
            self.tresholds_user_listbox.grid()

        f = tk.Frame(self.treshold_tab)
        if user == "admin":
            tk.Button(f, text="nieuw", command=self.parent.add_waypoint).grid(row=0, column=1, pady=5, padx=5)
            tk.Button(f, text="delete", command=self.parent.delete_waypoint).grid(row=0,column=2, pady=5, padx=5)

        tk.Button(f, text="edit", command=self.parent.edit_waypoint).grid(row=0,column=0, pady=5, padx=5)
        f.grid(sticky=tk.E)

        tabs.add(self.treshold_tab, text="Drempels")

        #CONNECTIONS TAB:
        self.connections_tab = tk.Frame(tabs)
        if user == "admin":
            tabs.add(self.connections_tab, text="Connecties")
            self.connections_lb = MultiListbox(self.connections_tab,(("drempel 1",20),("drempel 2", 20), ("afstand", 10)))
            self.connections_lb.grid(row=0,column=0, sticky=tk.W)

            conn_button_frame = tk.Frame(self.connections_tab)
            tk.Button(conn_button_frame, text="nieuw", command=self.parent.add_connection).grid(row=0, column=1, pady=5, padx=5)
            tk.Button(conn_button_frame, text="edit", command=self.parent.edit_connection).grid(row=0,column=0, pady=5, padx=5)
            tk.Button(conn_button_frame, text="delete", command=self.parent.delete_connection).grid(row=0,column=2, pady=5, padx=5)
            conn_button_frame.grid(sticky=tk.E)

        #ROUTES TAB:
        self.routes_tab = ttk.Frame(tabs)

        route_f = tk.Frame(self.routes_tab)
        tk.Label(route_f, text="routes", borderwidth=1, relief=tk.RAISED).grid(row=0, sticky=tk.W+tk.E)
        self.route_lb = tk.Listbox(route_f, borderwidth=0, selectborderwidth=0, relief=tk.FLAT, exportselection=tk.FALSE)
        self.route_lb.grid(row=1,column=0)
        self.route_lb.bind('<<ListboxSelect>>', self.fill_routepoints_listbox)
        route_f.grid(row=0, column=0, padx=10)

        self.route_tresholds_lb = MultiListbox(self.routes_tab,(("drempel",20),("afstand",10)))
        self.route_tresholds_lb.grid(row=0,column=1, sticky=tk.E)

        route_button_frame = tk.Frame(self.routes_tab)
        tk.Button(route_button_frame, text="nieuw", command=self.parent.add_route).grid(row=0, column=1, pady=5, padx=5)
        tk.Button(route_button_frame, text="edit", command=self.parent.edit_route).grid(row=0,column=0, pady=5, padx=5)
        tk.Button(route_button_frame, text="delete", command=self.parent.delete_route).grid(row=0,column=2, pady=5, padx=5)
        route_button_frame.grid(sticky=tk.E, columnspan=2)

        tabs.add(self.routes_tab, text="Routes")
        tabs.grid(row=0,column=0, sticky=tk.W)

    def fill_tresholds_user_listbox(self, waypoints):
        '''to fill the user listbox with waypoint data'''
        for key in sorted(waypoints.keys(), key=lambda s: s.lower()):
            route_point = waypoints[key]
            self.tresholds_user_listbox.insert(tk.END,
                                            (route_point.name,
                                            route_point.depth_outgoing,
                                            route_point.depth_ingoing))

    def fill_tresholds_admin_listbox(self, waypoints, ukc_units, deviations, speeds, tidal_points):
        '''to fill the admin listbox with waypoint data'''
        for key in sorted(waypoints.keys(), key=lambda s: s.lower()):
            route_point = waypoints[key]
            self.tresholds_admin_listbox.insert(tk.END,
                            (route_point.name, \
                            speeds[int(route_point.speed_id)], \
                            route_point.depth_outgoing, \
                            route_point.depth_ingoing, \
                            deviations[int(route_point.deviation_id)], \
                            "{0}{1}".format(route_point.UKC_value, ukc_units[int(route_point.UKC_unit_id)]) , \
                            tidal_points[int(route_point.tidal_point_id)]))

    def clear_tresholds_listbox(self, user):
        '''clears the listbox of all data'''
        if user == "admin":
            self.tresholds_admin_listbox.delete(0, self.tresholds_admin_listbox.size())
        else:
            self.tresholds_user_listbox.delete(0, self.tresholds_user_listbox.size())

    def fill_connections_listbox(self, waypoints, connections):
        '''fills the listbox with connection data'''
        #map wp id's to names
        wp_ids = {}
        for wp in waypoints.values():
            wp_ids[wp.id] = wp.name
        #fill lb:
        for conn in connections.values():
            self.connections_lb.insert(tk.END,(wp_ids[conn[0]], wp_ids[conn[1]],conn[2]))

    def clear_connections_listbox(self):
        '''clears the listbox of all data'''
        self.connections_lb.delete(0, self.connections_lb.size())

    def fill_routes_listbox(self, routes, waypoints, connections):
        '''fills the routes listbox with all available routes in the DB'''
        #store fresh waypoint and connection data:
        self.waypoints = waypoints
        self.waypoint_names_by_id = {}
        self.waypoint_ids_by_name = {}
        self.route_lb.delete(0, self.route_lb.size())
        for wp in self.waypoints.values():
            self.waypoint_names_by_id[wp.id] = wp.name
            self.waypoint_ids_by_name[wp.name] = wp.id

        self.connections = connections
        self.routes = routes
        for r in routes.keys():
            self.route_lb.insert(tk.END, r)

    def fill_routepoints_listbox(self, *args):
        '''fills the routepoints listbox with waypoints of the selected route'''
        route_name = self.route_lb.get(self.route_lb.curselection())
        r = self.routes[route_name]
        self.clear_routepoints_listbox()
        #loop routepoints to insert:
        distance = 0
        last_waypoint_id = -1
        for rp in range(1, r.amount_of_routepoints + 1):
            wp = r.routepoints[rp]
            wp_id = wp["id"]
            wp_name = self.waypoint_names_by_id[wp_id]
            if last_waypoint_id > -1:
                distance += round(self.__get_distance_from_connections(wp_id, last_waypoint_id),2)
            self.route_tresholds_lb.insert(tk.END, (wp_name, str(distance)))
            last_waypoint_id = wp_id

    def clear_routepoints_listbox(self):
        self.route_tresholds_lb.delete(0, self.route_tresholds_lb.size())

    def __get_distance_from_connections(self, id_1, id_2):
        '''will return the distance between the 2 wp id's'''
        for con in self.connections.values():
            if (id_1 == con[0] and id_2 == con[1]) or (id_1 == con[1] and id_2 == con[0]):
                return con[2]

class ConnectionsFrame(tk.Frame):
    '''creates a frame with everything to add and modify connections between waypoints.'''
    def __init__(self, parent):
        self.parent = parent
        tk.Frame.__init__(self, parent)
        self.lb = MultiListbox(self,(("drempel 1",20),("drempel 2", 20), ("afstand", 10)))
        self.lb.grid(row=0,column=0, sticky=tk.W)
        f = tk.Frame(self)
        tk.Button(f, text="nieuw", command=self.parent.add_connection).grid(row=0, column=1, pady=5, padx=5)
        tk.Button(f, text="edit", command=self.parent.edit_connection).grid(row=0,column=0, pady=5, padx=5)
        tk.Button(f, text="delete", command=self.parent.delete_connection).grid(row=0,column=2, pady=5, padx=5)
        f.grid(sticky=tk.E)

    def fill_listbox(self, waypoints, connections):
        '''fills the listbox with connection data'''
        #map wp id's to names
        wp_ids = {}
        for wp in waypoints.values():
            wp_ids[wp.id] = wp.name
        #fill lb:
        for conn in connections.values():
            self.lb.insert(tk.END,(wp_ids[conn[0]], wp_ids[conn[1]],conn[2]))

    def clear_listbox(self):
        '''clears the listbox of all data'''
        self.lb.delete(0, self.lb.size())

class login_screen_toplevel(tk.Toplevel):
    '''displays a login screen that will default to a normal user, has Admin as 2nd'''
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.title("login")
        users = ["gebruiker", "Admin"]

        r = 0
        #user label and optionmenu
        self.user_label = tk.Label(self, text="programma gebruiken als:")
        self.user_label.grid(row=r, column=0)
        r += 1
        self.selected_user = tk.StringVar()
        self.user_option = tk.OptionMenu(self, self.selected_user, *users)
        self.user_option.grid(row=r, column=0)
        self.selected_user.set(users[0])
        self.password_entry = tk.Entry(self, show='*')
        self.selected_user.trace("w", self.__show_password_box)

        r += 2 #skip one row to account for the password box

        self.ok_button = tk.Button(self, text='Ok', command=self.__login)
        self.ok_button.grid(row=r,column=0)

    def __login(self):
        '''check password and login'''
        if self.selected_user.get() == "Admin" and self.password_entry.get() == "a":#"gnaPass":DEBUG
            self.parent.user = "admin"
        if self.selected_user.get() == "gebruiker":
            self.parent.user = "user"
        self.destroy()

    def __show_password_box(self, *args):
        '''show the entry box to input a password'''
        if self.selected_user.get() == "Admin":
            self.password_entry.grid(row=2, column=0)
        else:
            self.password_entry.grid_forget()

class modify_route_toplevel(tk.Toplevel):
    def __init__(self, parent, title, waypoints, connections, route, speeds, UKC_units):
        tk.Toplevel.__init__(self,parent)
        self.parent = parent

        self.speeds = speeds
        self.speed_ids_by_name = {}
        for id, s in self.speeds.iteritems():
            self.speed_ids_by_name[s] = id

        self.UKC_units = UKC_units
        self.UKC_ids_by_name = {}
        for id, u in self.UKC_units.iteritems():
            self.UKC_ids_by_name[u] = id

        self.connections = connections
        self.Route = route

        self.tresholds = waypoints
        self.treshold_names_by_id = {}
        self.treshold_ids_by_name = {}
        for wp in self.tresholds.values():
            self.treshold_names_by_id[wp.id] = wp.name
            self.treshold_ids_by_name[wp.name] = wp.id

        self.last_waypoint = None

        self.selected_waypoint = tk.StringVar(self)
        self.selected_waypoint.trace("w", self.fill_data_fields)
        self.selected_speed = tk.StringVar(self)
        self.selected_UKC = tk.StringVar(self)

        self.routename_frame = tk.Frame(self)
        #frame to ask for the route name
        tk.Label(self.routename_frame, text="Naam van de route: ").grid(row=0, column=0, sticky=tk.E)
        self.route_name_entry = tk.Entry(self.routename_frame)
        self.route_name_entry.grid(row=0, column=1, sticky=tk.W)

        self.set_route_name_button = tk.Button(self.routename_frame, text='Ok', command=self.set_waypoint_name)
        self.set_route_name_button.grid(row=1,column=1, sticky=tk.E)

        self.routename_frame.grid(row=0, column=0,padx = 10, pady=10)


        self.dataframe = tk.Frame(self)

        r=0
        self.route_name_label = tk.Label(self.dataframe)
        self.route_name_label.grid(row=r, padx=10)
        r += 1

        tk.Frame(self.dataframe, height=2, background="white", borderwidth=2, relief=tk.SUNKEN).grid(row=r, sticky=tk.W+tk.E, columnspan=2)

        r += 1
        #waypoint label and optionmenu
        self.waypoint_label = tk.Label(self.dataframe, text="Selecteer de eerste drempel:")
        self.waypoint_label.grid(row=r, column=0, sticky=tk.W)

        self.waypoint_option = tk.OptionMenu(self.dataframe, self.selected_waypoint, "")
        self.waypoint_option.grid(row=r, column=1, sticky=tk.E)

        r += 1
        #speed label and optionmenu
        tk.Label(self.dataframe, text="selecteer snelheid:").grid(row=r, column=0, sticky=tk.W)
        self.speed_option = tk.OptionMenu(self.dataframe, self.selected_speed, *speeds.values())
        self.speed_option.grid(row=r, column=1, sticky=tk.E)
        self.selected_speed.set(speeds[1])

        r += 1
        #UKC_value label and entry
        tk.Label(self.dataframe, text="waarde voor UKC:").grid(row=r, column=0, sticky=tk.W)
        self.ukc_value_entry = tk.Entry(self.dataframe)
        self.ukc_value_entry.grid(row=r,column=1, sticky=tk.E)

        r += 1
        #UKC_unit label and optionmenu
        tk.Label(self.dataframe, text="UKC eenheid:").grid(row=r, column=0, sticky=tk.W)
        self.ukc_unit_option = tk.OptionMenu(self.dataframe, self.selected_UKC, *UKC_units.values())
        self.ukc_unit_option.grid(row=r, column=1, sticky=tk.E)
        self.selected_UKC.set(UKC_units[1])

        r += 1
        #button to select waypoint
        self.select_waypoint_button = tk.Button(self.dataframe, text='selecteer', command=self.select_waypoint)
        self.select_waypoint_button.grid(row=r,column=1, padx=5, sticky=tk.E)

        buttonframe = tk.Frame(self)
        self.cancel_button = tk.Button(buttonframe, text='Cancel', command=self.destroy)
        self.cancel_button.grid(row=0, column=0, padx=5)
        self.ok_button = tk.Button(buttonframe, text='Opslaan', command=self.save_route)
        self.ok_button.grid(row=0,column=1, padx=5)
        buttonframe.grid(row=1,column=0, pady= 10)

        self.fill_optionmenu()

    def save_route(self):
        '''save the build route to the database'''
        self.parent.save_route(self.Route)

    def select_waypoint(self):
        '''save the waypoint selected in the optionmenu'''
        wp_name = self.selected_waypoint.get()
        UKC_value  = self.ukc_value_entry.get()
        UKC_id = self.UKC_ids_by_name[self.selected_UKC.get()]
        speed = self.speed_ids_by_name[self.selected_speed.get()]

        wp = self.tresholds[wp_name]
        self.Route.add_routepoint(wp.id, UKC_id, UKC_value, speed)
        self.last_waypoint = wp_name
        self.fill_optionmenu()
        self.waypoint_label.config(text="Volgende drempel:")

    def fill_optionmenu(self):
        '''fills the optionmenu with applicable waypoints'''
		#find last waypoint. If not set, give all waypoints
		#if set, find all connections with last waypoint and give waypoints that connect
        wp_list = self.find_connections(self.last_waypoint)
        #fill optionmenu
        menu = self.waypoint_option["menu"]
        menu.delete(0, 'end')
        for wp in wp_list:
            menu.add_command(label=wp, command=lambda wp=wp: self.selected_waypoint.set(wp))

        #select a waypoint that is not yet in the route (preferably)
        for i in range(0,len(wp_list)):
            self.selected_waypoint.set(wp_list[i])
            wp_id = self.treshold_ids_by_name[wp_list[i]]
            if not self.Route.route_holds_wp_id(wp_id):
                self.fill_data_fields()
                return

    def fill_data_fields(self, *args):
        '''fills the data fields with the right data'''
        wp_name = self.selected_waypoint.get()
        wp_id = self.treshold_ids_by_name[wp_name]
        wp = self.tresholds[wp_name]
        self.selected_speed.set(self.speeds[int(wp.speed_id)])
        self.selected_UKC.set(self.UKC_units[int(wp.UKC_unit_id)])
        self.ukc_value_entry.delete(0, tk.END)
        self.ukc_value_entry.insert(0,wp.UKC_value)

    def find_connections(self, wp=None):
        '''finds all connections to the given waypoint. If None, return all'''
        waypoints = []
        if wp == None:
            for w in self.tresholds.values():
                waypoints.append(w.name)
        else:
            wp_id = self.tresholds[wp].id
            for con in self.connections.values():
                if wp_id == con[0]:
                    waypoints.append(self.treshold_names_by_id[con[1]])
                elif wp_id == con[1]:
                    waypoints.append(self.treshold_names_by_id[con[0]])
        return waypoints

    def set_waypoint_name(self):
        '''sets the waypoint name'''
        routename = self.route_name_entry.get()
        if routename == '': return
        self.Route.name = routename
        self.routename_frame.grid_forget()
        self.dataframe.grid(row=0,column=0,padx=10,pady=10)
        self.route_name_label.configure(text=routename)

class modify_connection_toplevel(tk.Toplevel):
    def __init__(self, parent, title, waypoints):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        r = 0
        self.title(title)

        #make a list of waypoint names:
        self.waypoints = []
        for wp in waypoints.values():
            self.waypoints.append(wp.name)

        self.Treshold_1 = tk.StringVar(self)
        self.Treshold_1.set(self.waypoints[0])
        self.Treshold_1.trace("w", self.fill_tresholds_option)

        self.Treshold_2 = tk.StringVar(self)
        self.Treshold_2.set(self.waypoints[1])
        self.Treshold_2.trace("w", self.fill_tresholds_option)

        dataframe = tk.Frame(self)
        tk.Label(dataframe,text="Eerste drempel:").grid(row=r, column=0, sticky=tk.E)
        #optionmenu 1
        self.conn_treshold_1_option = tk.OptionMenu(dataframe, self.Treshold_1, *self.waypoints)
        self.conn_treshold_1_option.grid(row=r, column=1, sticky=tk.W)
        r += 1

        tk.Label(dataframe,text="Tweede drempel:").grid(row=r, column=0, sticky=tk.E)
        #optionmenu 2
        self.conn_treshold_2_option = tk.OptionMenu(dataframe, self.Treshold_2, "")
        self.conn_treshold_2_option.grid(row=r, column=1, sticky=tk.W)
        r += 1

        tk.Label(dataframe, text="Afstand:").grid(row=r, column=0, sticky=tk.E)
        self.distance_entry = tk.Entry(dataframe)
        self.distance_entry.grid(row=r, column=1)

        self.fill_tresholds_option()

        dataframe.grid(row=0, column=0, padx=10, pady=10)

        buttonframe = tk.Frame(self)
        self.cancel_button = tk.Button(buttonframe, text='Cancel', command=self.destroy)
        self.cancel_button.grid(row=0, column=0, padx=5)
        self.ok_button = tk.Button(buttonframe, text='Ok', command=self.parent.insert_connection_data)
        self.ok_button.grid(row=0,column=1, padx=5)
        buttonframe.grid(row=1,column=0, pady= 10)

    def fill_tresholds_option(self, *args):
        '''fill the treshold_1 optionmenu'''
        wp1 = self.Treshold_1.get()
        wp2 = self.Treshold_2.get()
        #delete all:
        menu1 = self.conn_treshold_1_option["menu"]
        menu2 = self.conn_treshold_2_option["menu"]
        menu1.delete(0,'end')
        menu2.delete(0,'end')

        for wp in self.waypoints:
            if wp != wp2:
                menu1.add_command(label=wp, command=lambda wp=wp: self.Treshold_1.set(wp))
        for wp in self.waypoints:
            if wp != wp1:
                menu2.add_command(label=wp, command=lambda wp=wp: self.Treshold_2.set(wp))


class modify_waypoint_toplevel(tk.Toplevel):
    def __init__(self, parent, user, title, UKC_units = None, deviations = None, tidal_points = None, speeds = None):
        tk.Toplevel.__init__(self,parent)
        self.parent = parent

        r = 0
        self.title(title)

        dataframe = tk.Frame(self)

        tk.Label(dataframe, text="Naam:").grid(row=r, column=0, sticky=tk.E)
        self.wp_name_entry = tk.Entry(dataframe)
        self.wp_name_entry.grid(row=r, column=1)
        r += 1

        if user == "admin":
            tk.Label(dataframe,text="Default snelheid:").grid(row=r, column=0, sticky=tk.E)
            self.Default_speed = tk.StringVar(self)
            self.Default_speed.set(speeds[min(speeds)])
            self.wp_speed_option = tk.OptionMenu(dataframe, self.Default_speed, *speeds.values())
            self.wp_speed_option.grid(row=r, column=1, sticky=tk.W)
            r += 1

        tk.Label(dataframe, text="Diepte afvarend:").grid(row=r, column=0, sticky=tk.E)
        self.wp_depth_outgoing_entry = tk.Entry(dataframe)
        self.wp_depth_outgoing_entry.grid(row=r, column=1)
        r += 1

        tk.Label(dataframe, text="Diepte opvarend:").grid(row=r, column=0, sticky=tk.E)
        self.wp_depth_ingoing_entry = tk.Entry(dataframe)
        self.wp_depth_ingoing_entry.grid(row=r, column=1)
        r += 1

        if user == "admin":
            tk.Label(dataframe,text="Afwijking waterstand:").grid(row=r, column=0, sticky=tk.E)
            self.deviation = tk.StringVar(self)
            self.deviation.set(deviations[min(deviations)])
            self.wp_deviation_option = tk.OptionMenu(dataframe, self.deviation, *deviations.values())
            self.wp_deviation_option.grid(row=r, column=1, sticky=tk.W)
            r += 1

            tk.Label(dataframe, text="UKC unit:").grid(row=r, column=0, sticky=tk.E)
            self.Default_UKC = tk.StringVar(self)
            self.Default_UKC.set(UKC_units[min(UKC_units)])
            self.wp_UKC_unit_option = tk.OptionMenu(dataframe, self.Default_UKC, *UKC_units.values())
            self.wp_UKC_unit_option.grid(row=r, column=1, sticky=tk.W)
            r += 1

            tk.Label(dataframe, text="UKC waarde:").grid(row=r, column=0, sticky=tk.E)
            self.wp_UKC_value_entry = tk.Entry(dataframe)
            self.wp_UKC_value_entry.grid(row=r, column=1)
            r += 1

            tk.Label(dataframe, text="getijdetabel:").grid(row=r, column=0, sticky=tk.E)
            self.tidal_point = tk.StringVar(self)
            self.tidal_point.set(tidal_points[min(tidal_points)])
            self.wp_tidal_point_option = tk.OptionMenu(dataframe, self.tidal_point, *tidal_points.values())
            self.wp_tidal_point_option.grid(row=r, column=1, sticky=tk.W)
            r += 1

        dataframe.grid(row=0, column=0, padx=10, pady=10)

        buttonframe = tk.Frame(self)
        self.cancel_button = tk.Button(buttonframe, text='Cancel', command=self.destroy)
        self.cancel_button.grid(row=0, column=0, padx=5)
        self.ok_button = tk.Button(buttonframe, text='Ok', command=self.parent.insert_waypoint_data)
        self.ok_button.grid(row=0,column=1, padx=5)
        buttonframe.grid(row=1,column=0, pady= 10)

class Find_Tidal_window_frame(tk.Frame):
    '''creates a frame that takes input variables for calculation and display results'''
    def __init__(self, parent):
        self.parent = parent
        tk.Frame.__init__(self, self.parent)

        self.timevalidate_command = (self.parent.register(self.__validate_time_in_entry), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.datevalidate_command = (self.parent.register(self.__validate_datetime_in_entry),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.floatvalidate_command = (self.parent.register(self.__validate_float_in_entry),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.integervalidate_command = (self.parent.register(self.__validate_integer_in_entry),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        next_eta_frame = tk.Frame(self)
        tk.Button(next_eta_frame, text="Bereken eerstvolgende tijpoort voor deze diepgang", command=self.__calculate_next_eta).grid(row=0, pady=5, padx=5, sticky=tk.W)
        self.next_eta_start_of_window_label = tk.Label(next_eta_frame)
        self.next_eta_start_of_window_label.grid(row=1, sticky=tk.W)
        self.next_eta_end_of_window_label = tk.Label(next_eta_frame)
        self.next_eta_end_of_window_label.grid(row=2, sticky=tk.W)
        next_eta_frame.grid(row=0, column=1, sticky=tk.N)

    def fill_data(self, routes, deviations, ship_types):
        self.routes = routes
        self.ship_types = ship_types
        self.deviations = deviations

        self.ship_types_names_by_id = {}
        self.ship_types_ids_by_name = {}
        for id, sht in self.ship_types.iteritems():
            self.ship_types_names_by_id[id] = sht[1]
            self.ship_types_ids_by_name[sht[1]] = id

        r = 0
        dataframe = tk.Frame(self)

        tk.Label(dataframe, text="ETA:").grid(row=r, column=0, sticky=tk.E)
        self.ETA_entry = tk.Entry(dataframe, validate="all", validatecommand=self.datevalidate_command)
        self.ETA_entry.grid(row=r, column=1)
        n = datetime.datetime.now()
        eta_string = "{d}-{m}-{y} {h}:{n}".format(d=n.day, m=n.month, y=n.year, h=n.hour, n=str(n.minute).zfill(2))
        self.ETA_entry.insert(0, eta_string)
        r += 1

        tk.Label(dataframe,text="Route:").grid(row=r, column=0, sticky=tk.E)
        self.selected_route = tk.StringVar(self)
        #{u'KB-ZV': <Routing.Route instance at 0x02C0EAD0>}
        self.selected_route.set(self.routes.keys()[0])
        self.route_option = tk.OptionMenu(dataframe, self.selected_route, *self.routes.keys())
        self.route_option.grid(row=r, column=1, sticky=tk.W)
        r += 1

        tk.Label(dataframe,text="Scheepstype:").grid(row=r, column=0, sticky=tk.E)
        self.selected_ship_type = tk.StringVar(self)
        self.selected_ship_type.set(self.ship_types_names_by_id.values()[0])
        self.ship_types_option = tk.OptionMenu(dataframe, self.selected_ship_type, *self.ship_types_names_by_id.values())
        self.ship_types_option.grid(row=r, column=1, sticky=tk.W)
        r += 1

        tk.Label(dataframe, text="Diepgang:").grid(row=r, column=0, sticky=tk.E)
        self.draught_entry = tk.Entry(dataframe, validate="all", validatecommand=self.floatvalidate_command)
        self.draught_entry.grid(row=r, column=1)
        self.draught_entry.insert(0, "100.0")
        r += 1

        #1 label / entry combo for each deviation.
        #{1: u'Vlissingen', 2: u'Bath'}
        self.dev_dict = {}
        for id, val in self.deviations.iteritems():
            tk.Label(dataframe, text="afwijking {dev_name}:".format(dev_name=val)).grid(row=r, column=0, sticky=tk.E)
            self.dev_dict[id] = tk.Entry(dataframe, validate="all", validatecommand=self.integervalidate_command)
            self.dev_dict[id].grid(row=r, column=1, sticky=tk.W)
            self.dev_dict[id].insert(0, "0")
            r += 1

        tk.Label(dataframe, text="Tijpoort voor het ship:").grid(row=r, column=0, sticky=tk.E)
        self.window_before_vessel_entry = tk.Entry(dataframe, validate="all", validatecommand=self.timevalidate_command)
        self.window_before_vessel_entry.grid(row=r, column=1)
        self.window_before_vessel_entry.insert(0, "01:00")
        r += 1

        tk.Label(dataframe, text="Tijpoort na het schip:").grid(row=r, column=0, sticky=tk.E)
        self.window_after_vessel_entry = tk.Entry(dataframe, validate="all", validatecommand=self.timevalidate_command)
        self.window_after_vessel_entry.grid(row=r, column=1)
        self.window_after_vessel_entry.insert(0, "00:00")
        r += 1

        dataframe.grid(row=0, column=0, padx=10, pady=10)

    def __get_parameters(self):
        '''gets all parameters from the entrys and optionmenus'''
        ship_type_id =  self.ship_types_ids_by_name[self.selected_ship_type.get()]
        self.input_ship_type = self.ship_types[ship_type_id]

        self.input_route = self.routes[self.selected_route.get()]

        self.input_draught = float(self.draught_entry.get())

        eta_string = self.ETA_entry.get()
        date = eta_string.split(" ")[0]
        time = eta_string.split(" ")[1]

        day = date.split("-")[0]
        day = int(day)
        month = date.split("-")[1]
        month = int(month)
        year = date.split("-")[2]
        year = int(year)

        hours = time.split(":")[0]
        hours = int(hours)
        minutes = time.split(":")[1]
        minutes = int(minutes)

        eta = datetime.datetime(year,month,day,hours,minutes,0)
        self.input_eta_GMT = convert_local_time_to_UTC(eta)

        hours = self.window_before_vessel_entry.get().split(":")[0]
        minutes = self.window_before_vessel_entry.get().split(":")[1]
        #confusing: window before vessel means window after eta and vv
        self.input_time_window_after_eta = datetime.timedelta(hours=int(hours), minutes=int(minutes))

        hours = self.window_after_vessel_entry.get().split(":")[0]
        minutes = self.window_after_vessel_entry.get().split(":")[1]

        self.input_time_window_before_eta = datetime.timedelta(hours=int(hours), minutes=int(minutes))

        self.input_deviations = {}
        for id, val in self.dev_dict.iteritems():
            self.input_deviations[id] = int(val.get())

    def __calculate_next_eta(self):
        '''construct the parameters to do the tidal calculations'''
        self.__get_parameters()
        window = self.parent.calculate_first_possible_window(ship_type=self.input_ship_type,
                                            draught=self.input_draught,
                                            route=self.input_route,
                                            eta=self.input_eta_GMT,
                                            time_window_before_eta=self.input_time_window_before_eta,
                                            time_window_after_eta=self.input_time_window_after_eta,
                                            deviations=self.input_deviations)
        if window != None:
            #convert window to local time:
            self.next_eta_start_of_window_label.config(text="begin tijpoort: {d.day}-{d.month} {d.hour}:{d.minute:02}".format(d=convert_UTC_to_local_time(window[0])))
            self.next_eta_end_of_window_label.config(text="einde tijpoort: {d.day}-{d.month} {d.hour}:{d.minute:02}".format(d=convert_UTC_to_local_time(window[1])))

    def __validate_integer_in_entry(self, d, i, P, s, S, v, V, W):
        #make sure there can be only one decimal point in the string
        if d == '1' and S == "-" and i == '0' and not "-" in s:
            return True
        #make sure only numbers are inserted or deleted
        if d == "1" and not self.__is_number(S):
            return False

        return True

    def __validate_float_in_entry(self, d, i, P, s, S, v, V, W):
        #if the entry is empty, allow entry of default string
        if s == "":
            return True

        #make sure there can be only one decimal point in the string
        if d == '1' and ("." in S):
            return ("." in P) and not ("." in s)

        #make sure only numbers are inserted or deleted
        if (d == "1" or d == "0") and not self.__is_number(S):
            return False

        if not (self.__is_number(P)):
            return False

        if len(P) == 0 or float(P) <= 0:
            return False

        return True

    def __validate_datetime_in_entry(self, d, i, P, s, S, v, V, W):
##        print "OnValidate:"
##        print "d='%s'" % d
##        print "i='%s'" % i
##        print "P='%s'" % P
##        print "s='%s'" % s
##        print "S='%s'" % S
##        print "v='%s'" % v
##        print "V='%s'" % V
##        print "W='%s'" % W
        # %d = Type of action (1=insert, 0=delete, -1 for others)
        # %i = index of char string to be inserted/deleted, or -1
        # %P = value of the entry if the edit is allowed
        # %s = value of entry prior to editing
        # %S = the text string being inserted or deleted, if any
        # %v = the type of validation that is currently set
        # %V = the type of validation that triggered the callback
        #      (key, focusin, focusout, forced)
        # %W = the tk name of the widget

        #if the entry is empty, allow entry of default string
        if s == "":
            return True

        #make sure only numbers are inserted or deleted
        if (d == "1" or d == "0") and not self.__is_number(S):
            return False

        date = P.split(" ")[0]
        time = P.split(" ")[1]

        day = date.split("-")[0]
        month = date.split("-")[1]
        year = date.split("-")[2]

        hours = time.split(":")[0]
        minutes = time.split(":")[1]

        #check lenght of data
        if len(day) > 2 or len(month) > 2 or len(year) > 4:
            return False
        if len(hours) > 2 or len(minutes) > 2:
            return False

        #check day (between 1 and 31)
        if len(day) > 0 and(int(day) > 31 or int(day) < 1):
            return False
        #check month (between 1 and 12)
        if len(month) > 0 and(int(month) > 12 or int(month) < 1):
            return False

        #make sure hours are between 0 and 23
        if len(hours) > 0 and (int(hours) > 23 or int(hours) < 0):
            return False
        #make sure minutes are between 0 and 59
        if len(minutes) > 0 and (int(minutes) > 59 or int(minutes) < 0):
            return False

        if V == "focusout":
            if len(hours) < 2:
                hours = "0" + hours
            if len(minutes) == 0:
                minutes = "00"
            elif len(minutes) == 1:
                minutes = "0" + minutes

            year = "2014"
            if len(month) == 0:
                month = 1

            last_day_of_month = calendar.monthrange(int(year), int(month))[1]
            if len(day) == 0:
                day = 1
            elif int(day) > last_day_of_month:
                day = last_day_of_month

            self._nametowidget(W).delete(0, tk.END)
            eta_string = "{d}-{m}-{y} {h}:{n}".format(d=day, m=month, y=year, h=hours, n=minutes)
            self._nametowidget(W).insert(0, eta_string)
            self.after_idle(lambda: self._nametowidget(W).config(validate="all"))
            return None


        return True


    def __validate_time_in_entry(self, d, i, P, s, S, v, V, W):

        #make sure there is one colon (and only one) in the string
        if d == '0' and (":" in S):
            return (":" in P)
        elif d == '1' and (":" in S):
            return (":" in P) and not (":" in s)

        hours = P.split(":")[0]
        minutes = P.split(":")[1]
        #make sure the hours and minutes are not more then 2 digits
        if len(hours) > 2 or len(minutes) > 2:
            return False

        #make sure hours and minutes are both numbers:
        if not self.__is_number(hours) or not self.__is_number(minutes):
            return False
        #make sure hours are between 0 and 23
        if len(hours) > 0 and (int(hours) > 23 or int(hours) < 0):
            return False
        #make sure minutes are between 0 and 59
        if len(minutes) > 0 and (int(minutes) > 59 or int(minutes) < 0):
            return False

        if V == "focusout":
            if len(hours) < 2:
                hours = "0" + hours
            if len(minutes) == 0:
                minutes = "00"
            elif len(minutes) == 1:
                minutes = "0" + minutes
            self._nametowidget(W).delete(0, tk.END)
            self._nametowidget(W).insert(0, "{h}:{m}".format(h=hours, m=minutes))
            self.after_idle(lambda: self._nametowidget(W).config(validate="all"))
            return None

        return True


    def __is_number(self, s):
        if s == "": return True
        try:
            float(s)
            return True
        except ValueError:
            return False

class TidalGraphCanvas(tk.Canvas):
    def __init__(self, *args, **kwargs):
        '''A custom canvas that generates <<ScrollEvent>> events whenever
           the canvas scrolls by any means (scrollbar, key bindings, etc)
        '''
        tk.Canvas.__init__(self, *args, **kwargs)

        # replace the underlying tcl object with our own function
        # so we can generate virtual events when the object scrolls
        tcl='''
            proc widget_proxy {actual_widget args} {
                set result [$actual_widget {*}$args]
                set command [lindex $args 0]
                set subcommand [lindex $args 1]
                if {$command in {xview yview} && $subcommand in {scroll moveto}} {
                    # widget has been scrolled; generate an event
                    event generate {widget} <<ScrollEvent>>
                }
                return $result
            }

            rename {widget} _{widget}
            interp alias {} ::{widget} {} widget_proxy _{widget}
        '''.replace("{widget}", str(self))
        self.tk.eval(tcl)

class TidalWindowsGraphFrame(tk.Frame):
    '''creates a frame with a canvas, that shows the tidal windows graphical'''
    def __init__(self, parent):
        self.parent = parent
        tk.Frame.__init__(self, parent)

        self.canvas_height = 4000
        self.canvas_view_height = 500
        self.canvas_width = 1200
        self.canvas_left_side_margin = 50
        self.canvas_right_side_margin = 10
        self.canvas_drawable_width = self.canvas_width - self.canvas_left_side_margin - self.canvas_right_side_margin
        self.canvas_treshold_column_width = 10

        self.canvas = TidalGraphCanvas(self,
                                        height=self.canvas_view_height,
                                        width=self.canvas_width,
                                        bg="white",
                                        relief=tk.SUNKEN,
                                        scrollregion=(0,0, self.canvas_width, self.canvas_height))
        self.sbar = tk.Scrollbar(self)
        self.sbar.config(command=self.canvas.yview)

        self.canvas.config(yscrollcommand=self.sbar.set)
        self.bind_all("<MouseWheel>", self.__on_mousewheel)
        self.canvas.bind("<<ScrollEvent>>", self.__on_canvas_scroll)

    def __on_canvas_scroll(self, event):
        y = self.canvas.yview()[0] * self.canvas_height + 5
        for label in self.canvas_labels:
            x = self.canvas.coords(label)[0]
            self.canvas.coords(label, x, y)

    def __on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta/120), "units")

    def fill_tidal_graph(self, tidal_calc):
        '''fills the graph with tidal windows'''
        self.canvas.delete(tk.ALL)
        self.canvas_labels = []

        #GET SOME DATA
        imin = min(tidal_calc.route_windows.keys())
        imax = max(tidal_calc.route_windows.keys())
        self.total_route_length = tidal_calc.route_windows[imax].distance_to_here

        if tidal_calc.global_window != None:
            self.global_tidal_window_LT = [convert_UTC_to_local_time(d) for d in tidal_calc.global_window]

        self.eval_startdate_LT = convert_UTC_to_local_time(tidal_calc.route_windows[imax].eval_startdate)
        self.eval_enddate_LT = convert_UTC_to_local_time(tidal_calc.route_windows[imax].eval_enddate)
        self.ETA_LT = convert_UTC_to_local_time(tidal_calc.ETA)

        #LOOP ROUTEPOINTS TO DRAW THE COLUMNS (RED/GREEN)
        for i in range(imin, imax +1):
            rp = tidal_calc.route_windows[i]
            self.__draw_treshold_column(rp)

        #PRINT DATE AND TIME LINES UNDER THE COLUMNS:
        d = datetime.datetime.combine(self.eval_startdate_LT.date(), datetime.time(0,0,0))
        d += datetime.timedelta(hours=24)
        while d.date() <= self.eval_enddate_LT.date():
            y = self.__draw_height(d)
            dateline = self.canvas.create_line(0, y, self.canvas_drawable_width + self.canvas_left_side_margin, y)
            datestring = "{day}-{month}".format(day=d.day, month=d.month)
            self.canvas.create_text(0,y, text=datestring, anchor=tk.SW)
            self.canvas.lower(dateline)
            t = d + datetime.timedelta(hours=3)
            while t < self.eval_enddate_LT and t < d + datetime.timedelta(hours=24):
                y = self.__draw_height(t)
                timeline = self.canvas.create_line(0, y, self.canvas_drawable_width + self.canvas_left_side_margin, y, dash=(2, 4))
                timestring = "{h}:00".format(h=t.hour)
                self.canvas.create_text(self.canvas_left_side_margin,y, text=timestring, anchor=tk.SE)
                self.canvas.lower(timeline)
                t += datetime.timedelta(hours=3)
            d += datetime.timedelta(hours=24)

        #LOOP ROUTEPOINTS TO DRAW THE (GLOBAL) TIDAL WINDOW (IF ANY) AND THE ETA LINES:
        if self.global_tidal_window_LT != None:
            print "Global window:", self.global_tidal_window_LT[0], self.global_tidal_window_LT[1]
        else:
            print "No Global window"
        time_to_last = datetime.timedelta(0)
        distance_to_last = 0
        for i in range(imin + 1, imax + 1):
            rp = tidal_calc.route_windows[i]
            if self.global_tidal_window_LT != None:
                self.__draw_tidal_window(rp, time_to_last, distance_to_last)
            self.__draw_eta_line(rp, time_to_last, distance_to_last)
            time_to_last = rp.time_to_here
            distance_to_last = rp.distance_to_here

        #SET CANVAS VIEW TO THE ETA LINE:
        fraction = (self.__draw_height(self.ETA_LT) - (self.canvas_view_height / 2)) / self.canvas_height
        self.canvas.yview_moveto(fraction)

        #INSERT CANVAS AND SCROLLBAR
        self.sbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, expand=tk.YES,fill=tk.BOTH)

    def __draw_eta_line(self, rp, time_to_last, distance_to_last):
        '''draws the eta as a line on top of the columns'''
        x1 = self.__left_of_treshold(distance_to_last)
        y1 = self.__draw_height(self.ETA_LT + time_to_last)
        x2 = self.__left_of_treshold(rp.distance_to_here)
        y2 = self.__draw_height(self.ETA_LT + rp.time_to_here)
        self.canvas.create_line(x1, y1, x2, y2, width=3)

    def __draw_tidal_window(self, rp, time_to_last, distance_to_last):
        '''draws a shape on the canvas, indicating the found window'''
        left1 = self.__left_of_treshold(distance_to_last)
        left2 = self.__left_of_treshold(rp.distance_to_here)
        nw_y = self.__draw_height(self.global_tidal_window_LT[1] + time_to_last)
        sw_y = self.__draw_height(self.global_tidal_window_LT[0] + time_to_last)
        ne_y = self.__draw_height(self.global_tidal_window_LT[1] + rp.time_to_here)
        se_y = self.__draw_height(self.global_tidal_window_LT[0] + rp.time_to_here)
        window = self.canvas.create_polygon(left1, nw_y, left1, sw_y, left2, se_y, left2, ne_y, fill="lightBlue")
        self.canvas.lower(window)

    def __left_of_treshold(self, distance):
        '''returns the left side of the treshold column'''
        return self.canvas_left_side_margin + (self.canvas_drawable_width / self.total_route_length) * distance

    def __draw_height(self, date):
        '''returns the height to draw from the given date'''
        seconds = (self.eval_enddate_LT - self.eval_startdate_LT).total_seconds()
        h_per_sec = self.canvas_height / seconds
        return self.canvas_height - (date - self.eval_startdate_LT).total_seconds() * h_per_sec

    def __draw_treshold_column(self, rp):
        '''draws the treshold column'''
        left = self.__left_of_treshold(rp.distance_to_here)

        canvas_text = self.canvas.create_text(left + 2 ,5,  text="\n".join(rp.treshold_name), anchor="nw")
        self.canvas_labels.append(canvas_text)

        #CHECK IF THERE ARE ANY TIDAL WINDOWS (TIDAL_WINDOWS != NONE)
        if rp.tidal_windows == None:
            self.canvas.create_rectangle(left, 0, left + self.canvas_treshold_column_width, self.canvas_height, fill="red")
            self.canvas.tag_raise(canvas_text)
            return

        #CHECK IF FIRST PART (FROM EVAL_STARTDATE) IS GREEN OR RED:
        if self.eval_startdate_LT < convert_UTC_to_local_time(rp.tidal_windows[0][0]):
            x = self.__draw_height(convert_UTC_to_local_time(rp.tidal_windows[0][0]))
            self.canvas.create_rectangle(left, self.canvas_height, left + self.canvas_treshold_column_width, x, fill="red")

        #DRAW THE REST OF THE WINDOWS:
        end_of_last_window_LT = None
        for w in rp.tidal_windows:
            x0 = self.__draw_height(convert_UTC_to_local_time(w[0]))
            x1 = self.__draw_height(convert_UTC_to_local_time(w[1]))
            self.canvas.create_rectangle(left, x0, left + self.canvas_treshold_column_width, x1, fill="green")
            if end_of_last_window_LT != None:
                x00 = self.__draw_height(end_of_last_window_LT)
                self.canvas.create_rectangle(left, x00, left + self.canvas_treshold_column_width, x0, fill="red")
            end_of_last_window_LT = convert_UTC_to_local_time(w[1])

        #DRAW THE LAST RED (IF APPLICABLE)
        if end_of_last_window_LT < self.eval_enddate_LT:
            x = self.__draw_height(end_of_last_window_LT)
            self.canvas.create_rectangle(left, x, left + self.canvas_treshold_column_width, 0, fill="red")

        self.canvas.tag_raise(canvas_text)


class StatusBar(tk.Frame):

    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.label = tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.label.pack(fill=tk.X)

    def set(self, format, *args):
        self.label.config(text=format % args)
        self.label.update_idletasks()

    def clear(self):
        self.label.config(text="")
        self.label.update_idletasks()

class MenuBar(tk.Menu):
    '''The menubar for the application'''
    def __init__(self, parent):
        self.parent = parent
        tk.Menu.__init__(self, self.parent)

        fileMenu = tk.Menu(self)
        fileMenu.add_command(label="Exit", command=parent.onExit)
        dataMenu = tk.Menu(self)
        dataMenu.add_command(label="configuratie", command=lambda: parent.set_program_state("config"))
        dataMenu.add_command(label="berekeningen", command=lambda: parent.set_program_state("calculate"))
        loginMenu = tk.Menu(self)
        loginMenu.add_command(label="login scherm", command=parent.display_login_screen)

        self.add_cascade(label="File", menu=fileMenu)
        self.add_cascade(label="Data", menu=dataMenu)
        self.add_cascade(label="Login", menu=loginMenu)

class MultiListbox(tk.Frame):
    '''A multilistbox'''
    def __init__(self, master, lists):
      tk.Frame.__init__(self, master)
      self.lists = []
      for l,w in lists:
          frame = tk.Frame(self); frame.pack(side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)
          tk.Label(frame, text=l, borderwidth=1, relief=tk.RAISED).pack(fill=tk.X)
          lb = tk.Listbox(frame, width=w, borderwidth=0, selectborderwidth=0,
                   relief=tk.FLAT, exportselection=tk.FALSE)
          lb.pack(expand=tk.YES, fill=tk.BOTH)
          self.lists.append(lb)
          lb.bind('<B1-Motion>', lambda e, s=self: s._select(e.y))
          lb.bind('<Button-1>', lambda e, s=self: s._select(e.y))
          lb.bind('<Leave>', lambda e: 'break')
          lb.bind('<B2-Motion>', lambda e, s=self: s._b2motion(e.x, e.y))
          lb.bind('<Button-2>', lambda e, s=self: s._button2(e.x, e.y))
      frame = tk.Frame(self); frame.pack(side=tk.LEFT, fill=tk.Y)
      tk.Label(frame, borderwidth=1, relief=tk.RAISED).pack(fill=tk.X)
      sb = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self._scroll)
      sb.pack(expand=tk.YES, fill=tk.Y)
      self.lists[0]['yscrollcommand']=sb.set

    def _select(self, y):
      row = self.lists[0].nearest(y)
      self.selection_clear(0, tk.END)
      self.selection_set(row)
      return 'break'

    def _button2(self, x, y):
      for l in self.lists: l.scan_mark(x, y)
      return 'break'

    def _b2motion(self, x, y):
      for l in self.lists: l.scan_dragto(x, y)
      return 'break'

    def _scroll(self, *args):
      for l in self.lists:
          apply(l.yview, args)

    def curselection(self):
      return self.lists[0].curselection()

    def delete(self, first, last=None):
      for l in self.lists:
          l.delete(first, last)

    def get(self, first, last=None):
      result = []
      for l in self.lists:
          result.append(l.get(first,last))
      if last: return apply(map, [None] + result)
      return result

    def index(self, index):
      self.lists[0].index(index)

    def insert(self, index, *elements):
      for e in elements:
          i = 0
          for l in self.lists:
            l.insert(index, e[i])
            i = i + 1

    def size(self):
      return self.lists[0].size()

    def see(self, index):
      for l in self.lists:
          l.see(index)

    def selection_anchor(self, index):
      for l in self.lists:
          l.selection_anchor(index)

    def selection_clear(self, first, last=None):
      for l in self.lists:
          l.selection_clear(first, last)

    def selection_includes(self, index):
      return self.lists[0].selection_includes(index)

    def selection_set(self, first, last=None):
      for l in self.lists:
          l.selection_set(first, last)


if __name__ == '__main__':
    pass