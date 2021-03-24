#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 21 12:20:27 2018
Modified on 02/22/2019 for version 0.1.0

@author: Bob Hentz

-------------------------------------------------------------------------------
  Name:        FieldClasses.py
  Purpose:     Provides for the methods & data structures associated with
               Defining the atributes of a Solar PV System

  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)

               This program is distributed WITHOUT ANY WARRANTY;
               without even the implied warranty of MERCHANTABILITY
               or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""
from tkinter import *
import tkinter.ttk as ttk
import guiFrames as tbf

GRID_ARGS = ['column','columnspan', 'in_', 'ipadx', 'ipady',
             'padx', 'pady', 'row', 'rowspan', 'sticky']

def build_args(kw):
    """ Separate grid args from field args """
    gargs= dict()
    fargs = dict()
    for idx in range(len(GRID_ARGS)):
        ky = GRID_ARGS[idx]
        if ky in kw:
            gargs[ky] = kw.pop(ky)
    fargs = kw
    return fargs, gargs


class data_field:
    """ Record Structure for a data field consisting of:
        name    -  defines name for field data and also widget dict key
        Lbl_txt -  defines the form label used on data entry forms
        fld_data - defines the initial value of the field as well as 
                   the default value used on the data form
        """
    def __init__(self, name, lbl_txt, fld_data):
        self.name = name
        self.lbl = lbl_txt
        self.dat = fld_data
        self.typ = type(self.dat)   # Always return same type as initial value
        self.init_val = fld_data
        self.lbl_fld = None
        self.dat_fld = None

    def __str__(self):
        """ Create printable string from data """
        return '{0}\t{1}\t'.format(self.lbl, self.dat)

    def get_name(self):
        return self.name
        
    def get_label(self):
        """ Return the label """
        return self.lbl
    
    def read_data(self):
        """ Return the data """
        return self.dat

    def is_okay(self, val):
        """ Test for correct data type """
        try:
            k = self.typ(val)
            return True
        except ValueError:
            return False
            
    def get_data_type(self):
        """ Return the initial data type """
        return self.typ

    def reset_value(self):
        """ Reset data to initial value """
        self.dat = self.init_val
        
    def write_data(self, val):
        """ Update data to new val """
        if self.is_okay(val):
            self.dat = self.typ(val)
            return True
        return False
        

class option_field(data_field):
    """ Data Structure for data field dependent on a list selection 
        structure adds to basic data_field structure by incorporating:
        initial Options list - defines the starting set of options
        current options list - defines the current set of options 
        option list source  - defines the source from which the options were derived"""
    def __init__(self, name, lbl_txt, fld_data, option_list, option_source):
        self.osrc = option_source
        self.iopts = option_list
        self.olist = option_list
        data_field.__init__(self, name, lbl_txt, fld_data)
        
    def get_list(self):
        # """ returns the current list of options filtered
        #    by current data entry """
        # return list(filter(lambda x: x.startswith(self.dat), self.olist))
        return self.olist

    def update_list(self, ls):
        """ Updates current option list with ls """
        self.olist = ls

    def update_source(self, sr):
        """ Updates source with sr value """
        self.osrc = sr
        
    def reset_options(self):
        """ Resets option list to initial values """
        self.olist = self.iopts
                
    def get_option_source(self):
        """ returns the option source """
        return self.osrc
        

class data_cell(ttk.Entry):
    """ Creates an Entry Field widget for displaying & updating a data field
        kargs include standard ttk.tkinter arguments plus:
            On_change - defines method to externally process changes
    """
    def __init__(self, parent_frame, data_src, **kargs):
        self.parent = parent_frame
        self.src = data_src
        self.kargs = kargs
        self.val = StringVar()
        self.set_val()
        self.show_field()
        
    def show_field(self):
        """ Display The Frame """  
        fargs, gargs = build_args(self.kargs)
        self.chg_cmd = fargs.pop('On_change', None)
        fargs['textvariable'] = self.val        
        ttk.Entry.__init__(self, self.parent, **fargs)
        self.grid(**gargs)
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
      
    def get_val(self):
        """ Method to get the contents of cell """
        return self.val.get()

    def set_val(self):
        if self.src.get_data_type() is float:
            self.val.set(self.src.read_data())     
        else:
            self.val.set(self.src.read_data())
        
    def on_enter(self, event):
        pass
               
    def on_leave(self, event):
        """ Method to process cell content changes """
        val = self.get_val()
        if val is not self.src.read_data():
            if self.chg_cmd is not None:
                self.chg_cmd(self.src.get_name(), val)
            self.src.write_data(val)
                  
class list_cell(ttk.Combobox):
    """ Creates an Option List Field widget for displaying & updating source data 
        kargs include standard ttk.tkinter arguments Plus:
            On_change - defines method to externally process changes
    """
    def __init__(self, parent_frame, data_src, **kargs):
        self.parent = parent_frame
        self.src = data_src
        self.kargs = kargs
        self.val = StringVar()
        self.set_val()
        self.show_field()
        
    def show_field(self):
        """ Display The Frame """              
        fargs, gargs = build_args(self.kargs)
        self.chg_cmd = fargs.pop('On_change', None)
        fargs['textvariable'] = self.val
        fargs['values'] = self.src.get_list()
        if not 'postcommand' in fargs:
            fargs['postcommand'] = self.on_click
        ttk.Combobox.__init__(self, self.parent, **fargs)
        self.grid(**gargs)
#        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

    def on_click(self):
        """ invoked when dropdown arrow is clicked """
        # self['values'] = list(filter(lambda x: x.startswith(self.val.get()),
        #                                        self.src.get_list()))
        pass
        
    def get_val(self):
        """ Method to get the contents of cell """
        return self.val.get()

    def set_val(self):
        """ Sets value of underlying data source """
        self.val.set(self.src.read_data())
               
    def on_leave(self, event):
        """ Method to process cell content changes """
        val = self.get_val()
        if val is not self.src.read_data():
            if self.chg_cmd is not None:
                self.chg_cmd(self.src.get_name(), val)
            self.src.write_data(val)

class note_cell(Text):
    """ Creates an Note Field widget for displaying & updating source data 
        kargs include standard ttk.tkinter arguments plus:
            On_change - defines method to externally process changes
    """
    def __init__(self, parent_frame, data_src, **kargs): 
        self.parent = parent_frame
        self.src = data_src
        self.show_field

    def show_field(self):
        """ Display The Frame """              
        fargs, gargs = build_args(self.kargs)
        self.chg_cmd = fargs.pop('On_change', None)
        fargs['textvariable'] = self.val
        fargs['values'] = list(filter(lambda x: x.startswith(self.val.get()), 
                                               self.opts))
        Text.__init__(self, self.parent, **fargs)
        self.grid(**gargs)
        self.insert('1.0', self.src.read_data())
        self.bind('<Leave>', self.on_chg)


    def get_val(self):
        return self.get('1.0', END+'-1c')

    def on_chg(self, event):
        """ Method to process cell content changes """
        val = self.get_val()
        if val is not self.src.read_data():
            if self.chg_cmd is not None:
                self.chg_cmd(self.src.get_name(), val)
            else:
                self.src.write_data(val)



def main():
    print ('Field Classes says - Hello World')
    battery_types = {'FLA':('Flooded Lead Acid', 0.90),
                     'GEL':('Gelled Electrolyte Sealed Lead-Acid', 0.92 ),
                     'AGM':('Sealed Absorbed Glass Mat Lead-Acid', 0.94)
            }   
    olf = option_field('b_typ','Type', '', list(battery_types), battery_types)
    print(olf.get_list())
    print(olf.read_data())


if __name__ == '__main__':
    main()            
