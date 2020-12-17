#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created   on Mon Jul 30 11:01:58 2018
Modified  on Mon Sep 17 19:33:02 2018
Modified on 02/22/2019 for version 0.1.0

@author: Bob Hentz

-------------------------------------------------------------------------------
  Name:        PVBattery.py
  Purpose:     Provides for the methods & data structures associated with
               Implementing the Battery of a Solar PV System

  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)

               This program is distributed WITHOUT ANY WARRANTY;
               without even the implied warranty of MERCHANTABILITY
               or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""
from tkinter import *
from FormBuilder import DataForm
from FieldClasses import data_field, option_field
from Parameters import battery_types
from Component import Component

        
class PVBattery(Component):
    """ Methods associated with battery definition, display, and operation """

    def __init__(self, master, **kargs):
        Component.__init__(self, master, 'Battery', **kargs)
               
    def _define_attrbs(self):    
        self.args = {
                 'b_mfg':data_field('b_mfg','Manufacturer:', ''),
                 'b_mdl':data_field('b_mdl','  Model:', ''),
                 'b_desc':data_field('b_desc','Description:', ''),
                 'b_typ':option_field('b_typ','Type:', '',
                                      list(battery_types), battery_types),
                 'b_nomv':data_field('b_nomv','Nominal Voltage (VDC):', 0.0),
                 'b_rcap':data_field('b_rcap','Rated Capacity (AH):', 0.0),
                 'b_rhrs':data_field('b_rhrs','Hour Basis for Rating:', 100),                           
                 'b_ir':data_field('b_ir','Internal Resistance (Ohms):', 0.0),
                 'b_stdTemp':data_field('b_stdTemp','Rated temperature (C):', 25.0),
                 'b_tmpc':data_field('b_tmpc','Temp Coeficient (C):', 0.0),
                 'b_mxDschg':data_field('b_mxDschg', "Max No. of Discharge Cycles:", 1000),
                 'b_mxDoD':data_field('b_mxDoD', 'Depth of Discharge % for Max Lifecycle:', 50.0)
                }

                              
    def check_arg_definition(self):
        """ Verify adequate battery definition """
        if (self.read_attrb('b_nomv') == 0.0 or 
               self.read_attrb('b_rcap')  == 0.0 or
               self.read_attrb('b_rhrs') == 0.0 or
               self.read_attrb('b_ir') == 0.0 or
#               self.read_attrb('b_tmpc') == 0.0 or
               self.read_attrb('b_stdTemp') == 0.0 or
               self.read_attrb('b_typ') == ""):           
            msg = 'Battery Specification undefined or incomplete'
            return False, msg
        return True,''
 
    def display_input_form(self, parent_frame):
        self.parent_frame = parent_frame
        self.form = BatteryForm(parent_frame, self, row=1, column=1,  width= 300, height= 300,
                      borderwidth= 5, relief= GROOVE, padx= 10, pady= 10, ipadx= 5, ipady= 5)
        return self.form
            
    def perform_unique_updates(self, attrib, val):
        """ No unique Updates required """
        pass
    
    
class BatteryForm(DataForm):
    def __init__(self, parent_frame, data_src, **kargs):
        DataForm.__init__(self, parent_frame, data_src, **kargs)

    def define_layout(self):
        self.wdg_dict = {
                'blank1': self.create_space(40, row= 1, column= 0, sticky=(EW),
                                           columnspan= 10),               
                'lbl_mfg':self.create_label(self.src.get_attrb('b_mfg'),
                                            row= 2, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc21': self.create_space(2, row= 2, column= 1, sticky= (EW)),
                'b_mfg': self.create_entry(self.src.get_attrb('b_mfg'),
                                           row= 2, column= 2, sticky=(EW), 
                                           name= self.src.get_attrb_name('b_mfg'),
                                           justify= CENTER),               
                'spc22': self.create_space(5, row= 2, column= 3, sticky= (EW)),
                'lbl_mdl': self.create_label(self.src.get_attrb('b_mdl'),
                                            row= 2, column= 5, justify= RIGHT,
                                            sticky= (EW)),
#                'spc23': self.create_space(2, row= 2, column= 5, sticky= (EW)),
                'b_mdl': self.create_entry(self.src.get_attrb('b_mdl'),
                                           row= 2, column= 6, sticky=(EW), 
                                           justify= CENTER),               
                'spc24': self.create_space(5, row= 2, column= 7, sticky= (EW)),
                'lbl_typ': self.create_label(self.src.get_attrb('b_typ'),
                                            row= 2, column= 8, justify= RIGHT,
                                            sticky= (EW)),
                'spc25': self.create_space(2, row= 2, column= 9, sticky= (EW)),
                'b_typ': self.create_dropdown(self.src.get_attrb('b_typ'),
                                           row= 2, column= 10, sticky=(EW), 
                                           justify= CENTER),               
                'lbl_desc': self.create_label(self.src.get_attrb('b_desc'),
                                            row= 3, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc31': self.create_space(2, row= 3, column= 1, sticky= (EW)),
                'b_desc': self.create_entry(self.src.get_attrb('b_desc'),
                                           row= 3, column= 2, sticky=(EW), 
                                           justify= LEFT, columnspan= 9) ,              
                'lbl_ir': self.create_label(self.src.get_attrb('b_ir'),
                                            row= 4, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan= 3),
#                'spc41': self.create_space(2, row= 4, column= 2, sticky= (EW)),
                'b_ir': self.create_entry(self.src.get_attrb('b_ir'),
                                           row= 4, column= 3, sticky=(EW), 
                                           justify= CENTER) ,              
                 'lbl_nv': self.create_label(self.src.get_attrb('b_nomv'),
                                            row= 4, column= 7, justify= RIGHT,
                                            sticky= (EW), columnspan= 3),
#                'spc41': self.create_space(2, row= 4, column= 2, sticky= (EW)),
                'b_nomv': self.create_entry(self.src.get_attrb('b_nomv'),
                                           row= 4, column= 10, sticky=(EW), 
                                           justify= CENTER,
                                           On_change= self.src.on_form_change),                
                'lbl_cap': self.create_label(self.src.get_attrb('b_rcap'),
                                            row= 5, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan= 3),
#                'spc41': self.create_space(2, row= 5, column= 2, sticky= (EW)),
                'b_rcap': self.create_entry(self.src.get_attrb('b_rcap'),
                                           row= 5, column= 3, sticky=(EW), 
                                           justify= CENTER,
                                           On_change= self.src.on_form_change),
                 'lbl_hrs': self.create_label(self.src.get_attrb('b_rhrs'),
                                            row= 5, column= 7, justify= RIGHT,
                                            sticky= (EW), columnspan= 3),
#                'spc41': self.create_space(2, row= 5, column= 2, sticky= (EW)),
                'b_rhrs': self.create_entry(self.src.get_attrb('b_rhrs'),
                                           row= 5, column= 10, sticky=(EW), 
                                           justify= CENTER),               
 
                'lbl_tc': self.create_label(self.src.get_attrb('b_tmpc'),
                                            row= 6, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan= 3),
#                'spc41': self.create_space(2, row= 5, column= 2, sticky= (EW)),
                'b_tmpc': self.create_entry(self.src.get_attrb('b_tmpc'),
                                           row= 6, column= 3, sticky=(EW), 
                                           justify= CENTER) ,              
                 'lbl_st': self.create_label(self.src.get_attrb('b_stdTemp'),
                                            row= 6, column= 7, justify= RIGHT,
                                            sticky= (EW), columnspan= 3),
#                'spc41': self.create_space(2, row= 5, column= 2, sticky= (EW)),
                'b_stdTemp': self.create_entry(self.src.get_attrb('b_stdTemp'),
                                           row= 6, column= 10, sticky=(EW), 
                                           justify= CENTER),               
 
                'lbl_mxdc': self.create_label(self.src.get_attrb('b_mxDschg'),
                                            row= 7, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan= 3),
#                'spc41': self.create_space(2, row= 5, column= 2, sticky= (EW)),
                'b_mxDschg': self.create_entry(self.src.get_attrb('b_mxDschg'),
                                           row= 7, column= 3, sticky=(EW), 
                                           justify= CENTER) ,              
                 'lbl_mxDoD': self.create_label(self.src.get_attrb('b_mxDoD'),
                                            row= 7, column= 7, justify= RIGHT,
                                            sticky= (EW), columnspan= 3),
#                'spc41': self.create_space(2, row= 5, column= 2, sticky= (EW)),
                'b_mxDoD': self.create_entry(self.src.get_attrb('b_mxDoD'),
                                           row= 7, column= 10, sticky=(EW), 
                                           justify= CENTER),               

                'blank1': self.create_space(40, row= 8, column= 0, sticky=(EW),
                                           columnspan= 10)               
            
                }


def main():
    print('PVBattery.py Load Check')    
    


if __name__ == '__main__':
    main()            