The tide-window program is a program to calculate tide windows. It uses imported tidal data and lets the user create waypoints (tresholds) and routes based on these tresholds. The program can calculate tidal windows based on these tresholds and their connected tidal data.

Changelog:
*****
20-05-2014
 - Added configuration screen with a ttk notebook (tabbed view) to modify tresholds, waypoints, connections, ship types and speed definitions.
 - Added login screen to determine normal user and admin user.

*****
version 0.1
-basic functionality in place. Program can now:
  -Import tidal data from an access database to an sqlite database
  -check if the program database is present (will error out if it isn't)
  -cross check the local program database with the one on the GNA network (if connection is present)
  -construct tresholds (waypoints) with all parameters and store them in the program database
  -construct connections between the waypoints with all parametes (distance) and store them in the program database
  -construct routes with connected waypoints, and store them in the program database
  -calculate tidal windows for a certain route and a certain ETA (and some other parameters)
  -visualize this tidal window in a graph

TODO:
-improve GUI
-add user profiles (user/administrator
-expand calculation possebilities (RTA / current window / etc)
-import and store high and low waters as well
-etc
