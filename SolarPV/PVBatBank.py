#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 27 17:00:07 2018
Modified   Wed Dec  5 2018 (Fix Issue 2, Handle DC Loads)
Modified on 02/25/2019 for version 0.1.0
Modified on 03/06/2019 to correct in updating soc

@author: Bob Hentz

-------------------------------------------------------------------------------
  Name:        PVBatBank.py
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
import numpy as np
from math import log
import pandas as pd
from FormBuilder import DataForm
from FieldClasses import data_field
from Parameters import battery_types
from Component import Component
from guiFrames import plot_graphic
#from PVUtilities import create_time_mask

class PVBatBank(Component):
    """ Methods associated with battery definition, display, and operation """
    def __init__(self, master, **kargs):
        Component.__init__(self, master, 'Battery Bank', **kargs)
        
        self.chg_cycle_count = [0,0]
        self.tot_cycles = 0
        self.bnk_vo = 0
        self.soc = 1.0
        self.cur_cap = None
        self.max_dischg_cycles = None
        self.max_dischg_dod = None

    def _define_attrbs(self):
        self.args = {
                     'doa':data_field('doa','Days of Autonomy:  ',  0),
                     'doc':data_field('doc','Depth of Discharge (%):  ',  100.0),
                     'bnk_uis':data_field('bnk_uis','Units in Series:  ',  1),
                     'bnk_sip':data_field('bnk_sip','Strings in Parallel:  ',  1),
                     'bnk_tbats':data_field('bnk_tbats','Total Bank Batteries:  ',  1),
                     'bnk_cap':data_field('bnk_cap','Bank Capacity (A-H):  ',  0.0),
                     'bnk_vo':data_field('bnk_vo','Bank Voltage:  ',  0.0)
                    }

    def update_cycle_counts(self, delta_soc):
        """ Compute the number of battery charging cycles """
        if self.max_dischg_cycles is None or self.max_dischg_dod is None:
            self.max_dischg_cycles = self.parts[0].read_attrb('b_mxDschg')
            self.max_dischg_dod = self.parts[0].read_attrb('b_mxDoD')
        if delta_soc != 0:
            if delta_soc < 0:
                self.tot_cycles += (abs(delta_soc)*100)/(2*self.max_dischg_dod)

    def bank_lifecycle(self):
        """ Estimate Life expectancy of battery """
        if self.max_dischg_cycles is not None and self.max_dischg_dod is not None:
            lc = self.max_dischg_cycles/self.tot_cycles
            if lc > 5.0:
                return 5.0
            return lc
        else:
            return 0
    
    def initialize_bank(self, socpt = 0.75):
        """ Set Battery Bank status to known starting point """
        self.chg_cycle_count = [0,0]
        self.tot_cycles = 0 
        self.soc= socpt + (self.read_attrb('doc')/100)*(1-socpt)
        self.cur_cap = self.read_attrb('bnk_cap')*self.soc
        self.set_volts()
    
    def set_volts(self):
        """ set Bank Voltage """
        bnk_vnom = self.read_attrb('bnk_vo')
        eff = battery_types[self.parts[0].read_attrb('b_typ')][1]
        if self.soc == 1:
            self.bnk_vo = bnk_vnom
        elif self.soc == 0:
            self.bnk_vo = 0            
        else:
            try:
                self.bnk_vo = eff*((bnk_vnom*1.2/6.22)*log(self.soc))+ bnk_vnom
            except ValueError:
                print(' eff= {0}, bnk_vnom= {1}, soc= {2}'.format(
                        eff, bnk_vnom, self.soc))
                        
    def current_capacity(self):
        """ return AH capacity available from Battery Bank """
        if self.cur_cap == None or self.soc == 1:
            self.soc = 1
            self.cur_cap = self.read_attrb('bnk_cap')
        return self.read_attrb('bnk_cap')*self.soc
    
    def current_power(self):
        """ returns available battery power in watts. """
        return self.current_capacity() * self.get_volts()
    
    def get_volts(self):
        """ Return Current Battery Voltage  """
        if self.soc == 1:
            self.bnk_vo = self.read_attrb('bnk_vo')
        return self.bnk_vo
    
    def get_soc(self):
        """ Return current Bnk SOC """
        return self.soc

    def is_okay(self):
        """ Tests for battery SOC above Minimum """
        return self.soc >  (1- (self.read_attrb('doc')/100))

    def perform_unique_updates(self, attrib, val):
        """ Update Bnk cap, vo, & tbats based on changes """
        self.update_attributes()
        self.form.wdg_dict['bnk_vo'].set_val()
        self.form.wdg_dict['bnk_cap'].set_val()        
        self.form.wdg_dict['bnk_tbats'].set_val()
        
    def update_attributes(self):
        """ Update bank attributes  """
        if len(self.parts) > 0:
            bat = self.parts[0]
            self.set_attribute('bnk_vo',(bat.read_attrb('b_nomv')*
                                           self.read_attrb('bnk_uis')))
            self.set_attribute('bnk_cap', (bat.read_attrb('b_rcap')*
                                        self.read_attrb('bnk_sip')))
            self.set_attribute('bnk_tbats',(self.read_attrb('bnk_uis')*
                                        self.read_attrb('bnk_sip')))        
    def get_total_cycles(self):
        """ return the total number of charging cycles experienced by battery """
        return self.tot_cycles

    def check_arg_definition(self):
        """ Verify adequate battery definition """
        msg = ''
        if len(self.parts) == 0:
            msg = 'Battery is undefined'
            return False, msg
        flag, msg = self.parts[0].check_arg_definition()
        if flag:
            self.update_attributes()
            return True, msg
        else:
            return flag, msg

    def validate_size_setting(self):
        """ triggerd by change in UIS or SIP """
        uis = 1
        sip = 1
        try:
            uis =  float(self.form.wdg_dict['bnk_uis'].get_val())
        except:
            self.set_attribute('bnk_uis', uis)
            self.form.wdg_dict['bnk_uis'].set_val()
        try:
            sip =  float(self.form.wdg_dict['bnk_sip'].get_val())
        except:
            self.set_attribute('bnk_sip', sip)
            self.form.wdg_dict['bnk_sip'].set_val()
        self.set_attribute('bnk_tbats', sip * uis)
        self.form.wdg_dict['bnk_tbats'].set_val()
        if len(self.parts) > 0:
            bat = self.parts[0]
            bvn = bat.read_attrb('b_nomv')
            bcp = bat.read_attrb('b_rcap')
            self.set_attribute('bnk_vo', uis * bvn )
            self.set_attribute('bnk_cap', sip * bcp)
            self.form.wdg_dict['bnk_vo'].set_val()
            self.form.wdg_dict['bnk_cap'].set_val()
        return True

    def compute_capacity_requirements(self):
        """Return required capacity to meet specified DOA """
        if self.check_arg_definition():
            doa = self.read_attrb('doa')
            doc = self.read_attrb('doc')/100
            typ = self.parts[0].read_attrb('b_typ')
            eff = 1
            if typ != '':
                eff = battery_types[typ][1]
            gv = self.master.site.read_attrb('gv')
            if gv == 0.0 or gv == '':
                gv = 120.0
            ld = sum(self.master.load.get_load_profile()['Total'])
            return round((doa*ld)/(gv*doc*eff))
        
    def update_soc(self, i_in, wkDict):
        """ Updates bank capacity by i_in and then updates the 
            Battery elements of wkDict """
        ermsg = 'SOC is less than 0 for i={0}, cap={1}. '
        new_soc = self.soc
        old_soc = self.soc
        i_chg = 0
        bd = 0
        if abs(i_in) > 0:
            i_chg = min(abs(i_in), self.current_capacity())
            i_chg = i_chg * (i_in/abs(i_in))
            bd = self.bnk_vo * i_chg        
            self.cur_cap += i_in
            if self.cur_cap > self.read_attrb('bnk_cap'):
               self.cur_cap = self.read_attrb('bnk_cap')
            if self.cur_cap <= 0:
                self.cur_cap = 0                
            new_soc = min(self.cur_cap/self.read_attrb('bnk_cap'), 1)
            assert new_soc >= 0, ermsg.format(i_in,self.cur_cap)
            self.soc = new_soc 
            self.set_volts()
        wkDict['BD'] = bd
        wkDict['BS'] = self.soc
        wkDict['BP'] = self.current_power()
        self.update_cycle_counts(old_soc - new_soc) 
      
    def show_bank_drain(self):
        """ Create graphic of Battery Bank Drain Performance  """
        if self.master.power_flow  is not None:
            xlabels = np.arange(24)
            pltslist = [
                {'label': 'Best Day Drain', 
                  'data': self.master.power_flow['BatDrain'].loc[
                          self.master.power_flow['DayofYear'] == self.master.mnthly_pwr_perfm[1]],
                  'type': 'Line', 'xaxis': xlabels, 
                  'width': 2.0, 'color': 'b'},
                {'label': 'Worst Day Drain', 
                  'data': self.master.power_flow['BatDrain'].loc[
                          self.master.power_flow['DayofYear'] == self.master.mnthly_pwr_perfm[2]],
                  'type': 'Line', 'xaxis': xlabels , 
                  'width': 2.0, 'color': 'r'}]
            dp = plot_graphic(self.master.rdw, 'Time of Day', 'Watts', xlabels, 
                                  pltslist, 'Range of Bank Drain', (6,4))

    def show_bank_soc(self):
        """ Create graphic of Battery Bank SOC Performance  """
        if self.master.power_flow  is not None:
            xlabels = np.arange(24)
            pltslist = [{'label': 'Best Day SOC', 
                         'data': self.master.power_flow ['BatSoc'].loc[
                                 self.master.power_flow['DayofYear'] == self.master.mnthly_pwr_perfm[1]],
                         'type': 'Line', 'xaxis': xlabels, 
                         'width': 2.0, 'color': 'b'},
                {'label': 'Worst Day SOC', 
                         'data': self.master.power_flow ['BatSoc'].loc[
                                 self.master.power_flow['DayofYear'] == self.master.mnthly_pwr_perfm[2]],
                         'type': 'Line', 'xaxis': xlabels , 
                         'width': 2.0, 'color': 'r'}]
            dp = plot_graphic(self.master.rdw, 'Time of Day', 'SOC', xlabels, 
                                  pltslist, 'Range of Bank SOC', (6,4))

    def create_overview(self):
        if self.master.power_flow  is not None:
            suns = self.master.site.get_sun_times(self.master.times.index)
            sr_soc = np.zeros(len(suns))
            ss_soc = np.zeros(len(suns))
            day = [None]*len(suns)
            for i in range(len(suns)):
                snr = suns['Sunrise'].iloc[i]
                sns = suns['Sunset'].iloc[i]
                snrtm = snr.floor('H')
                snstm = snr.ceil('H')
                day[i] = snrtm
                sr_soc[i] = self.master.power_flow.loc[snrtm]['BatSoc']
                ss_soc[i] = self.master.power_flow.loc[snstm]['BatSoc']
            bat_ovr = pd.DataFrame(data={'Sunrise':sr_soc, 'Sunset':ss_soc},
                                   index= day)        
            return bat_ovr
    
    def show_bank_overview(self):
        """ Create graphic of Battery Bank Overview Performance  """
        if self.master.power_flow  is not None:
            ovr = self.create_overview()
            xlabels = ovr.index
            pltslist = [{'label': 'Sunrise', 
                         'data': ovr['Sunrise'],
                         'type': 'Line', 'xaxis': xlabels, 
                         'width': 2.0, 'color': 'r'},
                       {'label': 'Sunset', 
                         'data': ovr['Sunset'],
                         'type': 'Line', 'xaxis': xlabels, 
                         'width': 2.0, 'color': 'b'}]
            dp = plot_graphic(self.master.rdw, 'Month', 'SOC', xlabels, 
                                  pltslist, 'Bank SOC', (6,4))

    def display_input_form(self, parent_frame):
        """ Generate the Data entry form for Battery Bank """
        self.parent_frame = parent_frame
        self.update_attributes()
        if len(self.parts) > 0:
            bat = self.parts[0]
            bvn = bat.read_attrb('b_nomv')
            bcp = bat.read_attrb('b_rcap')
            vo = self.read_attrb('bnk_uis') * bvn
            cap = self.read_attrb('bnk_sip') * bcp
            self.set_attribute('bnk_vo', self.read_attrb('bnk_uis') * bvn )
            self.set_attribute('bnk_cap', self.read_attrb('bnk_sip') * bcp )        
        self.form = BankForm(parent_frame, self, row=1, column=1,  width= 300, 
                      height= 300, borderwidth= 5, relief= GROOVE, padx= 10, 
                      pady= 10, ipadx= 5, ipady= 5, 
                      Formclose =  self.on_form_close)
        return self.form

    def on_form_close(self):
        if self.check_arg_definition():
            ideal_cap = self.compute_capacity_requirements()
            if ideal_cap > self.read_attrb('bnk_cap'):
                s = 'Insufficient Bank Capacity to meet DOA.  '
                s += ('Current Capacity only meets {0:.2f} Days'.
                      format(self.read_attrb('doa')*
                             self.read_attrb('bnk_cap')/ideal_cap))
                self.master.stw.show_message(s, 'Warning')
                

class BankForm(DataForm):
    def __init__(self, parent_frame, data_src, **kargs):
        DataForm.__init__(self, parent_frame, data_src, **kargs)


    def define_layout(self):
        self.wdg_dict = {
                'blank1': self.create_space(40, row= 1, column= 0, sticky=(EW),
                                           columnspan= 10),
                # Row 2
                'lbl_doa':self.create_label(self.src.get_attrb('doa'),
                                            row= 2, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc21': self.create_space(2, row= 2, column= 1, sticky= (EW)),
                'doa': self.create_entry(self.src.get_attrb('doa'),
                                           row= 2, column= 2, sticky=(EW),
                                           justify= CENTER),
                'spc23': self.create_space(5, row= 2, column= 3, sticky= (EW)),
                'lbl_doc': self.create_label(self.src.get_attrb('doc'),
                                            row= 2, column= 4, justify= RIGHT,
                                            sticky= (EW)),
                'spc25': self.create_space(2, row= 2, column= 5, sticky= (EW)),
                'doc': self.create_entry(self.src.get_attrb('doc'),
                                           row= 2, column= 6, sticky=(EW),
                                           justify= CENTER),
                'spc27': self.create_space(5, row= 2, column= 7, sticky= (EW)),
                # Row 3
                'lbl_uis': self.create_label(self.src.get_attrb('bnk_uis'),
                                            row= 3, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan= 3),
                'spc31': self.create_space(2, row= 3, column= 1, sticky= (EW)),
                'bnk_uis': self.create_entry(self.src.get_attrb('bnk_uis'),
                                           row= 3, column= 2, sticky=(EW),
                                           justify= CENTER, validate= 'focusout',
                                           validatecommand= self.src.validate_size_setting),
                'spc33': self.create_space(2, row= 3, column= 3, sticky= (EW)),
                'lbl_sip': self.create_label(self.src.get_attrb('bnk_sip'),
                                            row= 3, column= 4, justify= RIGHT,
                                            sticky= (EW), columnspan= 3),
                'spc35': self.create_space(2, row= 3, column= 5, sticky= (EW)),
                'bnk_sip': self.create_entry(self.src.get_attrb('bnk_sip'),
                                           row= 3, column= 6, sticky=(EW),
                                           justify= CENTER, validate= 'focusout',
                                           validatecommand= self.src.validate_size_setting),
                'spc37': self.create_space(2, row= 3, column= 7, sticky= (EW)),
                # Row 4
                'blank1': self.create_space(40, row= 4, column= 0, sticky=(EW),
                                           columnspan= 10),
                # Row 5
                'lbl_tbats': self.create_label(self.src.get_attrb('bnk_tbats'),
                                            row= 5, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan= 3),
                'spc51': self.create_space(2, row= 5, column= 1, sticky= (EW)),
                'bnk_tbats': self.create_entry(self.src.get_attrb('bnk_tbats'),
                                           row= 5, column= 2, sticky=(EW),
                                           justify= CENTER) ,
                # Row 6
                'lbl_cap': self.create_label(self.src.get_attrb('bnk_cap'),
                                            row= 6, column= 0, justify= RIGHT,
                                            width= 40, sticky= (EW), columnspan= 3),
                'spc61': self.create_space(2, row= 6, column= 1, sticky= (EW)),
                'bnk_cap': self.create_entry(self.src.get_attrb('bnk_cap'),
                                           row= 6, column= 2, sticky=(EW),
                                           justify= CENTER) ,
                'spc63': self.create_space(2, row= 6, column= 3, sticky= (EW)),
                'lbl_vo': self.create_label(self.src.get_attrb('bnk_vo'),
                                            row= 6, column= 4, justify= RIGHT,
                                            sticky= (EW), columnspan= 3),
                'spc65': self.create_space(2, row= 6, column= 5, sticky= (EW)),
                'bnk_vo': self.create_entry(self.src.get_attrb('bnk_vo'),
                                           row= 6, column= 6, sticky=(EW),
                                           justify= CENTER) ,
                # Row 7
                 'blank2': self.create_space(40, row= 7, column= 0, sticky=(EW),
                                           columnspan= 10)

                }

      
def main():
    print ('BatBank Startup check')



if __name__ == '__main__':
    main()