#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 30 12:04:12 2018
Modified on 02/22/2019 for version 0.1.0
Modified on 04/11/2021 to address Issues #10, 12, & 13 related to improving 
            Site Load Definition performance and ease of use
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
import tkinter as tk
import tkinter.ttk as ttk
from SiteLoad import SiteLoad


class table_button_cell(ttk.Button):
    """ Creates a Button Cell """
    def __init__(self, parent, tblpos, datpos, text, callback):
        self.tblpos = tblpos
        self.datpos = datpos
        self.text = text
        self.width = 5
        self.callback = callback
        ttk.Button.__init__(self, parent, text= self.text , 
                            command= self.button_resp)
        self.grid(row=self.tblpos[0], column=self.tblpos[1], padx=2, pady=2,
                     sticky= (tk.E, tk.W))        
    def button_resp(self):
        if self.callback:
            self.callback(self.tblpos, self.datpos)
    
class table_combo_cell(ttk.Combobox):
    """ Creates a Selector Cell to contain Type Selection Options """
    def __init__(self, parent, tblpos, datpos, var, opts_lst, 
                 select_command= None):
        self.tblpos = tblpos
        self.datpos = datpos
        self.opts = opts_lst
        self.width = 5
        for li in opts_lst:
            if len(li) > self.width:
                self.width = len(li)
        self.var = var
        self.evar = tk.StringVar()
        self.evar.set(str(self.var))
        self.parent = parent
        self.select_command = select_command
        ttk.Combobox.__init__(self, parent, values=self.opts, 
                              textvariable= self.evar, 
                               width = self.width, exportselection= False)
        self.grid(row=self.tblpos[0], column=self.tblpos[1], padx=2, pady=2,
                     sticky= (tk.E, tk.W))
        self.bind("<<ComboboxSelected>>", self.is_selected)
        
    def is_selected(self, event):
        if self.select_command:
            self.select_command(self.tblpos, self.datpos, self.get())
        
       
class table_data_cell(ttk.Entry):
    """ Creates an Enrty cell to contain table data """
    def __init__(self, parent, tblpos, datpos, var):
        self.parent = parent
        self.tblpos = tblpos
        self.datpos = datpos
        self.varTyp = type(var)
        self.var = var
        self.evar = tk.StringVar()
        self.evar.set(str(self.var))
        self.just = tk.CENTER
        if self.datpos[1] == 0:
            self.just = tk.LEFT
        cw = 5
        if len(str(var))-2 > cw:
            cw =len(str(var)) +2
        ttk.Entry.__init__(self, parent, textvar= self.evar, width= cw, 
                           justify= self.just)
        self.grid(row=self.tblpos[0], column=self.tblpos[1], padx=2, pady=2, 
                  sticky=(tk.E, tk.W))
        self.bind('<Leave>', self.update)   # Mouse leaves cell
        self.bind('<FocusOut>', self.update) # Keyboard Focus exits
        self.bind('<Key-Tab>', self.update)
        self.bind('<Key-Return>', self.update)

        
    def update(self, event):
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
                           borderwidth=2, width=cw+2, anchor=tk.CENTER) 
        self.grid(row= 0, column= colpos, padx= 3, pady= 2, sticky= (tk.E , tk.W))


class Table(ttk.Frame):
    """ Creates a master container to hold the DataFrame widgets """
    def __init__(self, sldf, parent, Delete_col = None):
        self.df = sldf
        self.col_hds = self.df.get_headers()
        self.LoadOpts = self.df.getTypeOptions()
        self.parent= parent
        self.add_Del_col = Delete_col
        ttk.Frame.__init__(self,parent)
        self.grid(sticky= (tk.N, tk.S, tk.E,tk. W))
        self.dsply_table()
        
    def build_workArray(self):
        #Load wa from underlying dataframe
        self.wa = list()
        for r in range(self.df.get_row_count()):
            self.wa.append(self.df.get_row_by_index(r))
        #add extra row at end, for new entry
        self.wa.append(['']*len(self.col_hds))
    
    def dsply_table(self):
        self.build_workArray()
        tbl_row = 0
        self.build_row(self.col_hds, 0, 0, TBLHDR=True)
        tbl_row += 2
        for r in range(len(self.wa)):
            self.build_row(self.wa[r], r, tbl_row, TBLHDR=False)
            tbl_row += 2

    def build_row(self, val_list, data_row, tbl_row, TBLHDR=False):
        # lastrow = False
        colpos = 0
        if len(val_list) > 0:
            for itm_no, itm_name, in enumerate(val_list):
                colpos = 1 + itm_no*2
                ttk.Separator(self, orient=tk.VERTICAL).grid(row=tbl_row, 
                                 column = colpos-1, sticky= (tk.N, tk.S)) 
                if TBLHDR:
                     header_cell(self, colpos, itm_name)
                                                
                else:
                    self.define_data_cell([tbl_row, colpos],  
                                          [data_row, itm_no], itm_name)
            ttk.Separator(self, orient=tk.VERTICAL).grid(row=tbl_row+1,
                 column = colpos+1, sticky=(tk.N, tk.S))
        
            if self.add_Del_col:
                # Add the Delete Row column entries if required
                colpos+=2
                if TBLHDR:
                    header_cell(self, colpos, self.add_Del_col)

                else:
                    table_button_cell(self, [tbl_row, colpos],
                                       [data_row, itm_no],
                                        'X', self.delete_row)
                ttk.Separator(self, orient=tk.VERTICAL).grid(row=tbl_row+1,
                     column = colpos+1, sticky=(tk.N, tk.S))

    def define_data_cell(self, tblpos, datpos, var):
        if datpos[1] == 0:
            table_combo_cell(self, tblpos, datpos, var, self.LoadOpts, 
                             select_command= self.combo_selected)
        else:
            table_data_cell(self, tblpos,  datpos, var)          
                       
    def delete_row(self, tpos, dpos):
        """ Delete a row after delete button pushed """
        if dpos[0] < self.df.get_row_count():
            self.df.delete_row(dpos[0])
            self.dsply_table()
    
    def combo_selected(self, tblpos, dpos, newval):
        # Process a Combobox entry change 
        if dpos[0] < self.df.get_row_count():
            if self.wa[dpos[0]][dpos[1]] != newval:
                ar = self.wa[dpos[0]]
                ar[0] = newval
                stdar = self.df.getDefaultRowValues(newval)
                for ky, val in stdar.items():
                    ar[self.col_hds.index(ky)] = val
                self.wa[dpos[0]] = ar
                self.df.update_row_values(dpos[0], ar)
                self.dsply_table()
        else:
            # This is a new row 
            ar = self.wa[dpos[0]]
            ar[0] = newval
            ar = self.df.setStdRowValues(ar)
            self.wa[dpos[0]] = ar
            self.df.add_new_row(ar)
            self.dsply_table()
        
    def update_data(self, dpos, new_val):
        ## This is where we come after each change to a data entry cell 
        ar = self.wa[dpos[0]]
        if ar[dpos[1]] != new_val:
            # A value change has occurred
            ar[dpos[1]] = new_val
            self.wa[dpos[0]] = ar
            self.df.set_cell_value(dpos, new_val)
            self.dsply_table()

    def on_form_close(self):
        pass
            

def main():
    sl = SiteLoad()
    sl.add_new_row(['Light, LED', 12, 0.6, 6, 17, 5.0, 'AC'])


    print ('Starting Display')
    print (sl.get_dataframe())
    root = tk.Tk()        
    
    root.title("Base Frame Testing")
    Table(sl, root, "Del")
    root.mainloop()
    print('\nExiting Display')
    print (sl.get_dataframe())


        
if __name__ == '__main__':
    main()
