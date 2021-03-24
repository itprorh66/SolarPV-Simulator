#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 30 11:10:12 2018
Modified on 11/27/2018 to clean up comments
Modified on 02/22/2019 for version 0.1.0

@author: Bob Hentz
-------------------------------------------------------------------------------
  Name:        PVSite.py
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
import pandas as pd
import numpy as np
from guiFrames import ask_question, popup_notification
from PVUtilities import dfcell_is_empty, hourly_temp, hourly_speed
from Component import Component
from NasaData import getSiteElevation, LoadNasaData
from FormBuilder import DataForm
from FieldClasses import data_field, option_field
from pvlib.location import Location
#from pvlib.solarposition import get_sun_rise_set_transit
from pvlib.solarposition import sun_rise_set_transit_spa

from DataFrame import *

class PVSite(Component):
    """ Methods associated with the Site & Project definition, display, and operation """
    default_wind_spd = 0  # in meters per sec
    default_temp = 30     # in degrees celcius

    def __init__(self, master, **kargs):
        self.curloc = None
        self.air_temp = None
        self.wind_spd = None
        self.atmospherics = None
        self.suntimes = None
        Component.__init__(self, master, 'Site Definition', **kargs)
        self.print_order = ['proj', 'client', 'p_desc', 'city', 
                            'cntry', 'lat', 'lon', 'elev', 'tz',
                            'gv', 'gf']               
    def _define_attrbs(self):    
        self.args = {
                 'cntry':option_field('cntry', 'Country:    ', '', 
                                      sorted(self.master.countries.index.values), 
                                      self.master.countries),
                 'proj':data_field('proj', 'Project Name:', ''),
                 'p_desc':data_field('p_desc','Description:', ''),
                 'lat':data_field('lat', 'Latitude:', 0.0),
                 'lon':data_field('lon', 'Longitude:', 0.0),
                 'city':data_field('city', 'City:', ''),
                 'client':data_field('client', 'Client:', ''),
                 'elev':data_field('elev', 'Elevation (m):', 0.0),
                 'tz':data_field('tz', 'TimeZone:', 0),
                 'gv':data_field('gv', 'Grid Volts (VAC):  ', 0),
                 'gf':data_field('gf', 'Grid Freq (Hz):  ', 0),
#                 'grdcnx':option_field('Grid Connection', 'No',['Yes','No'],
#                                       ['Yes','No'])
                 }
                              

    def check_arg_definition(self):
        """ Check Site definition """      
        if self.read_attrb('lat') == 0.0:
            msg = 'Site Lat is undefined'
            return False, 'Site Latitude is undefined'
        if self.read_attrb('lon') == 0.0:
            return False, 'Site Longitude is undefined'
        if self.read_attrb('gv') == 0.0:
            return False, 'Site Grid Voltage is undefined'      
        if self.read_attrb('tz') == 0.0:
            return False, 'Time Zone is undefined'      
        return True, ''
 
    def get_location(self):
        """ Create & return a PVLIB Location Instance """
        if self.curloc is None:
            mtghgt = self.master.ary.read_attrb('mtg_hgt')
            self.curloc = Location(self.read_attrb('lat'), 
                            self.read_attrb('lon'), 
                            #Sets Valid TZ information for Location
                            tz= f"Etc/GMT{-self.read_attrb('tz'):+}", 
                            altitude= self.read_attrb('elev') + mtghgt, 
                            name= '{0}, {1}'.format(self.read_attrb('city'), 
                                   self.read_attrb('cntry')))
        return self.curloc
    
    def validate_country_setting(self):        
        """ Update Grid Voltage & Frequency based on valid country selection """
        val = self.form.wdg_dict['cntry'].get_val()
        osrc = self.args['cntry'].get_option_source()
        lst = list(filter(lambda x: x.startswith(val), osrc.index.values))
        if len(lst) == 0:
            return False        
        if len(lst) == 1 and val == lst[0]:
            self.set_attribute('cntry',val)
            self.form.wdg_dict['cntry'].set_val()
            gv = osrc[osrc.index.values == val]["Voltage"].values[0]
            gf = osrc[osrc.index.values == val]["Freq"].values[0]
            gav = osrc[osrc.index.values == val]["Alt-Volts"].values[0]
            gaf = osrc[osrc.index.values == val]["Alt-Freq"].values[0]
            if not dfcell_is_empty(gav):
                s = 'Two Grid Voltages {0} V or {1} V, Select {0} V?'.format(gv, gav)
                if not ask_question('Multiple Grid Voltages', s, parent= self.form ):
                    gv = gav
                    gf = gaf                                        
            self.set_attribute('gv',gv)
            self.set_attribute('gf',gf)
            self.form.wdg_dict['gv'].set_val()
            self.form.wdg_dict['gf'].set_val()
        return True

    def _Lentry_valid(self, val):
        """ Tests for valid Lat/Lon entries & not equal to 0.0 """
        try:
            x = float(val)
            if x != 0.0 and x <= 180.0 and x >= -180.0:
                return True
            return False
        except:
            return False

#TODO Implement retrieve elevation data functionality when focusin and elev cell is 0.0
    def retrieve_elevation(self, lat, lon):
        elvdat =  popup_notification(self.form, 
                        'Retrieving Elevation Data, Please wait', 
                        getSiteElevation, lat, lon)
        if elvdat[2] is not None:
            self.set_attribute('elev',elvdat[2])
            self.form.wdg_dict['elev'].set_val()
            self.set_attribute('tz',round(elvdat[0]/15.0,0))
            self.form.wdg_dict['tz'].set_val()
        
    def validate_lat_lon_setting(self):
        latval = self.form.wdg_dict['lat'].get_val()
        if latval == "":
            latval = 0.0
        lonval = self.form.wdg_dict['lon'].get_val()
        if lonval == '':
            lonval = 0.0
        elvval = self.form.wdg_dict['elev'].get_val()
        if elvval == '':
            elvval = 0.0
        if self.curloc is None and self._Lentry_valid(latval) and self._Lentry_valid(lonval):
           self.retrieve_elevation(latval, lonval)
        elif self.curloc is not None and self._Lentry_valid(latval) and self._Lentry_valid(lonval):
            if self.curloc[1] != latval or self.curloc[0] != lonval:
                self.retrieve_elevation(latval, lonval)
        return True                
            

    def display_input_form(self, parent_frame):
        self.parent_frame = parent_frame
        self.form = SiteForm(parent_frame, self, row=1, column=1,  width= 300, height= 300,
                      borderwidth= 5, relief= GROOVE, padx= 10, pady= 10, ipadx= 5, ipady= 5)
        return self.form

    def get_air_temp(self, times, stat_win):
        """ Get The site specific temperature estimates """
        if self.air_temp is None:
            self.get_atmospherics(times, stat_win)
        return self.air_temp 
    
    def get_wind_spd(self, times, stat_win):
        """ Get The site specific wind speed estimates """
        if self.wind_spd is None:
            self.get_atmospherics(times, stat_win)
        return self.wind_spd

    def get_sun_times(self, times):
        """ Create a DataFrame with SunRise & Sunset Times for each
            of the 365 days in a year   """           
        if self.suntimes is None:
            lt = self.read_attrb('lat')
            ln = self.read_attrb('lon')
            #st = get_sun_rise_set_transit(times, lt, ln)
            st = sun_rise_set_transit_spa(times, lt, ln)
            sunup = []
            sundwn = []
            transit = []
            doy = []
            for i in range(365):
                sunup.append(st.iloc[i*24]['sunrise'])
                sundwn.append(st.iloc[i*24]['sunset'])
                transit.append(st.iloc[i*24]['transit'])
                doy.append(times[i*24].date())
            df_dict = {'Sunrise': sunup,
                       'Sunset':sundwn,
                       'Transit':transit}
            self.suntimes = pd.DataFrame(data= df_dict, index= doy)
        return self.suntimes
        
    
    def get_atmospherics(self, times, stat_win):
        """ Using NASA meteorlogical data create wind & temp dataframes """
        self.air_temp = None
        self.wind_spd = None
        lt = self.read_attrb('lat')
        ln = self.read_attrb('lon')
        if self.atmospherics is None:
            self.atmospherics = popup_notification(stat_win, 
                        'Retrieving Atmospheric Data, Please Wait', 
                        LoadNasaData, lt,ln)
            if len(self.atmospherics) == 0:
                wm = 'Failed to load Atmospheric data, using fixed temp and wind speed'
                stat_win.show_message(wm, 'Warning')
                self.air_temp = PVSite.default_temp
                self.wind_spd = PVSite.default_wind_spd                
        if self.air_temp is None and self.wind_spd is None and self.atmospherics is not None:
            # Build Arrays of Temps & Wind Speed by Hour            
            temp =np.zeros([len(times)])
            speed = np.zeros(len(times))
            #sunlight = get_sun_rise_set_transit(times, lt, ln)
            sunlight = sun_rise_set_transit_spa(times, lt, ln)
            sunindx = list(sunlight.index.values)
            avt = self.atmospherics['T10M']['S-Mean'].values
            mxt = self.atmospherics['T10M_MAX']['S-Mean'].values
            mnt = self.atmospherics['T10M_MIN']['S-Mean'].values
            avw = self.atmospherics['WS10M']['S-Mean'].values
            mxw = self.atmospherics['WS10M_MAX']['S-Mean'].values
            mnw = self.atmospherics['WS10M_MIN']['S-Mean'].values
            for indx in range(len(sunindx)):
                doy = indx//24
                sunrise= sunlight.iloc[indx, 0]
                sunset =  sunlight.iloc[indx, 1]
                transit =  sunlight.iloc[indx, 2]
                current =  np.datetime_as_string(sunindx[indx])
                temp[indx] = hourly_temp(avt[indx//24], mxt[indx//24], 
                                       mnt[indx//24], current,
                                       sunrise, sunset, transit)
                speed[indx] = hourly_speed(avw[indx//24], mxw[indx//24], 
                                        mnw[indx//24], current, sunrise, 
                                        sunset, transit)
            self.air_temp = pd.DataFrame(data= temp, index= times, 
                                         columns=['Air_Temp'])
            self.wind_spd = pd.DataFrame(data= speed, index= times, 
                                     columns=['Wind_Spd'])




class SiteForm(DataForm):
    def __init__(self, parent_frame, data_src, **kargs):
        DataForm.__init__(self, parent_frame, data_src, **kargs)

    def define_layout(self):
        self.wdg_dict = {
                'blank1': self.create_space(40, row= 1, column= 0, sticky=(EW),
                                           columnspan= 10),               
                'lbl_proj':self.create_label(self.src.get_attrb('proj'),
                                            row= 2, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc21': self.create_space(2, row= 2, column= 1, sticky= (EW)),
                'proj': self.create_entry(self.src.get_attrb('proj'),
                                           row= 2, column= 2, sticky=(EW), 
                                           name= self.src.get_attrb_name('proj'),
                                           justify= CENTER, columnspan = 4),               
                'lbl_clnt': self.create_label(self.src.get_attrb('client'),
                                            row= 2, column= 7, justify= RIGHT ),
                'client': self.create_entry(self.src.get_attrb('client'),
                                           row= 2, column= 8, sticky=(EW), 
                                           justify= CENTER, columnspan= 3),               
                'spc22': self.create_space(10, row= 2, column= 12, sticky= (EW)),
                'spc23': self.create_space(10, row= 2, column= 13, sticky= (EW)),                
                'lbl_desc': self.create_label(self.src.get_attrb('p_desc'),
                                            row= 3, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc31': self.create_space(2, row= 3, column= 1, sticky= (EW)),
                'p_desc': self.create_entry(self.src.get_attrb('p_desc'),
                                           row= 3, column= 2, sticky=(EW), 
                                           justify= LEFT, columnspan= 10) ,              
                'blank2': self.create_space(40, row= 4, column= 0, sticky=(EW),
                                           columnspan= 10),               
                'lbl_city': self.create_label(self.src.get_attrb('city'),
                                            row= 5, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc51': self.create_space(2, row= 5, column= 1, sticky= (EW)),
                'city': self.create_entry(self.src.get_attrb('city'),
                                           row= 5, column= 2, sticky=(EW), 
                                           justify= CENTER, columnspan= 3) ,              
                'spc52': self.create_space(5, row= 5, column= 5, sticky= (EW)),
                'lbl_cntry': self.create_label(self.src.get_attrb('cntry'),
                                            row= 5, column= 7, justify= CENTER,
                                            sticky= (EW)),
                'cntry': self.create_dropdown(self.src.get_attrb('cntry'),
                                           row= 5, column= 8, sticky=(EW), 
                                           justify= CENTER, columnspan= 4,
                                           validate= 'focusout',
                                           validatecommand= self.src.validate_country_setting),                
                'blank3': self.create_space(40, row= 6, column= 0, sticky=(EW),
                                           columnspan= 10),        
                'lbl_lat': self.create_label(self.src.get_attrb('lat'),
                                            row= 8, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc81': self.create_space(2, row= 8, column= 2, sticky= (EW)),
                'lat': self.create_entry(self.src.get_attrb('lat'),
                                           row= 8, column= 3, sticky=(EW), 
                                           justify= CENTER, width=10,
                                           On_change= self.src.on_form_change,
                                           validate= 'focusout',
                                           validatecommand= self.src.validate_lat_lon_setting),
                'spc82': self.create_space(2, row= 8, column= 5, sticky= (EW)),
                'lbl_lon': self.create_label(self.src.get_attrb('lon'),
                                            row= 8, column= 5, justify= RIGHT,
                                            width= 10),
#                'spc83': self.create_space(2, row= 8, column= 6, sticky= (EW)),
                'lon': self.create_entry(self.src.get_attrb('lon'),
                                           row= 8, column= 7, sticky=(EW), 
                                           justify= CENTER, width=10,
                                           validate= 'focusout',
                                           validatecommand= self.src.validate_lat_lon_setting),               
                 'lbl_elev': self.create_label(self.src.get_attrb('elev'),
                                            row= 8, column= 11, justify= RIGHT),
                 'elev': self.create_entry(self.src.get_attrb('elev'),
                                           row= 8, column= 12, sticky=(EW), 
                                           justify= CENTER, width=10),               
                'lbl_tz': self.create_label(self.src.get_attrb('tz'),
                                            row= 9, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc91': self.create_space(2, row= 9, column= 2, sticky= (EW)),
                'tz': self.create_entry(self.src.get_attrb('tz'),
                                           row= 9, column= 3, sticky=(EW), 
                                           justify= CENTER, width=5,
                                           On_change= self.src.on_form_change),
                'spc92': self.create_space(2, row= 9, column= 5, sticky= (EW)),
                'lbl_gv': self.create_label(self.src.get_attrb('gv'),
                                            row= 9, column= 5, justify= RIGHT),
#                'spc93': self.create_space(2, row= 9, column= 6, sticky= (EW)),
                'gv': self.create_entry(self.src.get_attrb('gv'),
                                           row= 9, column= 7, sticky=(EW), 
                                           justify= CENTER, width=5),               
                 'lbl_gf': self.create_label(self.src.get_attrb('gf'),
                                            row= 9, column= 11, justify= RIGHT),
                 'gf': self.create_entry(self.src.get_attrb('gf'),
                                           row= 9, column= 12, sticky=(EW), 
                                           justify= CENTER, width=5),               
                  'blank4': self.create_space(40, row= 10, column= 0, sticky=(EW),
                                           columnspan= 10)               
                }

def main():
    print ('PVSite Definition Check')
    


if __name__ == '__main__':
    main()            
