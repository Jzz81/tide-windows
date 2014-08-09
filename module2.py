#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      hvl
#
# Created:     06-06-2014
# Copyright:   (c) hvl 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------
from Tkinter import *
from GUI_helper import StatusBar

def set_view(name):
    try:
        first_view.pack_forget()
    except:
        pass
    try:
        second_view.pack_forget()
    except:
        pass

    if name == "first":
        first_view.pack()
    elif name == "second":
        second_view.pack()

root = Tk()
Button(root, text="first view", command=lambda: set_view("first")).pack()
Button(root, text="second view", command=lambda: set_view("second")).pack()

status = StatusBar(root)
status.pack(side=BOTTOM, fill=X)

first_view = Label(root, text="First")

second_view = Label(root, text="Second")

set_view("second")

root.mainloop()
