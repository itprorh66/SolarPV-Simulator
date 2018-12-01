#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  2 13:15:35 2018
Modified   Sat Dec  1 2018 (fix save/import issue)

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
from DataFrame import *
import seaborn as sns
import matplotlib.pyplot as plt
import guiFrames as tbf

#TODO  Add back the AC/DC field to Siteload,
#TODO  update get_load_profile to create AC & DC hourly load profiles

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


    def addRow(self, typ, qty=None, uf=None, hrs=None, st=0, wts=None, src=None):
        """ Create a new entry in the load array from individual items """
        ar = [typ, qty, uf, hrs, st, wts, src]
        self.add_new_row(ar)


    def setStdRowValues(self, ar):
        """ Update AR based on change of Load Type """
        if ar[0] is not '':
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
        return sum(self.get_load_profile())

    def get_load_profile(self):
        """ Return an array of usage by hour for the given load
            over a typical 25 hour period """
        rslt = [0.0]*24
        for dfrw in range(self.get_row_count()):
            ldvals = self.get_row_by_index(dfrw)
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
                        rslt[h] += hr_wts
                else:
                    if h >= st or h + 24 < et:
                        rslt[h] += hr_wts
        return np.array(rslt)

    def show_load_profile(self, window):
        """ Build & display the load profile graphic """
        elp = self.get_load_profile()
        pl = 'Peak Hourly Load = {0:.2f} KW'.format(max(elp)/1000)
        tdl = 'Total Daily Load = {0:.2f} KW'.format(sum(elp)/1000)
        mp = 0
        ypos = max(elp)
        while ypos > 10:
            mp += 1
            ypos = ypos//10
        adj = 10**(mp-1)
        pltlist = [{'label': 'Load', 'data': np.array(elp),
                        'type': 'Bar', 'color': 'grey', 'width': 0.4,
                        'xaxis':np.array([x for x in range(24)])}]
        dp = tbf.plot_graphic(window, 'Hour of Day', 'Watts',
                              np.array([x for x in range(24)]),
                    pltlist,'Hourly Electrical Use Profile', (6,4),
                    text_inserts= ['Peak Hourly Load = {0:.2f} KW'.format(max(elp)/1000),
                                   'Total Daily Load = {0:.2f} KW'.format(sum(elp)/1000)])


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
        elp = self.get_load_profile()
        if sum(elp) == 0.0:
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
    alt_load_fields = ['Type', 'Qty', 'Use Factor','Hours', 'Start Hour', 'Watts', 'Mode']
    alt_load_field_types = [str, int, float, float, int, float, str]
    sl = SiteLoad(sp.load_fields, sp.load_field_types)
    sl2 = SiteLoad(alt_load_fields, alt_load_field_types)
    sl.add_new_row(['Light, LED', 15, 1.0, "", "", 5.0])
#    sl.add_new_row(['Light, LED', 8, 0.85, 2, 6, 5.0])
#    sl2.add_new_row(['Light, Halogen', 10, 0.95, 5, 18, 35.0])
#    sl.add_new_row(['Computer, Desktop', 10, 0.95, 12, 8, 175.0])
    sl.add_new_row(['Phone Charger', 10, 0.45, 12, 6, 2.0])
#    sl.add_new_row(['Refrigerator', 2, 0.25, 24, 0 , 200.0])
#    sl2.add_new_row(['TV', 3, 0.9, 5, 16, 100.0])
#    sl.add_new_row(['Well Pump', 1, 0.3, 24, 0, 300.0])
#    sl.add_new_row(['Stereo', 2, 0.25, 6, 14, 35.0])
#    elp = sl.get_load_profile()
#    print (elp, sl.get_daily_load())
#        ld = pd.DataFrame(elp, columns=['Load'])
#        ld.plot( kind= 'Bar', title= 'Watts per Daily Hour', legend= False)
#        plt.show

    print(sl.get_dataframe())
    exDf = sl.export_frame()
    sl2.import_frame(exDf)
    print()
    print(sl2.get_dataframe())


if __name__ == '__main__':
    main()
