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
import time
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
                numpy_dict):
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
        self.numpy_dict = numpy_dict

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

            numpy_timeframe = self.numpy_dict["TDP_{id}_Tidal_Data".format(id=tidal_point_id)]
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
                                                            numpy_timeframe=numpy_timeframe)

    def __since_epoch(self, dt):
        '''returns the seconds since epoch of a given datetime'''
        return (dt - datetime.datetime(1970, 1,1)).total_seconds()

    def __epoch_to_date(self, epoch):
        '''returns a datatime, constructed from a given epoch'''
        pass

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
                 numpy_timeframe
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
        self.numpy_timeframe = numpy_timeframe
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

    def __since_epoch(self, dt):
        '''returns the seconds since epoch of a given datetime'''
        return (dt - datetime.datetime(1970, 1,1)).total_seconds()

    def __get_numpy_slice_between_dates(self, date1, date2):
        '''slices the numpy array between 2 dates (in epoch)'''
        return self.numpy_timeframe[(self.numpy_timeframe[:,0] >= date1) & (self.numpy_timeframe[:,0] <= date2)]

    def __get_tidal_windows(self):
        '''will retreive all tidal windows for the given ETA and one week ahead (2 days before)'''
        startdate = self.ETA

        #CREATE TESTING TIMEFRAME OF 2 DAYS BEFORE AND 7 DAYS FROM ETA:
        self.eval_startdate = startdate - datetime.timedelta(days=2)
        epoch_start_date = self.__since_epoch(self.eval_startdate)
        self.eval_enddate = startdate + datetime.timedelta(days=7)
        epoch_end_date = self.__since_epoch(self.eval_enddate)
        test_tf = self.__get_numpy_slice_between_dates(epoch_start_date, epoch_end_date)

        #TEST IF ALL OF THE TEST TIMEFRAME IS ABOVE THE NEEDED RISE:
        above = test_tf[:,1] >= self.needed_rise
        if not False in above:
            self.tidal_windows.append([self.eval_startdate, self.eval_enddate])
            return

        #TEST IF ALL OF THE TEST TIMEFRAME IS BELOW THE NEEDED RISE:
        if not True in above:
            self.tidal_windows = None
            return

        #GET TIME VALUES OF CROSSING POINTS (WITH UP/DOWN INDICATOR)
        crossings =  self.cross(test_tf)

        #IF FIRST DATA POINT IS EQUAL OR ABOVE NEEDED RISE, FIRST PART IS A TIDAL WINDOW.
        if test_tf[0][1] >= self.needed_rise:
            self.tidal_windows.append([self.eval_startdate, self.__epoch_to_date(crossings[0])])
            start_i = 1
        else:
            start_i = 0

        for i in range(start_i, len(crossings), 2):
            d0 = crossings[i]
            if i == len(crossings) -1:
                d1 = epoch_end_date
            else:
                d1 = crossings[i+1]
            self.tidal_windows.append([self.__epoch_to_date(d0),self.__epoch_to_date(d1)])

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

    def cross(self, array):
        """
        Given an array returns all the index values where the data values equal
        the 'cross' value.

        Direction can be 'rising' (for rising edge), 'falling' (for only falling
        edge), or 'cross' for both edges
        """
        # Find if values are above or bellow yvalue crossing:
        above= array[:,1] >= self.needed_rise
        below= numpy.logical_not(above)
        left_shifted_above = above[1:]
        left_shifted_below = below[1:]
        x_crossings = []
        # Find indexes on left side of crossing point
        rising = left_shifted_above & below[0:-1]
        falling = left_shifted_below & above[0:-1]
        idxs = (rising | falling).nonzero()[0]

        # Calculate x crossings with interpolation using formula for a line:
        dates1 = array[:,0][idxs]
        dates2 = array[:,0][idxs+1]
        rises1 = array[:,1][idxs]
        rises2 = array[:,1][idxs+1]

        x_crossings = (self.needed_rise-rises1)*(dates2-dates1)/(rises2-rises1) + dates1
        return x_crossings

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

    def __epoch_to_date(self, epoch):
        '''returns a datatime, constructed from a given epoch'''
        timestruct = time.gmtime(epoch)
        return datetime.datetime(year=timestruct.tm_year,
                                month=timestruct.tm_mon,
                                day=timestruct.tm_mday,
                                hour=timestruct.tm_hour,
                                minute=timestruct.tm_min,
                                second=timestruct.tm_sec)


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
