#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 30 12:04:12 2018

@author: Bob Hentz


-------------------------------------------------------------------------------
  Name:        SiteLoadDisplay.py
  Purpose:     Provide Methods for Displaying, Entering and Editting the Site 
               Energy Load DataFrame             

  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)

               This program is distributed WITHOUT ANY WARRANTY;
              without even the implied warranty of MERCHANTABILITY
              or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""
from tkinter import *
import tkinter.ttk as ttk
from SiteLoad import *

#TODO Correct intemittent input data gathering
#TODO Implement on combo block content change, update watts field
#TODO implement record delete functionality
class table_combo_cell(ttk.Combobox):
    """ Creates a Selector Cell to contain Type Selection Options """
    def __init__(self, parent, tblpos, datpos, var, opts_lst, 
                 validate_command= None):
        self.tblpos = tblpos
        self.datpos = datpos
        self.opts = opts_lst
        self.width = 5
        for li in opts_lst:
            if len(li) > self.width:
                self.width = len(li)
        self.var = var
        self.evar = StringVar()
        self.evar.set(str(self.var))
        self.parent = parent
        self.validate_command = validate_command
        self.validate = None
        if self.validate_command:
            self.validate = 'focusout'     
        ttk.Combobox.__init__(self, parent, values=self.opts, textvariable= self.evar, 
                               width = self.width, exportselection= False, 
                               validate= self.validate, 
                               validatecommand= self.is_okay)
        self.grid(row=self.tblpos[0], column=self.tblpos[1], padx=2, pady=2,
                     sticky= (E, W))
        self.bind('<FocusOut>', self.event_process)
        self.bind('<Return>', self.event_process)
        self.bind('<Key-Delete>', self.delete)

    def event_process(self, event):
        self.is_okay()
               
    def delete(self, event):
        #TODO Add delete row function to Site Load Display
        # Ask if you want to delete the record
        # If yes, drop row by index number, else do nothing
        
        pass

    def is_okay(self):
        """ Vailidate contents of entry using method passed by caller """
        new_val = self.evar.get()
        if new_val != self.var:
            return self.validate_command(self.datpos, new_val)   
       
class table_data_cell(ttk.Entry):
    """ Creates an Enrty cell to contain table data """
    def __init__(self, parent, tblpos, datpos, var):
        self.parent = parent
        self.tblpos = tblpos
        self.datpos = datpos
        self.varTyp = type(var)
        self.var = var
        self.evar = StringVar()
        self.evar.set(str(self.var))
        self.just = CENTER
        if self.datpos[1] == 0:
            self.just = LEFT
        cw = 5
        if len(str(var))-2 > cw:
            cw =len(str(var)) +2
        ttk.Entry.__init__(self, parent, textvar= self.evar, width= cw, 
                           justify= self.just)
        self.grid(row=self.tblpos[0], column=self.tblpos[1], padx=2, pady=2, 
                  sticky=(E, W))
        self.bind('<Leave>', self.update) 
        self.bind('<Key-Delete>', self.delete)
        self.bind('Key-Tab>', self.update)
        self.bind('FocusOut>', self.update)
        self.bind('Key-Return>', self.update)
        
    def update(self, event):
        try:
            new_val = self.varTyp(self.evar.get())
        except:
            if self.evar.get().strip() == '':
                new_val = 0
            else:
                new_val = self.evar.get()
        if new_val != self.var:
            self.parent.update_data(self.datpos, new_val) 
        
    def delete(self, event):
        pass
        

class header_cell(ttk.Label):
    """ Creates a Label Cell to contain Table Header Info """
    def __init__(self,  parent, colpos, var):
        cw = 5
        if len(var)-2 > cw:
            cw = len(var) +2
        ttk.Label.__init__(self, parent, text=var, font='Helvetica 10 bold', 
                           borderwidth=2, width=cw+2, anchor=CENTER) 
        self.grid(row= 0, column= colpos, padx= 3, pady= 2, sticky= (E ,W))


class Table(ttk.Frame):
    """ Creates a master container to hold the DataFrame widgets """
    def __init__(self, sldf, parent):
        self.df = sldf
        self.col_hds = self.df.get_headers()
        self.LoadOpts = self.df.getTypeOptions()
        self.parent= parent
        ttk.Frame.__init__(self,parent)
        self.grid(sticky= (N, S, E, W))
        self.dsply_table()
        
    def build_workArray(self):
        self.wa = list()
        for r in range(self.df.get_row_count()):
            self.wa.append(self.df.get_row_by_index(r))
        self.wa.append(['']*len(self.col_hds))
    
    def dsply_table(self):
        self.build_workArray()
        tbl_row = 0
        self.build_row(self.col_hds, 0, 0,True)
        tbl_row += 2
        for r in range(len(self.wa)):
            self.build_row(self.wa[r], r, tbl_row, False)
            tbl_row += 2

    def build_row(self, val_list, data_row, tbl_row, TBLHDR=False):
        lastrow = False
        if len(val_list) > 0:
            for i in range(len(val_list)):
                colpos = 1+i*2
                ttk.Separator(self, orient=VERTICAL).grid(row=tbl_row, column = colpos-1, sticky= (N, S))               
                if TBLHDR:
                    cf = header_cell(self, colpos, val_list[i])
                else:
                    cf = self.define_data_cell([tbl_row, colpos],  [data_row, i], val_list[i])
        ttk.Separator(self, orient=VERTICAL).grid(row=tbl_row+1, column = len(val_list)*2, sticky=(N, S)) 

    def define_data_cell(self, tblpos, datpos, var):
        if datpos[1] == 0:
            cf = table_combo_cell(self, tblpos, datpos, var, self.LoadOpts, self.update_data)
        else:
            cf = table_data_cell(self, tblpos,  datpos, var)          
                       
    def update_data(self, pos, new_val):
        self.wa[pos[0]][pos[1]] = new_val
        if pos[1] == 0:
            ar = self.wa[pos[0]]
            ar = self.df.setStdRowValues(ar)
            self.wa[pos[0]] = ar   
        if pos[0] == len(self.wa) -1:
            ar = []
            for i in range(len(self.wa[pos[1]])):
                ar.append(self.wa[pos[0]][i])
            self.df.add_new_row(ar)
            self.dsply_table()
        else:
            self.df.set_cell_value(pos, new_val)

    def on_form_close(self):
        pass
            

def main():
    sl = SiteLoad()
    sl.add_new_row(['Light, LED', 12, 0.6, 6, 17, 5.0, 'AC'])


    print ('Starting Display')
    print (sl.get_dataframe())
    root = Tk()        
    
    root.title("Base Frame Testing")
    tabframe = Table(sl, root)
    #tabframe.add_data(mrdat)
#    tf = ttk.Frame(root)
#    tf.grid(sticky= (N S E W))
#    opts = ['Light LED', 'Light Halogen', 'Refrigerator 18 CF', 'This is a really, really long option']
#    cc = combo_cell( tf, [0,0], [2,5], 'Light LED', opts, update_combo)
#    for i in range(8):
#        cx = data_cell(tf, [0,i+1], [0,0], "123456789")
    root.mainloop()
    print('\nExiting Display')
    print (sl.get_dataframe())


        
if __name__ == '__main__':
    main()
