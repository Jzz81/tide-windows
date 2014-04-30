'''
Created on 10 feb. 2014

@author: Joos
'''
import GUI_main
import Tkinter


#get db file path:
root = Tkinter.Tk()
root.withdraw()
AXDB = tkFileDialog.askopenfilename()
root.destroy()

#start GUI:
root = Tkinter.Tk()

#set maximized:
root.wm_state('zoomed')
#pass to Window class
GUI_main.Application(root)

##AXDB = "C:\Users\Joos\Google Drive\GNA\programma Patrick\Jaartij-2014_1_1.accdb"

#'send' program into gui loop (to keep program in gui)
root.mainloop()
