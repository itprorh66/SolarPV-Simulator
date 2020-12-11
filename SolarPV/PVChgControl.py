#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 13:39:02 2018
modified   Wed Dec 12 2018 (Issue #5)
Modified on 02/25/2019 for version 0.1.0

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
import numpy as np
from math import log
import pandas as pd
from FormBuilder import *
from FieldClasses import *
from Component import *
from Parameters import chgcntl_types

class PVChgControl(Component):
    """ Methods associated with battery definition, display, and operation """

    def __init__(self, master, **kargs):
        Component.__init__(self, master, 'Charge Control', **kargs)
        self._chg_break = 0.85

    def _define_attrbs(self):
        """ Define Charge Controller Attributes """
        self.args = {
                     'c_mfg':data_field('c_mfg', 'Manufactuerer:',''),
                     'c_mdl':data_field('c_mdl', 'Model:',''),
                     'Name':data_field('Name','Description:', ''),
                     'c_type':option_field('c_type','Type:', '',
                                           list(chgcntl_types), chgcntl_types),
                     'c_pvmxv':data_field('c_pvmxv', 'Max PV Voltage (Vdc):',0.0),
                     'c_pvmxi':data_field('c_pvmxi', 'Max PV Current (A):',0.0),
                     'c_bvnom':data_field('c_bvnom', 'Bat Volts (Vdc):',0.0),
                     'c_mvchg':data_field('c_mvchg', 'Max Chg Volts (Vdc):',0.0),
                     'c_michg':data_field('c_michg', 'Max Chg Current (A):',0.0),
                     'c_midschg':data_field('c_midschg', 'Max Dischg Current (A):',0.0),
                     'c_tmpc':data_field('c_tmpc', 'Temp Compensation Coefficient (/C)', 0.0),
                     'c_tmpr':data_field('c_tmpc', 'Temp Rating (C)', 25.0),
                     'c_cnsmpt':data_field ('c_stdbyPow', 'Self Consumption (W):',0.0),
                     'c_eff':data_field('c_eff', 'Efficiency (%):',90.0),
                 }
    def check_arg_definition(self):
        """ Verify adequate Charge Controller definition """
        bf, msg = self.master.bnk.check_arg_definition()
        if self.read_attrb('c_type') == "":
            return False, 'PV Charge Controller Type not defined'
        if self.read_attrb('c_pvmxv') == 0.0:
            return False, 'PV Charge Controller PVMax Volts not defined'
        if self.read_attrb('c_pvmxi') == 0.0:
            return False, 'PV Charge Controller PVMax Current not defined'
        if self.read_attrb('c_mvchg') == 0.0:
            return False, 'PV Charge Controller Max Charge Current not defined'
        if self.read_attrb('c_midschg') == 0.0:
            return False, 'PV Charge Controller Max Discharge Current not defined'
        if self.read_attrb('c_bvnom') == 0.0:
            return False, 'PV Charge Controller Bat Nom Volts not defined'
        if self.master.ary.read_attrb('ary_Vmp') > self.read_attrb('c_pvmxv'):
            return False, 'Charge Control Max PVvolts mismatch Array Voltage'
        if bf and (self.master.bnk.read_attrb('bnk_vo') > self.read_attrb('c_bvnom')):
            return False, 'Charge Control Max Bat volts mismatch Bank Voltage'
        return True, ""

    def Control_Output(self, ArP, ArV, ArI, acLd, dcLd, wkDict):
        """Computes the controlled Voltage & current output used to either power
           the load or charge/discharge a battery bank. Updates the
           battery bank and contents of wkDict based on results of computations"""
        sysLd = self.read_attrb('c_cnsmpt')
        ctype = self.read_attrb('c_type')
        totUsrLd = dcLd + acLd
        invFlg  = self.master.inv.is_defined()
        bnkFlg  = self.master.bnk.is_defined()
        if invFlg:
            sysLd += self.master.inv.read_attrb('Pnt')
            sysLd += self.master.inv.compute_dc_power(acLd)
        sysLd = (100*(totUsrLd + sysLd)/self.read_attrb('c_eff')) - totUsrLd
        pload = totUsrLd + sysLd
        vout = min(ArV, self.read_attrb('c_pvmxv'))
        iout = min(ArI, self.read_attrb('c_pvmxi'))
        drain = ArP - pload*1.1
        #Test for Batbank and either charge state or ability to discharge
        if bnkFlg and (drain >= 0 or (drain <0 and self.master.bnk.is_okay())):
            # A battery bank exists and it is usable for charging or discharging
            bnkok = self.master.bnk.is_okay()
            bv = self.master.bnk.get_volts()
            if bv <= 0:
                bv = 1
            if drain >= 0:
                vout = min(vout, self.read_attrb('c_mvchg'))
                bv = bv*1.2
                if ctype  == 'MPPT':
                    iout = max(drain/vout, drain/bv)                                       
                else:                   
                    iout = min(drain/vout, drain/bv)
    
            else:
                # Discharge Battery state
                if abs(drain) <= self.master.bnk.current_power():
                    if vout == 0.0 or iout == 0.0:
                        vout = bv
                        iout = min(self.read_attrb('c_midschg'), -drain/vout)
                    iout= -1* iout
                else:
                    # Bnk can't provide needed power
                    if ArP < sysLd:
                        msg = 'Insufficient Array & Bank power to sustain System operation'
                        msg += '\n {0:.2f} watts needed but only {1:.2f} watts generated'
                        wkDict['Error'] = (msg.format(sysLd, ArP), 'Warning')
                    else:
                        iout = -1 * ((ArP-sysLd)/vout)
            #update Bank State
            self.master.bnk.update_soc(iout, wkDict)
            if ArP - wkDict['BD'] -pload >= 0.0:
                #okay met pload requirements
                wkDict['PO'] = pload
            elif ArP - wkDict['BD'] - sysLd >= 0:
                wkDict['PO'] = ArP - sysLd
            else:
                msg = 'Insufficient Array + Bank power to sustain System operation'
                msg += '\n {0:.2f} watts needed but only {1:.2f} watts generated'
                wkDict['Error'] = (msg.format(sysLd, ArP), 'Warning')
                wkDict['PO'] = 0.0                               
            if totUsrLd > 0: 
                wkDict['PS'] = wkDict['PO']/pload              
            if ArP > 0:
                wkDict['DE'] = wkDict['PO'] /ArP     
        else:
            # No battery exists or battery can't be discharged further
            if ArP < sysLd and totUsrLd > 0:
                msg = 'Insufficient Array power to sustain System operation'
                msg += '\n {0:.2f} watts needed but only {1:.2f} watts available' 
                wkDict['Error'] = (msg.format(sysLd, ArP), 'Warning')
            vout = min(vout, self.read_attrb('c_mvchg') )
            iout = min(iout, self.read_attrb('c_midschg'))
            if self.read_attrb('c_type') == 'MPPT':
                iout = max(iout, self.read_attrb('c_midschg'))
            pout = min(ArP, vout*iout, pload)
            if ArP > 0 and totUsrLd > 0:
                wkDict['PO'] = pout
                wkDict['DE'] = wkDict['PO']/ArP
            if ArP > pload and totUsrLd > 0:
                wkDict['PS'] = pout/pload

    def display_input_form(self, parent_frame):
        """ Generate the Data Entry Form """
        self.parent_frame = parent_frame
        self.form = ChgCntlForm(parent_frame, self, row=1, column=1,  
                                width= 300, height= 300, borderwidth= 5, 
                                relief= GROOVE, padx= 10, pady= 10, 
                                ipadx= 5, ipady= 5)
        return self.form

""" The Charge Controller Data Entry Window Definition """
class ChgCntlForm(DataForm):
    def __init__(self, parent_frame, data_src, **kargs):
        DataForm.__init__(self, parent_frame, data_src, **kargs)

    def define_layout(self):
        self.wdg_dict = {
                 'blank1': self.create_space(40, row= 1, column= 0, sticky=(EW),
                                           columnspan= 10),
                'lbl_mfg':self.create_label(self.src.get_attrb('c_mfg'),
                                            row= 2, column= 0, justify= LEFT,
                                            sticky= (EW)),
                'c_mfg': self.create_entry(self.src.get_attrb('c_mfg'),
                                           row= 2, column= 1, sticky=(EW),
                                           width= 25, justify= CENTER, columnspan= 5),
                'lbl_mdl': self.create_label(self.src.get_attrb('c_mdl'),
                                            row= 3, column= 0, justify= LEFT),
                'c_mdl': self.create_entry(self.src.get_attrb('c_mdl'),
                                           row= 3, column= 1, sticky=(EW),
                                           justify= CENTER, width= 25, columnspan= 3),
                'lbl_typ': self.create_label(self.src.get_attrb('c_type'),
                                            row= 3, column= 7, justify= RIGHT),
                'c_type': self.create_dropdown(self.src.get_attrb('c_type'),
                                           row= 3, column= 8, sticky=(EW),
                                           justify= CENTER, width= 10),
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

                'lbl_mxv':self.create_label(self.src.get_attrb('c_pvmxv'),
                                             row= 6, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc61': self.create_space(2, row= 6, column= 1, sticky= (EW)),
                'c_pvmxv': self.create_entry(self.src.get_attrb('c_pvmxv'),
                                             row= 6, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
               'spc63': self.create_space(2, row= 6, column= 3, sticky= (EW)),
               'lbl_isc': self.create_label(self.src.get_attrb('c_pvmxi'),
                                             row= 6, column= 4, justify= RIGHT,
                                            sticky= (EW)),
               'c_pvmxi': self.create_entry(self.src.get_attrb('c_pvmxi'),
                                             row= 6, column= 5, justify= CENTER,
                                            sticky= (EW), width= 10),
                'lbl_bv':self.create_label(self.src.get_attrb('c_bvnom'),
                                             row= 7, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc71': self.create_space(2, row= 7, column= 1, sticky= (EW)),
                'c_bvnom': self.create_entry(self.src.get_attrb('c_bvnom'),
                                             row= 7, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),

                'lbl_mvchg':self.create_label(self.src.get_attrb('c_mvchg'),
                                             row= 7, column= 4, justify= RIGHT,
                                            sticky= (EW)),
                'c_mvchg': self.create_entry(self.src.get_attrb('c_mvchg'),
                                             row= 7, column= 5, justify= CENTER,
                                            sticky= (EW), width= 10),

                'lbl_michg':self.create_label(self.src.get_attrb('c_michg'),
                                             row= 8, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc81': self.create_space(2, row= 8, column= 1, sticky= (EW)),
                'c_michg': self.create_entry(self.src.get_attrb('c_michg'),
                                             row= 8, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
                'lbl_mvdchg':self.create_label(self.src.get_attrb('c_midschg'),
                                             row= 8, column= 4, justify= RIGHT,
                                            sticky= (EW)),
                'c_midschg': self.create_entry(self.src.get_attrb('c_midschg'),
                                             row= 8, column= 5, justify= CENTER,
                                            sticky= (EW), width= 10),

               'lbl_tmpc': self.create_label(self.src.get_attrb('c_tmpc'),
                                             row= 9, column= 0, justify= RIGHT,
                                            sticky= (W)),
                'spc91': self.create_space(2, row= 9, column= 1, sticky= (EW)),
                'c_tmpc': self.create_entry(self.src.get_attrb('c_tmpc'),
                                             row= 9, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
                'lbl_tmpr':self.create_label(self.src.get_attrb('c_tmpr'),
                                             row= 9, column=4, justify= RIGHT,
                                            sticky= (EW)),
                'spc94': self.create_space(2, row= 9, column= 5, sticky= (EW)),
                'c_tmpr': self.create_entry(self.src.get_attrb('c_tmpr'),
                                             row= 9, column= 5, justify= CENTER,
                                            sticky= (EW), width= 10),

               'lbl_sPow': self.create_label(self.src.get_attrb('c_cnsmpt'),
                                             row= 10, column= 0, justify= RIGHT,
                                            sticky= (W)),
                'spc101': self.create_space(2, row= 10, column= 1, sticky= (EW)),
                'c_cnsmpt': self.create_entry(self.src.get_attrb('c_cnsmpt'),
                                             row= 10, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
                'lbl_eff':self.create_label(self.src.get_attrb('c_eff'),
                                             row= 10, column=4, justify= RIGHT,
                                            sticky= (EW)),
                'spc104': self.create_space(2, row= 10, column= 5, sticky= (EW)),
                'c_eff': self.create_entry(self.src.get_attrb('c_eff'),
                                             row= 10, column= 5, justify= CENTER,
                                            sticky= (EW), width= 10),
                }

def main():
    print('PVChgControl.Py check complete')


if __name__ == '__main__':
    main()
