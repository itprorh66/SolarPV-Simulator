#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  2 13:15:35 2018
Modified   Sat Dec  1 2018 (fix save/import issue)
Modified   Wed Dec  5 2018 (Fix Issue 2, Handle DC Loads)
Modified on 02/22/2019 for version 0.1.0
Modified on 04/11/2021 to address Issues #10, 12, & 13 related to improving 
            Site Load Definition performance and ease of use

@author: Bob Hentz

-------------------------------------------------------------------------------
  Name:        SiteLoad.py
  Purpose:     Provide Methods for Building and Maintaining the Site Energy
               Load Table as a Panda DataFrame

  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)

               This program is distributed WITHOUT ANY WARRANTY;
              without even the implied warranty of MERCHANTABILITY
              or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""
import numpy as np
import pandas as pd
import Parameters as sp
from DataFrame import DataFrame
import guiFrames as tbf

def findindex(val):
    """ If val is a Column Label return the column index
        else: return -1"""
    try:
        return sp.load_fields.index(val)
    except:
            return -1


class SiteLoad(DataFrame):
    """ A Panda DataFrame Structure containing the Site Energy Load
        Characteristics"""

    def __init__(self, master= None):
        self.master = master
        DataFrame.__init__(self,   sp.load_fields, sp.load_field_types)

    def addRow(self, typ, qty=None, uf=None, hrs=None, st=0, wts=None, 
               mde=None):
        """ Create a new entry in the load array from individual items """
        ar = [typ, qty, uf, hrs, st, wts, mde]
        self.add_new_row(ar)
        
    def getDefaultRowValues(self, load_type):
        """ Return the dictionary of default values for this type """
        return sp.load_types[load_type]
    
    def setStdRowValues(self, ar):
        """ Update AR based on change of Load Type """
        if ar[0] != '':
            key = ar[0]
            if key in sp.load_types.keys():
                od = sp.load_types[key]
                for sks in od.keys():
                    indx = self.get_col_indx(sks)
                    if indx > 0:
                        ar[indx] = od[sks]
        return ar

    def getTypeOptions(self):
        """ Return list of Load Type options """
        ret = list(sp.load_types.keys())
        ret.sort()
        return ret

    def get_daily_load(self):
        """ Return the total electrical load for a day """
        return sum(self.get_load_profile()['Total'])
    
    def get_demand_hours(self):
        elp = self.get_load_profile()
        return len(elp.loc[elp['Total'] > 0])
        
    def get_load_profile(self):
        """ Return a Dataframe of hourly usage by AC, DC and Total Power
            for the given load over a 24 hour period """
        ac_rslt = [0.0]*24
        dc_rslt = [0.0]*24
        tl_rslt = [0.0]*24
        for dfrw in range(self.get_row_count()):
            ac_mode = True
            ldvals = self.get_row_by_index(dfrw)
            if ldvals[sp.load_fields.index('Mode')] == 'DC':
                ac_mode = False            
            hr_wts = (ldvals[sp.load_fields.index('Qty')] *
                      ldvals[sp.load_fields.index('Use Factor')] *
                      ldvals[sp.load_fields.index('Watts')] )
            st = ldvals[sp.load_fields.index('Start Hour')]
            if type(st) is str or st is None:
                st = 0
            hpd = ldvals[sp.load_fields.index('Hours')]
            if type(hpd) is str or hpd is None:
                hpd = 24
            et = hpd + st
            for h in range(24):
                if et < 24:
                    if h >= st and h < et:
                        if ac_mode:
                            ac_rslt[h] += hr_wts
                        else:
                            dc_rslt[h] += hr_wts
                else:
                    if h >= st or h + 24 < et:
                        if ac_mode:
                            ac_rslt[h] += hr_wts
                        else:
                            dc_rslt[h] += hr_wts
        for i in range(24):
            tl_rslt[i] = ac_rslt[i] + dc_rslt[i]
        return pd.DataFrame({'AC': ac_rslt, 'DC': dc_rslt, 'Total':tl_rslt})

    def show_load_profile(self, window):
        """ Build & display the load profile graphic """
        elp = self.get_load_profile()
        dmd_hrs = len(elp.loc[elp['Total'] > 0])
        if dmd_hrs > 0:
            pls = 'Peak Hourly Load KW: Total= {0:4.2f},\tAC= {1:4.2f},\tDC= {2:4.2f}'
            pl = pls.format(max(elp['Total'])/1000, (max(elp['AC']))/1000, 
                            (max(elp['DC']))/1000)
            tdls = 'Daily Load KW:           Total= {0:4.2f},\tAC= {1:4.2f},\tDC= {2:4.2f}'
            tdl = tdls.format(sum(elp['Total'])/1000, sum(elp['AC'])/1000, 
                              sum(elp['DC'])/1000)
            avhs = 'Avg Hourly Load KW:  Total= {0:4.2f},\tAC= {1:4.2f},\tDC= {2:4.2f}'
            avhl = avhs.format(sum(elp['Total'])/(1000*dmd_hrs), 
                               sum(elp['AC'])/(1000*dmd_hrs), 
                               sum(elp['DC'])/(1000*dmd_hrs))
            pltlist = [{'label': 'Load', 'data': np.array(elp['Total']),
                            'type': 'Bar', 'color': 'grey', 'width': 0.4,
                            'xaxis':np.array([x for x in range(24)])}]
            tbf.plot_graphic(window, 'Hour of Day', 'Watts',
                                  np.array([x for x in range(24)]),
                        pltlist,'Hourly Electrical Use Profile', (6,4),
                        text_inserts= [pl,tdl,avhl])

    def report_error(self, msg, level, error_class):
        """ Generate Error Report """
        if self.master is None or self.master.stw is None:
            if error_class is None:
                print('{0} Error: {1}'.format(level, msg))
            else:
                raise error_class(msg)
        else:
            self.master.stw.show_message(msg, level)

    def check_arg_definition(self):
        """ Verify the load is defined """
        elp = self.get_load_profile()
        if sum(elp['Total']) == 0.0:
            return False, 'Electrical Load is unspecified'
        return True, ""

    def check_definition(self):
        """ Check Load Definition and if rslt is False
            Report in status window if identified else raise Error
            return rslt """
        rslt, msg = self.check_arg_definition()
        if not rslt:
            self.report_error(msg, "Fatal", AttributeError )
        return rslt

def main():
    sl = SiteLoad()
    sl.add_new_row(['Light, LED', 15, 0.30, "", "", 5.0, 'AC'])
    sl.add_new_row(['Light, LED', 8, 0.85, 2, 6, 5.0, 'AC'])
    sl.add_new_row(['Light, Halogen', 10, 0.95, 5, 18, 35.0, 'AC'])
    sl.add_new_row(['Well Pump DC, 1 HP', 1, 0.35, 12, 8, 500.0, 'DC'])
    sl.add_new_row(['Phone Charger', 10, 0.45, 12, 6, 2.0, 'DC'])
    elp = sl.get_load_profile()
    print(elp)
    print(sl.get_dataframe())


if __name__ == '__main__':
    main()
