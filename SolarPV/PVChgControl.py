#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 13:39:02 2018

@author: Bob Hentz

-------------------------------------------------------------------------------
  Name:        PVChgControl.py
  Purpose:     Provides for the methods & data structures associated with
               Implementing the Charge Controller of a Solar PV System

  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)

               This program is distributed WITHOUT ANY WARRANTY;
               without even the implied warranty of MERCHANTABILITY
               or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""
from FormBuilder import *
from FieldClasses import *
from Component import *


class PVChgControl(Component):
    """ Methods associated with battery definition, display, and operation """

    def __init__(self, master, **kargs):
        Component.__init__(self, master, 'Charge Control', **kargs)
               
    def _define_attrbs(self):    
        self.args = {
                     'c_mfg':data_field('c_mfg', 'Manufactuerer:',''),
                     'c_mdl':data_field('c_mdl', 'Model:',''),
                     'Name':data_field('Name','Description:', ''),
                     'mxv':data_field('mxv', 'Max Voltage (Vdc):',0.0),
                     'isc':data_field('isc', 'Short Circuit Current (A):',0.0),
                     'bvnom':data_field('bvnom', 'Battery Nominal Volts:',0.0),
                     'c_mxPow':data_field('c_mxPow', 'Max-Pow (W):',0.0),
                     'c_stdbyPow':data_field ('c_stdbyPow', 'Standby-Power (W):',0.0),
                     'c_eff':data_field('c_eff', 'Efficiency (%):',0.0),
                 }
    def check_arg_definition(self):
        """ Verify adequate battery definition """
        if self.read_attrb('c_mfg') == "" or self.read_attrb('c_mdl') == '':
            return False, 'PV Charge Controller is undefined'      
        return True, msg
 
    def display_input_form(self, parent_frame):
        self.parent_frame = parent_frame
        self.form = ChgCntlForm(parent_frame, self, row=1, column=1,  width= 300, height= 300,
                      borderwidth= 5, relief= GROOVE, padx= 10, pady= 10, ipadx= 5, ipady= 5)
        return self.form
            

class ChgCntlForm(DataForm):
    def __init__(self, parent_frame, data_src, **kargs):
        DataForm.__init__(self, parent_frame, data_src, **kargs)

    def define_layout(self):
        self.wdg_dict = {
                 'blank1': self.create_space(40, row= 1, column= 0, sticky=(EW),
                                           columnspan= 10),
                'lbl_mfg':self.create_label(self.src.get_attrb('c_mfg'),
                                            row= 2, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc21': self.create_space(2, row= 2, column= 1, sticky= (EW)),
                'c_mfg': self.create_entry(self.src.get_attrb('c_mfg'),
                                           row= 2, column= 2, sticky=(EW),
                                           width= 45, justify= CENTER, columnspan= 5),
    #            'spc22': self.create_space(20, row= 2, column= 3, sticky= (EW)),
                'lbl_mdl': self.create_label(self.src.get_attrb('c_mdl'),
                                            row= 3, column= 0, justify= RIGHT),
                'spc31': self.create_space(2, row= 3, column= 1, sticky= (EW)),
                'c_mdl': self.create_entry(self.src.get_attrb('c_mdl'),
                                           row= 3, column= 2, sticky=(EW),
                                           justify= CENTER, width= 35, columnspan= 5),
                'lbl_desc': self.create_label(self.src.get_attrb('Name'),
                                            row= 4, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc31': self.create_space(2, row= 4, column= 1, sticky= (EW)),
                'Name': self.create_entry(self.src.get_attrb('Name'),
                                           row= 4, column= 2, sticky=(EW),
                                           justify= LEFT, columnspan= 8) ,

                'col40': self.create_space(10, row= 5, column= 0, sticky= (EW)),
                'col41': self.create_space(10, row= 5, column= 1, sticky= (EW)),
                'col42': self.create_space(10, row= 5, column= 2, sticky= (EW)),
                'col43': self.create_space(10, row= 5, column= 3, sticky= (EW)),
                'col44': self.create_space(10, row= 5, column= 4, sticky= (EW)),
                'col45': self.create_space(10, row= 5, column= 5, sticky= (EW)),
                'col46': self.create_space(10, row= 5, column= 6, sticky= (EW)),
                'col47': self.create_space(10, row= 5, column= 7, sticky= (EW)),
                'col48': self.create_space(10, row= 5, column= 8, sticky= (EW)),
                'col49': self.create_space(10, row= 5, column= 9, sticky= (EW)),
                'col410': self.create_space(10, row= 5, column= 10, sticky= (EW)),

                'lbl_mxv':self.create_label(self.src.get_attrb('mxv'),
                                             row= 6, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc61': self.create_space(2, row= 6, column= 1, sticky= (EW)),
                'mxv': self.create_entry(self.src.get_attrb('mxv'),
                                             row= 6, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
               'spc62': self.create_space(2, row= 6, column= 3, sticky= (EW)),
               'lbl_isc': self.create_label(self.src.get_attrb('isc'),
                                             row= 6, column= 4, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
                'isc': self.create_entry(self.src.get_attrb('isc'),
                                             row= 6, column= 6, justify= CENTER,
                                            sticky= (EW), width= 10),
                'lbl_bv':self.create_label(self.src.get_attrb('bvnom'),
                                             row= 6, column= 8, justify= RIGHT,
                                            sticky= (EW)),
                'spc69': self.create_space(2, row= 6, column= 9, sticky= (EW)),
                'bvnom': self.create_entry(self.src.get_attrb('bvnom'),
                                             row= 6, column= 10, justify= CENTER,
                                            sticky= (EW), width= 10),
 
                'lbl_mxp':self.create_label(self.src.get_attrb('c_mxPow'),
                                             row= 7, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc71': self.create_space(2, row= 7, column= 1, sticky= (EW)),
                'c_mxPow': self.create_entry(self.src.get_attrb('c_mxPow'),
                                             row= 7, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
               'lbl_sPow': self.create_label(self.src.get_attrb('c_stdbyPow'),
                                             row= 7, column= 4, justify= RIGHT,
                                            sticky= (W), columnspan = 2,
                                            width=30),
                'c_stdbyPow': self.create_entry(self.src.get_attrb('c_stdbyPow'),
                                             row= 7, column= 6, justify= CENTER,
                                            sticky= (EW), width= 10),
                'lbl_eff':self.create_label(self.src.get_attrb('c_eff'),
                                             row= 7, column= 8, justify= RIGHT,
                                            sticky= (EW)),
                'spc79': self.create_space(2, row= 7, column= 9, sticky= (EW)),
                'c_eff': self.create_entry(self.src.get_attrb('c_eff'),
                                             row= 7, column= 10, justify= CENTER,
                                            sticky= (EW), width= 10),           
                }

def main():
    print('PVChgControl.Py check complete')


if __name__ == '__main__':
    main()            