#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 10 11:07:02 2018
Modified on 02/22/2019 for version 0.1.0
Modified on 04/11/2021 to address Issues #10, 12, & 13 related to improving 
            Site Load Definition performance and ease of use


@author: Bob Hentz

-------------------------------------------------------------------------------
  Name:        guiFrames.py
  Purpose:     Implement general puprpose GUI Frames & logic required to 
               implement the data entry and result display.
     
  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)

              This program is distributed WITHOUT ANY WARRANTY;
              without even the implied warranty of MERCHANTABILITY
              or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""


import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter.messagebox import askyesno
import tkinter.ttk as ttk
from tkinter.filedialog import askopenfilename 


"""  Helper Methods & Functions """
def ask_question(title, mssg, **kargs):
    """ Implements a pop-up window that asks a question """
    if askyesno(title, mssg, **kargs):
        return True
    else:
        return False

def show_warning(title, mssg):
    """ Implements a pop-up Window that Notifies the User of an error/warning """
    tk.showwarning(title, mssg)

def cleanse_data(data):
    """ Converts a null data display to None Value """
    if data == None:
        return ""
    else:
        return data

def entry_is_empty(data):
    """ Tests for a null data field  """
    if data == None or data == "":
        return True
    return False
    
def popup_notification(parent, message, command, *command_args, color= '#ffff80'):
    """ Create a popup notification to alert user to long running process
        Execute the Process, clear the alert screen and return the process results """
    rslts = None
    tplvl = tk.Toplevel()
    tplvl.lift()
    lbl = tk.Label(tplvl, text = message, padx= 5, pady=5, bd= 5, bg= color)
    lbl.pack(fill = "both", expand=True)
    parent.update_idletasks()
    if command_args is None:
        rslts = command()
    else:
        rslts = command(*command_args)
    tplvl.destroy()
    return  rslts   
 
def build_menubar(parent, menu_itms):
    """ Create a Menu bar and populate it's contents 
        menu_itms consists of a Dictionary where each key
        represents a new Menu Header and references a list of tuples 
        defining the (sub-menu title, the action method) """
    def add_command(mnu, itm):
        mnu.add_command(label= itm[0], command= itm[1])
        
    def add_sub_menu(mnu, cmd_dict):
        for ky in cmd_dict.keys():
            if len(cmd_dict[ky]) > 0:
                mi = tk.Menu(mnu, tearoff= 0)
                mnu.add_cascade(label=ky, menu=mi)
                for itm in cmd_dict[ky]:
                    if type(itm) == tuple:
                        add_command(mi, itm)
                    else:
                        add_sub_menu(mi, itm)
            
    mbar = tk.Menu(parent)
    add_sub_menu(mbar, menu_itms)
    parent.config(menu=mbar)
    return mbar
        
        

def open_file(parent, title, filename, initialdir, df_ext):
    """ Open Dialog to identify File to be openned  """
    return askopenfilename(parent= parent, title= title,
                           defaultextension= df_ext, 
                           initialdir= initialdir)
 
    
""" Building Blocks used to Implement Most Frames """

class make_figure(Figure):
    """ Manages the Figure and Axis creation process """ 
#    plt_colors = ['#3F7FBF', '#6AFF33', '#F4FF33', '#6600ff', '#FF3348']
    def __init__(self, xlabel, ylabel, xaxis, yaxislist, pltlbl, pltsize, **kargs):                                                     
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.xdata = xaxis
        self.pltlbl = pltlbl
        self.pltsize = pltsize
        Figure.__init__(self)
        self.ax  = self.add_subplot(111)
        self.ax.set_title (self.pltlbl)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        self.lgnd_loc = kargs.pop('Legend', None)
        for i in range(len(yaxislist)):
            self.insert_plot(yaxislist[i])
        if len(yaxislist) > 1 :
            if self.lgnd_loc is not None:
                self.ax.legend(loc=self.lgnd_loc)
            else:
                self.ax.legend(loc= 'upper right')

    def insert_plot(self, plt_dict):
        """
        pargs = dict of the form {
                                  'type': STRING (Bar|Hist|Line),
                                  'xaxis': x axis np.array of plot
                                  'data': y axis np.array of plot
                                  'label': STRING, 
                                  'data': np.array(),
                                  'color': STRING, 
                                  'width': FLOAT'
                                 }
        """
        plt_type = plt_dict.pop('type', 'Line')
        plt_color = plt_dict.pop('color', 'b')
        plt_wdth = plt_dict.pop('width', 0.8)
        plt_lbl = plt_dict.pop('label', None)
        plt_data = plt_dict.pop('data', None)
        plt_xaxis = plt_dict.pop('xaxis', None)
        plt_line = plt_dict.pop('linestyle', 'solid')
    
        if plt_type == 'Bar':
             self.ax.bar(plt_xaxis, plt_data, label= plt_lbl, width= plt_wdth, color= plt_color)
        elif plt_type == 'Hist':
            self.ax.hist(plt_xaxis, plt_data, label= plt_lbl, color= plt_color)
        else:
            self.ax.plot(plt_xaxis, plt_data, label= plt_lbl, color= plt_color, 
                         linewidth= plt_wdth, linestyle= plt_line)
            
        
class plot_graphic(ttk.Frame):
    """ Creates a Figure Instance and inserts the figure into a Canvas within the
        a frame """
    def __init__(self, parent_frame, xlabel, ylabel, xaxis, yaxislist, pltlbl, pltsize, **kargs):
        self.parent = parent_frame
        text_inserts = kargs.pop('text_inserts',[])
        ttk.Frame.__init__(self, self.parent)
        self.grid(row= 0, column= 0, sticky = "NWES", padx=5, pady=5)
        for i in range(len(text_inserts)):
            ttk.Label(self, text=text_inserts[i]).grid(row = i+1, column= 0, sticky = 'EW')
        self.fig = make_figure(xlabel, ylabel, xaxis, yaxislist, pltlbl, pltsize, **kargs)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0)
        
    def on_click(self, event):
        print('Detected Button Release', event)
            
               
    def close_graphic(self):
        self.destroy()
                
class list_cell(ttk.Combobox):
    """ Creates an Option List Field widget for gathering & updating source data """
    def __init__(self, parent_frame, data_src, min_lngth, location= None,
                  validate_command= None, On_change= None):
        self.parent = parent_frame
        self.src = data_src
        self.opts = self.src.get_list()
        self.min_width = min_lngth
        self.loc = [0,1]
        if location is not None:
            self.loc = location
        self.wdth = None
        self.val = tk.StringVar()
        self.val.set(self.src.read_data())
        self.validate = None
        self.chg_cmd = On_change
        self.validate_cmd = validate_command
        self.show_frame()
        
    def show_frame(self):
        """ Display The Frame """              
        ttk.Combobox.__init__(self, self.parent, width=self.wdth, 
                           textvariable=self.val,
                           values= list(filter(lambda x: x.startswith(self.val.get()), 
                                               self.opts)),
                           exportselection = 0, justify= tk.LEFT)
        self.grid(row= self.loc[0], column= self.loc[1], sticky=(tk.E))
        self.bind('<FocusOut>', self.is_okay)
        self.bind('<KeyRelease>', self.on_chg)
      
    def get_val(self):
        """ Method to get the contents of cell """
        return self.val.get()

    def on_chg(self, event):
        """ Method to process cell content changes """
        val = self.get_val()
        if val is not self.src.read_data():
            self.src.write_data(val)
            if self.chg_cmd is not None:
                self.chg_cmd(val)
        self.show_frame()
        
    def is_okay(self, event):
        """ Validate contents of entry using method passed by caller """
        val = self.val.get()
        rslt = True
        if self.validate_cmd is not None:
            rslt = self.validate_cmd(val)
        if rslt:
            self.on_chg(event)
        return rslt
    
class data_cell(ttk.Entry):
    """ Creates an Entry Field widget for gathering & updating source data """
    def __init__(self, parent_frame, data_src, min_lngth=None, location= None,
                  validate_command= None, On_change= None):
        self.parent = parent_frame
        self.src = data_src
        self.min_width = 10
        if min_lngth is not None:
            self.min_width = min_lngth
        self.loc = [0,1]
        if location is not None:
            self.loc = location
        self.val = tk.StringVar()
        self.val.set(self.src.read_data())
        self.validate = None
        self.chg_cmd = On_change
        self.validate_cmd = validate_command
        self.show_frame()
        
    def show_frame(self):
        """ Display The Frame """       
        ttk.Entry.__init__(self, self.parent, width=self.min_width, 
                           textvariable=self.val, justify= tk.CENTER 
                           #validate= self.validate, 
                           #validatecommand= self.validate_cmd
                           )
        self.grid(row= self.loc[0], column= self.loc[1], sticky=(tk.EW))
        self.bind('<FocusOut>', self.is_okay)
        self.bind('<KeyRelease>', self.on_chg)
      
    def get_val(self):
        """ Method to get the contents of cell """
        return self.val.get()

    def on_chg(self, event):
        """ Method to process cell content changes """
        val = self.get_val()
        if val is not self.src.read_data():
            if self.chg_cmd is not None:
                self.chg_cmd(val)
            else:
                self.src.write_data(val)
        self.show_frame()
                  
    def is_okay(self, event):
        """ Validate contents of entry using method passed by caller """
        val = self.val.get()
        rslt = True
        if self.validate_cmd is not None:
            rslt = self.validate_cmd(val)
        if rslt:
            self.on_chg(event)
        return rslt
        

class note_cell(tk.Text):
    """ Creates an Entry Field Widget for input & update of Long string data  """
    def __init__(self, parent_frame, data_src, size= None, location= None): 
        self.parent = parent_frame
        self.src = data_src
        self.loc = [0,1]
        if location is not None:
            self.loc = location   
        self.size = [1, 50]
        if size != None:
            self.size = size
        tk.Text.__init__(self, self.parent, height= self.size[0], width= self.size[1],
                      wrap= tk.WORD, padx = 5, pady = 5)
        self.grid(row= self.loc[0], column= self.loc[1], sticky=(tk.N, tk.S, tk.W, tk.E))
        self.insert('1.0', self.src.read_data())
        self.bind('<FocusOut>', self.on_chg)

    def is_dirty(self):
        return self.src.read_data() != self.get('1.0', tk.END+'-1c')

    def get_val(self):
        return self.get('1.0', tk.END+'-1c')

    def on_chg(self, event):
        self.src.write_data(self.get_val())
        
class entry_form_frame(ttk.Frame):
   """ Creates a two widget frame containing a Label Widget and an data Widget
        used to implement a Data Entry Form field """    
   def __init__(self, parent_frame, data_src, frm_type, location= None, size= None,
                 colspan= None, validate_command= None, On_change= None):
        assert frm_type == "Data Entry" or frm_type == "List Entry" or frm_type == "Note Entry"
        self.parent = parent_frame
        self.src = data_src
        self.frm = frm_type
        self.size = 10
        if size is not None:
            self.size = size
        self.loc = [0,1]
        if location is not None:
            self.loc = location
        self.colspan = 1
        if colspan is not None:
            self.colspan = colspan
        self.chg_cmd = On_change
        self.validate_cmd = validate_command
        self.make_frame()
        
   def get_val(self):
       return self._ntry.get_val()
       
   def make_frame(self):
        ttk.Frame.__init__(self, self.parent)
        self.grid(row = self.loc[0], column= self.loc[1], 
                  sticky= (tk.N, tk.W, tk.E, tk.S), columnspan=self.colspan)
        if self.frm == "Data Entry":
            ttk.Label(self, padding='2 2 2 2', 
                      text=self.src.get_label()).grid(column=0, row=0, 
                                                      sticky=(tk.W, tk.E))
            self._ntry = data_cell(self, self.src, min_lngth=self.size, location= [0, 1],
                      validate_command= self.validate_cmd, On_change= self.chg_cmd) 
        elif self.frm == "List Entry":
            ttk.Label(self, padding='2 2 2 2', 
                      text=self.src.get_label()).grid(column=0, row=0, 
                                                      sticky=(tk.W, tk.E))
            self._ntry = list_cell(self, self.src, min_lngth=self.size, 
                                   location= [0, 1],
                      validate_command= self.validate_cmd, On_change= self.chg_cmd)
        else:
            ttk.Label(self, padding='2 2 2 2', 
                      text=self.src.get_label()).grid(column=0, row=0, 
                                                      sticky=(tk.W, tk.E))
            self._ntry = note_cell(self, self.src, size=self.size, 
                                   location= [1, 0])
                  
        
    
""" Master Frame Classes Used to Implement GUI Functions  """
class status_window(tk.LabelFrame):
    """ Implements a Status Window and Manages display of status messages """
    def __init__(self, parent, title, loc= None, spn = None ):
        self.parent = parent
        if loc is None:
            loc = [0,0]
        tk.LabelFrame.__init__(self, parent, text= title) 
        self.grid(row= loc[0], column= loc[1], columnspan= spn, sticky = 'EW')
        self.configure(borderwidth= 5, width= 500, height= 50, 
                       relief= tk.GROOVE, background= '#ccffb3')
        self.lbl = None
        
    def show_message(self, message, style= None):
        fs = ('Times', '12', 'bold')
        fg = '#006600'
        s = message
        if style is not None:
            if style == 'Fatal':
                s = 'Fatal Error:  ' + s
                fs = ('Times', '15', 'bold')
                fg = '#990000'
            elif style == 'Warn':
                s = 'Warning:  ' + s
                fg = '#660066' 
        else:
           s = 'Notice: ' + s
        if self.lbl is not None:
            self.lbl.destroy()
        self.lbl = tk.Label(self, text= s, font= fs, padx= 2, pady= 2, 
                            background= '#ccffb3', foreground= fg)
        self.lbl.grid(row= 0, column=0)
        self.parent.update_idletasks()


class switchboard(ttk.LabelFrame):
    """ Creates a Menu for use in managing application administration"""
    def __init__(self, src, location = None, parent=None,  menuTitle = None):
        self.src = src
        self.parent = parent
        self.loc = [1,1]
        if location != None:
            self.loc = location
        self.menuTitle = 'Menu'
        if menuTitle is not None:
            self.menuTitle = menuTitle
        self.mstrKey = None
        ttk.LabelFrame.__init__(self, self.parent, text=self.menuTitle, borderwidth= 5,
                                width= 400, height = 500, padding= 5, relief= tk.GROOVE)
        self.grid(row = self.loc[0], column = self.loc[1], 
                  sticky = ( tk.N, tk.S, tk.W, tk.E))
        self.grid_propagate(0)
        self.define_menu()
        self.display_actions()
        
    def define_menu(self):
        """ Method over-ridden locally to set specific menu options """
        """ self_actions  is a list of tuples defining each menu item 
            The tuple consists of:
                descript_txt: describing the menu action
                btn_text:     identifying the button text
                command:      directing the action when button is clicked"""      
        self.actions = []


    def display_actions(self):
        """ Parses action list to create menu items """
        cur_row = 1
        for act in self.actions:
#            menu_action(act[0], act[1], [cur_row, cur_col], parent = self)
            ttk.Label(self, text = act[0], padding= '2 5 2 2').grid(
                    row = cur_row, column= 1, sticky= (tk.E, tk.W))
            ttk.Label(self, text = " ", padding= '2 5 2 2').grid(
                    row = cur_row, column= 2, sticky= (tk.E, tk.W))
            ttk.Button(self, text= act[1], command = act[2], 
                       padding= '2 5 2 2').grid(row = cur_row, 
                                         column =3, sticky= (tk.E, tk.W))            
            cur_row += 1
            

    def set_mstrKey(self,mstrKey):
        """ Define Master Key for Current Record """
        self.mstrKey = mstrKey

        
    def menu_close(self):
        """ Close the Switchboard """
        self.parent.destroy()





def main():
    pass
        
    
if __name__ == '__main__':
    main()
