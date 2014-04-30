#-------------------------------------------------------------------------------
# Name:        Tidal_calculations.py
# Purpose:
#
# Author:      hvl
#
# Created:     10-04-2014
# Copyright:   (c) hvl 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import sqlite3
import datetime
import pandas
import numpy

class TidalcalculationError(Exception):
    pass



class Tidal_calc():
    def __init__(self, parent,
                route,
                waypoints,
                connections,
                ukc_units,
                speeds,
                deviations,
                ship_type,
                draught,
                ETA,
                min_tidal_window_before_ETA,
                min_tidal_window_after_ETA,
                panda_timeframes):
        self.parent = parent
        self.route = route
        self.waypoints = waypoints
        self.connections = connections
        self.UKC_units = ukc_units
        self.speeds = speeds
        self.deviations = deviations
        self.ship_type = ship_type
        self.draught = draught
        self.ETA = ETA
        self.min_tidal_window_before_ETA = min_tidal_window_before_ETA
        self.min_tidal_window_after_ETA = min_tidal_window_after_ETA
        self.panda_dict = panda_timeframes

        self.waypoint_names_by_id = {}
        for wp in self.waypoints.values():
            self.waypoint_names_by_id[wp.id] = wp.name

        self.__fill_route_dict()
        self.global_eta = None

    def __fill_route_dict(self):
        '''loop routepoints in the route and fill a dict with classes'''
        self.route_windows = {}
        distance_total = 0
        time_elapsed = datetime.timedelta(hours=0, minutes=0, seconds=0)
        last_routepoint_id = -1
        for i in range(1, self.route.amount_of_routepoints + 1):
            rp = self.route.routepoints[i]
            rp_id = rp["id"]
            rp_name = self.waypoint_names_by_id[rp_id]
            rp_ukc_unit_id = rp["UKC_unit_id"]
            rp_UKC_unit = self.UKC_units[rp_ukc_unit_id]
            rp_UKC_value = rp["UKC_value"]
            #ukc in meters:
            if rp_UKC_unit == "m":
                rp_UKC_in_meters = rp_UKC_value
            else:
                rp_UKC_in_meters = rp_UKC_value / 100 * self.draught
            #speed in knots:
            rp_speed = self.__get_speed(rp["speed_id"])
            if last_routepoint_id > -1:
                distance = self.__get_distance_from_connections(rp_id, last_routepoint_id)
                timediff = datetime.timedelta(hours=distance/last_routepoint_speed)
                #time since start of route:
                time_elapsed += timediff
                #distance in miles:
                distance_total += distance
            treshold = self.waypoints[rp_name]
            #name of treshold:
            treshold_name = treshold.name
            #tidal point id:
            tidal_point_id = treshold.tidal_point_id
            #depth:
            if self.route.route_is_ingoing:
                depth = treshold.depth_ingoing
            else:
                depth = treshold.depth_outgoing
            deviation = self.deviations[treshold.deviation_id]
            last_routepoint_speed = rp_speed
            last_routepoint_id = rp_id
            self.route_windows[i] = route_point_tidal_data(parent=self,
                                                            treshold_name=rp_name,
                                                            treshold_depth=depth,
                                                            treshold_deviation=deviation,
                                                            tidal_point=tidal_point_id,
                                                            draught=self.draught,
                                                            UKC_in_meters=rp_UKC_in_meters,
                                                            ETA=self.ETA,
                                                            min_tidal_window_before_ETA=self.min_tidal_window_before_ETA,
                                                            min_tidal_window_after_ETA=self.min_tidal_window_after_ETA,
                                                            distance_to_here=distance_total,
                                                            time_to_here=time_elapsed,
                                                            panda_timeframes=self.panda_dict)

    def get_global_window(self):
        '''finds the global tidal window. self.global_eta must be set'''
        self.global_window = None
        #THROW AN ERROR IF ETA IS NOT CALCULATED
        if self.global_eta == None:
            raise TidalcalculationError("No ETA was calculated")
        #IF THERE IS NO LOCAL WINDOW FOR THE FIRST ROUTE POINT, RETURN NONE:
        if self.route_windows[1].local_tidal_window == None:
            return
        start_of_global_window = self.route_windows[1].local_tidal_window[0] - self.route_windows[1].time_to_here
        end_of_global_window = self.route_windows[1].local_tidal_window[1] - self.route_windows[1].time_to_here
        #LOOP ALL ROUTEPOINTS TO SEE IF THE GLOBAL WINDOW MUST BE ADJUSTED:
        for rp in self.route_windows.values():
            if rp.local_tidal_window == None:
                return
            if start_of_global_window < rp.local_tidal_window[0] - rp.time_to_here:
                start_of_global_window = rp.local_tidal_window[0] - rp.time_to_here
            if end_of_global_window > rp.local_tidal_window[1] - rp.time_to_here:
                end_of_global_window = rp.local_tidal_window[1] - rp.time_to_here
            if start_of_global_window > end_of_global_window:
                return None
        #STORE THE GLOBAL WINDOW:
        self.global_window = [start_of_global_window, end_of_global_window]

    def calculate_first_possible_ETA(self):
        '''finds a global eta that gives a sufficient window on all routepoints'''
        self.global_eta = None
        test_ETA = self.ETA
        imin = min(self.route_windows.keys())
        imax = max(self.route_windows.keys())
        settled = False
        while not settled:
            settled = True
            for i in range(imin, imax + 1):
                rp = self.route_windows[i]
                found_eta = rp.first_tidal_window_available_after_time(test_ETA)
                if found_eta == None:
                    return None
                if found_eta > test_ETA:
                    test_ETA = found_eta
                    settled = False
                    break
        self.global_eta = test_ETA

    def __get_speed(self, speed_id):
        '''returns the speed value derived from the speed id and the ship type'''
        return self.ship_type[speed_id + 1]

    def __get_distance_from_connections(self, id_1, id_2):
        '''will return the distance between the 2 wp id's'''
        for con in self.connections.values():
            if (id_1 == con[0] and id_2 == con[1]) or (id_1 == con[1] and id_2 == con[0]):
                return con[2]



class route_point_tidal_data():
    '''class that will make the actual queries about the tidal windows'''
    def __init__(self, parent,
                 treshold_name,
                 treshold_depth,
                 treshold_deviation,
                 tidal_point,
                 draught,
                 UKC_in_meters,
                 ETA,
                 min_tidal_window_before_ETA,
                 min_tidal_window_after_ETA,
                 distance_to_here,
                 time_to_here,
                 panda_timeframes
                 ):
        self.parent = parent
        self.treshold_name = treshold_name
        self.treshold_depth = treshold_depth
        self.treshold_deviation = treshold_deviation
        self.tidal_point = tidal_point
        self.draught = draught
        self.UKC = UKC_in_meters
        self.ETA = ETA
        self.min_window_before_ETA = min_tidal_window_before_ETA
        self.min_window_after_ETA = min_tidal_window_after_ETA
        self.distance_to_here = distance_to_here
        self.time_to_here = time_to_here
        self.local_ETA = self.ETA + self.time_to_here
        self.panda_dict = panda_timeframes
        #variable that indicates all of the tidal curve is below the needed rise:
        self.no_tidal_window_possible = False
        #variable that indicates all of the tidal curve is above the needed rise:
        self.passage_always_possible = False
        #list with possible windows for this point:
        self.tidal_windows = []
        #list of 2 datetime objects, defining the tidal window in effect for this treshold
        self.local_tidal_window = None
        self.needed_rise = self.draught + self.UKC - (self.treshold_depth + self.treshold_deviation)
        self.__get_tidal_windows()

    def __get_tidal_windows(self):
        '''will retreive all tidal windows for the given ETA and one week ahead (2 days before)'''
        startdate = self.ETA

        #GET PANDAS TIMEFRAME OF CURRENT TIDAL POINT:
        table_name = "TDP_{id}_Tidal_Data".format(id=self.tidal_point)
        tf = self.panda_dict[table_name]

        #CREATE TESTING TIMEFRAME OF 2 DAYS BEFORE AND 7 DAYS FROM ETA:
        self.eval_startdate = startdate - datetime.timedelta(days=2)
        d1 = unicode(self.eval_startdate)
        self.eval_enddate = startdate + datetime.timedelta(days=7)
        d2 = unicode(self.eval_enddate)
        test_tf = tf[(tf.datetime > d1) & (tf.datetime < d2)]

        #TEST IF ALL OF THE TEST TIMEFRAME IS ABOVE THE NEEDED RISE:
        if test_tf[test_tf.rise < self.needed_rise].empty:
            self.tidal_windows.append([self.eval_startdate, self.eval_enddate])
            return

        #TEST IF ALL OF THE TEST TIMEFRAME IS BELOW THE NEEDED RISE:
        if test_tf[test_tf.rise > self.needed_rise].empty:
            self.tidal_windows = None
            return

        #GET TIME VALUES OF CROSSING POINTS (WITH UP/DOWN INDICATOR)
        crossings =  self.cross(test_tf,self.needed_rise)

        #IF FIRST CROSSING IS DOWN, EVAL_STARTDATE IS BEGINNING OF TIDALFRAME.
        if crossings[0][0] == 'DOWN':
            self.tidal_windows.append([self.eval_startdate, crossings[0][1]])
            start_i = 1
        else:
            start_i = 0

        for i in range(start_i, len(crossings), 2):
            d0 = crossings[i][1]
            if i == len(crossings) -1:
                d1 = self.eval_enddate
            else:
                d1 = crossings[i+1][1]
            self.tidal_windows.append([d0,d1])

    def __interpolate_rise_value(self, d0, d1, r0, r1, dx):
        '''function to interpolate a rise from a given datetime value (dx)'''
        sec_total = (d1 - d0).total_seconds()
        sec_x = (dx - d0).total_seconds()
        dr = r1 - r0
        return dr * (sec_x / sec_total) + r0

    def __interpolate_datetime_value(self, d0, d1, r0, r1, rx):
        '''function to interpolate a datetime from a given rise value (rx)'''
        sec_total = (d1 - d0).total_seconds()
        r_total = r1 - r0
        r_x = rx - r0
        sec_x = sec_total * (r_x / r_total)
        return d0 + datetime.timedelta(seconds=sec_x)

    def __make_datetime_from_db_val(self, time):
        '''returns a datetime value'''
        return datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S")

    def cross(self, series, cross=0, direction='cross'):
        """
        Given a Series returns all the index values where the data values equal
        the 'cross' value.

        Direction can be 'rising' (for rising edge), 'falling' (for only falling
        edge), or 'cross' for both edges
        """
        # Find if values are above or bellow yvalue crossing:
        above=series.values > cross
        below= numpy.logical_not(above)
        left_shifted_above = above[1:]
        left_shifted_below = below[1:]
        x_crossings = []
        # Find indexes on left side of crossing point
        if direction == 'rising':
            idxs = (left_shifted_above & below[0:-1]).nonzero()[0]
        elif direction == 'falling':
            idxs = (left_shifted_below & above[0:-1]).nonzero()[0]
        else:
            rising = left_shifted_above & below[0:-1]
            falling = left_shifted_below & above[0:-1]
            idxs = (rising | falling).nonzero()[0]

        # Calculate x crossings with interpolation using formula for a line:
        x1 = series.index.values[idxs]
        x2 = series.index.values[idxs+1]
        y1 = series.values[idxs]
        y2 = series.values[idxs+1]
        result = []
        for i in range(0,len(x1)):
            d0 = self.__make_datetime_from_db_val(y1[i][0])
            d1 = self.__make_datetime_from_db_val(y2[i][0])
            d = self.__interpolate_datetime_value(d0,d1,y1[i][1],y2[i][1],cross)
            if y1[i][1] < y2[i][1]:
                result.append(['UP', d])
            else:
                result.append(['DOWN', d])
        return result


    def first_tidal_window_available_after_time(self, time):
        '''returns the first tidal window available (returns the eta starting point)'''
        #time is the global ETA
        starttime = time + self.time_to_here
        start_of_window = starttime - self.min_window_before_ETA
        end_of_window = starttime + self.min_window_after_ETA

        if self.tidal_windows == None:
            self.local_tidal_window = None
            return None

        for w in self.tidal_windows:
            #DISCARD WINDOWS BEFORE TIME:
            if w[1] < starttime:
                continue
            #CHECK IF CURRENT TIME IS IN A VALID WINDOW:
            if w[0] <= start_of_window and w[1] >= end_of_window:
                self.local_tidal_window = w
                return w[0] + self.min_window_before_ETA - self.time_to_here
            #FIND NEXT WINDOW AND RETURN FIRST POSSIBLE TIME:
            else:
                if (w[1] - w[0] >= self.min_window_before_ETA + self.min_window_after_ETA) and \
                        (w[1] >= end_of_window):
                    self.local_tidal_window = w
                    return w[0] + self.min_window_before_ETA - self.time_to_here


##    def has_tidal_window_around_local_ETA(self):
##        '''returns true if the ETA fits in a valid tidal window'''
##        c = self.memory_database.cursor()
##        table_name = "TDP_{id}_Tidal_Data".format(id=self.tidal_point)
##        startdate = self.local_ETA - self.min_window_before_ETA
##        enddate = self.local_ETA + self.min_window_after_ETA
##        sql = "SELECT * FROM {table} WHERE datetime BETWEEN '{start}' AND '{end}';".format(table=table_name, start=startdate, end=enddate)
##        c.execute(sql)
##        print "needed rise: ", self.needed_rise
##        for r in c:
##            if r[1] < self.needed_rise:
##                print "on: ",
##                print r[0],
##                print " insufficient rise of: ",
##                print r[1]

##    def __has_tidal_window_on_time(self, time):
##        '''test of panda series as data structure'''
##        table_name = "TDP_{id}_Tidal_Data".format(id=self.tidal_point)
##        enddate = time + self.min_window_after_ETA
##        startdate = time - self.min_window_before_ETA
##        d1 = unicode(startdate)
##        d2 = unicode(enddate)
##        tf = self.panda_dict[table_name]
####        new_index = tf.index + pandas.Index([d1, d2])
####        try:
####            tf = tf.reindex(new_index).interpolate(method="linear")
####        except:
####            print table_name
####            print d1
####            print d2
####            print tf[tf.groupby(level=0).transform(len)['rise'] > 1]
##
##        #get indexes of the slice of data from start to end
##        index_list =  tf[(tf.datetime >= d1) & (tf.datetime <= d2)].index.tolist()
##
##
##        #check if extended slice is all above needed rise:
##        if tf[(tf.index >= min(index_list) -1) & (tf.index <= max(index_list) + 1) & (tf.rise < self.needed_rise)].empty:
##            return True
##        #check if non-extended slice is anywhere below needed rise:
##        if not tf[(tf.index >= min(index_list)) & (tf.index <= max(index_list)) & (tf.rise < self.needed_rise)].empty:
##            return False
##        #interpolate:
##        window_slice = tf[(tf.index >= min(index_list) -1) & (tf.index <= max(index_list) + 1)]
##        dt_list = window_slice.datetime.tolist()
##        r_list = window_slice.rise.tolist()
##        dt0 = self.__make_datetime_from_db_val(dt_list[0])
##        dt1 = self.__make_datetime_from_db_val(dt_list[1])
##        r0 = r_list[0]
##        r1 = r_list[1]
##        if self.__interpolate_rise_value(dt0, dt1, r0, r1, startdate) < self.needed_rise:
##            return False
##        dt0 = self.__make_datetime_from_db_val(dt_list[-2])
##        dt1 = self.__make_datetime_from_db_val(dt_list[-1])
##        r0 = r_list[-2]
##        r1 = r_list[-1]
##        if self.__interpolate_rise_value(dt0, dt1, r0, r1, enddate) < self.needed_rise:
##            return False
##        else:
##            return True


##    def __construct_datetime_string(self, datetime):
##        s = "{y}-{m}-{d} {H}:{M}:{S}".format(y=datetime.datetime.year(datetime),
##                                                 m=datetime.datetime.month(datetime),
##                                                 d=datetime.datetime.day(datetime),
##                                                 )

##    def __has_tidal_window_on_time1(self, time):
##        '''tests if there is a tidal window on this given time'''
##        c = self.memory_database.cursor()
##        table_name = "TDP_{id}_Tidal_Data".format(id=self.tidal_point)
##        enddate = time + self.min_window_after_ETA
##        startdate = time - self.min_window_before_ETA
##        sql = "SELECT * FROM {table} WHERE datetime BETWEEN '{start}' AND '{end}';".format(table=table_name, start=startdate, end=enddate)
##        c.execute(sql)
##        for r in c:
##            if r[1] < self.needed_rise:
##                return False
##        return True


##    def first_tidal_window_available_after_time2(self, time):
##        '''tryout of dict as data structure'''
##        startdate = time + self.time_to_here
##        if self.__has_tidal_window_on_time(startdate):
##            return startdate - self.time_to_here

def main():
    d1 = datetime.datetime.today()
    d2 = datetime.timedelta(hours=0)
    d3 = datetime.timedelta(hours=1.5)
    print d1
    print d1 + d3
    d2 = d2 + d3
    print d1 + d2

if __name__ == '__main__':
    main()
