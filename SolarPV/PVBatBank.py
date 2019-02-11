#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 27 17:00:07 2018
Modified   Wed Dec  5 2018 (Fix Issue 2, Handle DC Loads)

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
import numpy as np
from math import log
import pandas as pd
from FormBuilder import *
from FieldClasses import *
from Parameters import battery_types
from Component import *
from guiFrames import plot_graphic
from PVUtilities import create_time_mask

class PVBatBank(Component):
    """ Methods associated with battery definition, display, and operation """
    def __init__(self, master, **kargs):
        Component.__init__(self, master, 'Battery Bank', **kargs)
#        self._dischrg_cycle_max = 85  #Used to determine %of charge required to define
#                                      #full discharge cycle
        self._chg_break = 0.85
        self.chg_cycle_count = [0,0]
        self.tot_cycles = 0
        self.bnk_vo = 0
        self.soc = 1.0
        self.max_dischg_cycles = None
        self.max_dischg_dod = None
        self.bat_drain = None

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
        
    def get_soc(self):
        """ Return current Bnk SOC """
        return self.soc

    def is_okay(self):
        """ Tests for battery ablityto provide power """
        return self.soc >  1.01 * (1- (self.read_attrb('doc')/100))

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
            
    def update_soc(self, drain):
        """ Update SoC and Vo based on drain
            Assumes Simulation Run has already checked valid definitions"""
        i_chg = 0.0
        max_dod = 1- self.read_attrb('doc')/100
        bnk_vnom = self.read_attrb('bnk_vo')
        if self.soc == 1:
            self.bnk_vo = bnk_vnom
        bnk_voc= self.bnk_vo * 1.15
        bnk_cap = self.read_attrb('bnk_cap')
        bnk_Idis = bnk_cap/ self.parts[0].read_attrb('b_rhrs')
        eff = battery_types[self.parts[0].read_attrb('b_typ')][1]
        if drain > 0:
            # Charging Battery State
            if self.soc < 1:
                if self.soc <= max_dod:
                    i_chg = 2 * bnk_Idis
                elif self.soc <= self._chg_break:
                    i_chg = (drain/bnk_voc) *(self.soc/self._chg_break)
                elif self.soc < 1.0:
                    i_chg = 6*((1-self.soc)*drain)/bnk_voc
        else:
            # Discharging Battery           
            if self.soc > max_dod:
                i_chg = drain/ self.bnk_vo
        new_soc = ((self.soc*bnk_cap) + i_chg)/bnk_cap
        self.update_cycle_counts(self.soc - new_soc)
        self.soc = new_soc
        try:
            self.bnk_vo = eff*((bnk_voc/6.22)*log(self.soc))+ bnk_vnom
        except:
            print ("Battery Bank: Computation Error ")
            print (('\tSOC: {0:f},\ti_chg: {1:f},\tCap: {2:f}'.
                    format(self.soc, i_chg, bnk_cap)))
            print (('\tSOC: {0:f},\teff: {1:f},\tVoc: {2:f},\tVnom: {3:f}'.
                    format(self.soc, eff, bnk_voc, bnk_vnom)))
        return self.soc

    def get_total_cycles(self):
        """ return the total number of charging cycles experienced by battery """
        return self.tot_cycles

    def check_arg_definition(self):
        """ Verify adequate battery definition """
        msg = ''
        if len(self.parts) == 0:
            msg = 'Bank component Battery is undefined'
            return False, msg
        bat = self.parts[0]
        flag, msg = bat.check_arg_definition()
        if flag:
            self.update_attributes()
            return True, msg
        else:
            return flag, msg

    def validate_size_setting(self):
        """ triggerd by change in UIS or SIP """
        uis =  float(self.form.wdg_dict['bnk_uis'].get_val())
        sip =  float(self.form.wdg_dict['bnk_sip'].get_val())
        self.set_attribute('bnk_tbats', uis * sip )
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
            if typ is not '':
                eff = battery_types[typ][1]
            gv = self.master.site.read_attrb('gv')
            if gv == 0.0 or gv == '':
                gv = 120.0
            ld = sum(self.master.load.get_load_profile()['Total'])
            return round((doa*ld)/(gv*doc*eff))
        
    def define_battery_drain(self, array_data, inverter_dict):
        """ Compute Hourly Battery Drain
            array_data = dataFrame of hourly performance data for the panel array
            inverter_dict = Dictionary of Inverter parameters from CEC inverter file
            returns a Dataframe of hourly battery drain estimates where:
                - sign implies power draw from battery
                + sign implies power add to battery
            """

        #TODO move estimate_required_dcpower to inverter class
        def estimate_required_dcPower(pac, paco, pdco, pnt):
            """ Estimates the amount of pdc required to drive the ac load 
                defined by pac
                   pac = required electrical load to be produced
                   paco = rated inverter ac power
                   pdco = rated inverter dc power
                   pnt = rated quiescent inverter power draw """
            rslt = None
            ie_ref = 0.9637
            if pac < paco:
                rslt =  pnt + pac*pdco/paco
            else:
                rslt = pnt + pdco
            return rslt/ie_ref

        bd = np.zeros(len(array_data))
        soc = np.zeros(len(array_data))
        pwr_out = np.zeros(len(array_data))
        bnk_pwr = np.zeros(len(array_data))
#        pac_load = array_data['Load']
        paco = inverter_dict['Paco']
        pdco = inverter_dict['Pdco']
        pnt = inverter_dict['Pnt']
        for indx in range(len(array_data)):
            pdc =estimate_required_dcPower(array_data['AC_Load'].iloc[indx], 
                                           paco, pdco, pnt)
            drain = (array_data['p_mp'].iloc[indx] - 
                    (pdc + array_data['DC_Load'].iloc[indx]))
            if (drain < 0 and self.is_okay())  or drain > 0:
                pwr_out[indx] = True
            else:
                pwr_out[indx] = False     
            bd[indx] = drain
            soc[indx] = self.update_soc(drain)*100
            bnk_pwr[indx] = soc[indx] * self.read_attrb('bnk_cap')/100
        self.bat_drain = pd.DataFrame({'Bat_Drain': bd, 'Bat_SOC': soc, 
                                  'Bat_PWR': bnk_pwr, 'Service': pwr_out}, 
                                 index= array_data.index)
        return self.bat_drain

    #TODO Improve method for selecting best day & worst day             
    def show_bank_drain(self):
        """ Create graphic of Battery Bank Drain Performance  """
        if self.bat_drain  is not None:
            xlabels = np.arange(24)
            pltslist = [
                {'label': 'Best Day Drain', 
                  'data': self.bat_drain ['Bat_Drain'].loc[pd.Timestamp(self.master.best_day[0]):pd.Timestamp(self.master.best_day[1])],
                  'type': 'Line', 'xaxis': xlabels, 
                  'width': 2.0, 'color': 'b'},
                {'label': 'Worst Day Drain', 
                  'data': self.bat_drain ['Bat_Drain'].loc[pd.Timestamp(self.master.worst_day[0]):pd.Timestamp(self.master.worst_day[1])],
                  'type': 'Line', 'xaxis': xlabels , 
                  'width': 2.0, 'color': 'r'}]
            dp = plot_graphic(self.master.rdw, 'Time of Day', 'Watts', xlabels, 
                                  pltslist, 'Range of Bank Drain', (6,4))

    #TODO Improve method for selecting best day & worst day     
    def show_bank_soc(self):
        """ Create graphic of Battery Bank SOC Performance  """
        if self.bat_drain  is not None:
            xlabels = np.arange(24)
            pltslist = [{'label': 'Best Day SOC', 
                         'data': self.bat_drain ['Bat_SOC'].loc[pd.Timestamp(self.master.best_day[0]):pd.Timestamp(self.master.best_day[1])],
                         'type': 'Line', 'xaxis': xlabels, 
                         'width': 2.0, 'color': 'b'},
                {'label': 'Worst Day SOC', 
                         'data': self.bat_drain ['Bat_SOC'].loc[pd.Timestamp(self.master.worst_day[0]):pd.Timestamp(self.master.worst_day[1])],
                         'type': 'Line', 'xaxis': xlabels , 
                         'width': 2.0, 'color': 'r'}]
            dp = plot_graphic(self.master.rdw, 'Time of Day', 'SOC', xlabels, 
                                  pltslist, 'Range of Bank SOC', (6,4))

    def create_overview(self):
        if self.bat_drain  is not None:
            suns = self.master.site.get_sun_times(self.master.times)
            sr_soc = np.zeros(len(suns))
            ss_soc = np.zeros(len(suns))
            day = [None]*len(suns)
            for i in range(len(suns)):
                snr = suns['Sunrise'].iloc[i]
                sns = suns['Sunset'].iloc[i]
                snrtm = create_time_mask(snr, 'Lead')
                snstm = create_time_mask(sns, 'Lag')
                day[i] = snrtm
                sr_soc[i] = self.bat_drain.loc[snrtm]['Bat_SOC']
                ss_soc[i] = self.bat_drain.loc[snstm]['Bat_SOC']
            bat_ovr = pd.DataFrame(data={'Sunrise':sr_soc, 'Sunset':ss_soc},
                                   index= day)        
            return bat_ovr
    
    def show_bank_overview(self):
        """ Create graphic of Battery Bank Overview Performance  """
        if self.bat_drain  is not None:
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