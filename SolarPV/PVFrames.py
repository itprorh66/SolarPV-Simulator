#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 21 13:28:32 2018
Modified on 02/22/2019 for version 0.1.0


@author: Bob Hentz

-------------------------------------------------------------------------------
  Name:        PVFrames.py
  Purpose:     Provide the interactive forms to implement the data entry needed
               for definition of Project, Electric Load, Battery, Panel, &
               Inverter characteristics

  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)

              This program is distributed WITHOUT ANY WARRANTY;
              without even the implied warranty of MERCHANTABILITY
              or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""

from tkinter import *
import tkinter.ttk as ttk
from ModelData import *
import guiFrames as tbf
import PVUtilities as pvu
from NasaData import getSiteElevation


class sitedata(tbf.data_entry_frame):
    """ Creates the Site data input Form """
    def __init__(self, parent_frame, data_src, location = None, show_actions = None):
        tbf.data_entry_frame.__init__(self, parent_frame, data_src, location, show_actions)

    def make_frames(self):
        """ Generates frames for Site Data record display """
        self.frame_dict['proj'] = tbf.entry_form_frame(self.parent,
                       self.src['proj'],'Data Entry',
                       location= [0,0], size= 25, colspan= 2)
        self.frame_dict['client'] = tbf.entry_form_frame(self.parent,
                       self.src['client'],'Data Entry',
                       location= [0,2], size= 25, colspan= 2)
        self.frame_dict['p_desc'] = tbf.entry_form_frame(self.parent,
                       self.src['p_desc'], 'Note Entry',
                       location= [1,0], size= [2, 70], colspan= 4)
        self.frame_dict['city'] = tbf.entry_form_frame(self.parent,
                       self.src['city'],'Data Entry',
                       location= [2,0], size= 25, colspan= 2)
        self.frame_dict['cntry'] = tbf.entry_form_frame(self.parent,
                       self.src['cntry'], 'List Entry',
                       location= [2,2], size= 25, colspan= 2,
                       validate_command= self.on_cntry_set)
        self.frame_dict['lat'] = tbf.entry_form_frame(self.parent,
                       self.src['lat'],'Data Entry',
                       validate_command= self.lat_validate,
                       location= [3,0], size= 10, colspan= 2)
        self.frame_dict['lon'] = tbf.entry_form_frame(self.parent,
                       self.src['lon'], 'Data Entry',
                       validate_command= self.lon_validate,
                       location= [3,2], size= 10, colspan= 2                       )
        self.frame_dict['elev'] = tbf.entry_form_frame(self.parent,
                       self.src['elev'],'Data Entry',
                       location= [4,0], size= 10)
        self.frame_dict['tz'] = tbf.entry_form_frame(self.parent,
                       self.src['tz'],'Data Entry',
                       location= [4,2], size= 10)
        self.frame_dict['gv'] = tbf.entry_form_frame(self.parent,
                       self.src['gv'],'Data Entry',
                       location= [5,0], size= 10)
        self.frame_dict['gf'] = tbf.entry_form_frame(self.parent,
                       self.src['gf'],'Data Entry',
                       location= [5,2], size= 10)

    def on_cntry_set(self, val):
        """ Triggered by a Validation Event """
        self.src['cntry'].write_data(val)
        lst = self.src['cntry'].get_list()
        if len(lst) == 1 and val == lst[0]:
            cval = self.src['cntry'].read_data()
            df = self.src['cntry'].get_option_source()
            gv = df[df.index.values == cval]["Voltage"].values[0]
            gf = df[df.index.values == cval]["Freq"].values[0]
            gav = df[df.index.values == cval]["Alt-Volts"].values[0]
            gaf = df[df.index.values == cval]["Alt-Freq"].values[0]
            if pvu.dfcell_is_empty(gav):
                self.src['gv'].write_data(gv)
                self.src['gf'].write_data(gf)
            else:
                s = 'Two Grid Voltages {0} V or {1} V, Select {0} V?'.format(gv, gav)
                if tbf.ask_question('Multiple Grid Voltages', s ):
                    self.src['gv'].write_data(gv)
                    self.src['gf'].write_data(gf)
                else:
                    self.src['gv'].write_data(gav)
                    self.src['gf'].write_data(gaf)
            #self.make_frames()
            self.frame_dict['gv'].make_frame()
            self.frame_dict['gf'].make_frame()
            return True
        else:
            # reset gv & gf
            self.src['gv'].write_data(0)
            self.src['gf'].write_data(0)
            self.frame_dict['gv'].make_frame()
            self.frame_dict['gf'].make_frame()
            return False

    def _Lentry_valid(self, val):
        """ Tests for valid Lat/Lon entries & not equal to 0.0 """
        if val != 0.0 and val <= 180.0 and val >= -180.0:
            return True
        return False

    def lat_validate(self, val):
        lat = float(val)
        lon = self.src['lon'].read_data()
        if self._Lentry_valid(lat) and self._Lentry_valid(lon):
            self.on_lat_lon_set(lat, lon)
            return True
        return False


    def lon_validate(self, val):
        lon = float(val)
        lat = self.src['lat'].read_data()
        if self._Lentry_valid(lon) and self._Lentry_valid(lat):
            self.on_lat_lon_set(lat, lon)
            return True
        return False


    def on_lat_lon_set(self, lat, lon):
        """ Update Elevation When Latitude & Longitude have Changed """
        curloc = self.src['curloc']
        if (curloc[0] is None and
            curloc[1] is None) or (lat != curloc[1] or
                     lon != curloc[0]):
#            elvdat = getSiteElevation(lat, lon)
            elvdat = tbf.popup_notification(self.parent, 
                        'Retrieving Elevation Data, Please wait', 
                        getSiteElevation, lat, lon)
            if elvdat[2] is not None:
                self.src['curloc']= elvdat
                self.src['elev'].write_data(elvdat[2])
                self.src['tz'].write_data(round(elvdat[0]/15.0,0))
                self.frame_dict['elev'].make_frame()
                self.frame_dict['tz'].make_frame()

class batdata(tbf.data_entry_frame):
    """ Creates the Battery data input Form """
    def __init__(self, parent_frame, data_src, location = None, show_actions = None):
        tbf.data_entry_frame.__init__(self, parent_frame, data_src, location, show_actions)
    def make_frames(self):
        """ Generates frames for record display """
        self.frame_dict['b_mfg'] = tbf.entry_form_frame(self.parent,
                       self.src['b_mfg'],'Data Entry',
                       location= [1,0], size= 25)
        self.frame_dict['b_mdl'] = tbf.entry_form_frame(self.parent,
                       self.src['b_mdl'],'Data Entry',
                       location= [1,1], size= 25)
        self.frame_dict['b_typ'] = tbf.entry_form_frame(self.parent,
                       self.src['b_typ'],'List Entry',
                       validate_command= self.on_type_validate,
                       location= [1,2], size= 5)
        self.frame_dict['b_desc'] = tbf.entry_form_frame(self.parent,
                       self.src['b_desc'], 'Data Entry',
                       location= [2,0], size= 50, colspan= 3)
        self.frame_dict['nomv'] = tbf.entry_form_frame(self.parent,
                       self.src['nomv'], 'Data Entry',
                       location= [3,0], size= 8)
        self.frame_dict['ir'] = tbf.entry_form_frame(self.parent,
                       self.src['ir'],'Data Entry',
                       location= [3,2], size= 10)
        self.frame_dict['rcap'] = tbf.entry_form_frame(self.parent,
                       self.src['rcap'],'Data Entry',
                       location= [4,0], size= 8)
        self.frame_dict['rhrs'] = tbf.entry_form_frame(self.parent,
                       self.src['rhrs'],'Data Entry',
                       location= [4,2], size= 8)        
        self.frame_dict['stdTemp'] = tbf.entry_form_frame(self.parent,
                       self.src['stdTemp'],'Data Entry',
                       location= [5,0], size= 8)
        self.frame_dict['tmpc'] = tbf.entry_form_frame(self.parent,
                       self.src['tmpc'],'Data Entry',
                       location= [5,2], size= 8)
#        ttk.Label(self, padding='2 2 2 2', text="        ").grid(column=0, row=6, sticky=(W, E))
        self.frame_dict['doa'] = tbf.entry_form_frame(self.parent,
                       self.src['doa'],'Data Entry',
                       location= [7,0], size= 5)
        self.frame_dict['doc'] = tbf.entry_form_frame(self.parent,
                       self.src['doc'],'Data Entry',
                       location= [7,2], size= 5)
        self.frame_dict['b_uis'] = tbf.entry_form_frame(self.parent,
                       self.src['b_uis'],'Data Entry',
                       validate_command= self.on_bank_size_update,
                       location= [8,0], size= 10)
        self.frame_dict['b_sip'] = tbf.entry_form_frame(self.parent,
                       self.src['b_sip'],'Data Entry',
                       validate_command= self.on_bank_size_update,
                       location= [8,1], size= 10)
        self.frame_dict['bnk_tbats'] = tbf.entry_form_frame(self.parent,
                       self.src['bnk_tbats'],'Data Entry',
                       location= [8,2], size= 10)
        self.frame_dict['bnk_vo'] = tbf.entry_form_frame(self.parent,
                       self.src['bnk_vo'],'Data Entry',
                       location= [9,0], size= 10)
        self.frame_dict['bnk_cap'] = tbf.entry_form_frame(self.parent,
                       self.src['bnk_cap'],'Data Entry',
                       location= [9,2], size= 10)       
    
    def on_bank_size_update(self, val):
        self.update_bank_data()
        self.make_frames()
        return True
          
    def on_type_validate(self, val):
        """ Triggered by change to type selection """
        self.src['b_typ'].write_data(val)
        src = self.src['b_typ'].get_option_source()
        if val in src:
            return True
        else:
            self.src['b_typ'].update_list(list(src))
            return True
        
    def update_bank_data(self):
        """ compute bank operational data """
        uis = self.src['b_uis'].read_data()
        sip = self.src['b_sip'].read_data()
        nmv = self.src['nomv'].read_data()
        bcap = self.src['rcap'].read_data()
        totbats = uis*sip
        self.src['bnk_tbats'].write_data(totbats)
        self.src['bnk_cap'].write_data(round(sip*bcap,2))
        self.src['bnk_vo'].write_data(round(uis*nmv,2))

    def on_local_frame_close(self):
        """ perform automated calculatioins on frame closure """
        if self.src['nomv'].read_data() != 0.0:
            self.update_bank_data()

        
class cntrldata(tbf.data_entry_frame):
    """ Creates the Solar Panel data input Form """
    def __init__(self, parent_frame, data_src, location = None, show_actions = None):
        tbf.data_entry_frame.__init__(self, parent_frame, data_src, location, show_actions)

    def make_frames(self):
        self.frame_dict['c_mfg'] = tbf.entry_form_frame(self.parent,
                       self.src['c_mfg'],'Data Entry',
                       location= [1,0], size= 25, colspan= 2)
        self.frame_dict['c_mdl'] = tbf.entry_form_frame(self.parent,
                       self.src['c_mdl'],'Data Entry',
                       location= [2,0], size= 25, colspan= 2)
        self.frame_dict['mxv'] = tbf.entry_form_frame(self.parent,
                       self.src['mxv'],'Data Entry',
                       location= [3,0], size= 8)
        self.frame_dict['isc'] = tbf.entry_form_frame(self.parent,
                       self.src['isc'],'Data Entry',
                       location= [3,1], size= 8)
        self.frame_dict['bvnom'] = tbf.entry_form_frame(self.parent,
                       self.src['bvnom'],'Data Entry',
                       location= [4,0], size= 8)
        self.frame_dict['c_mxPow'] = tbf.entry_form_frame(self.parent,
                       self.src['c_mxPow'],'Data Entry',
                       location= [4,1], size= 8)
        self.frame_dict['c_stdbyPow'] = tbf.entry_form_frame(self.parent,
                       self.src['c_stdbyPow'],'Data Entry',
                       location= [5,0], size= 8)
        self.frame_dict['c_eff'] = tbf.entry_form_frame(self.parent,
                       self.src['c_eff'],'Data Entry',
                       location= [5,1], size= 8)
      
class moddata(tbf.data_entry_frame):
    """ Creates the Solar Panel data input Form """
    def __init__(self, parent_frame, data_src, location = None, show_actions = None):
        tbf.data_entry_frame.__init__(self, parent_frame, data_src, location, show_actions)

    def make_frames(self):
        
        self.frame_dict['tilt'] = tbf.entry_form_frame(self.parent,
                       self.src['tilt'],'Data Entry',
                       location= [0,0], size= 10)
        self.frame_dict['azimuth'] = tbf.entry_form_frame(self.parent,
                       self.src['azimuth'],'Data Entry',
                       location= [0,1], size= 10)
        self.frame_dict['albedo'] = tbf.entry_form_frame(self.parent,
                       self.src['albedo'], 'List Entry',
                       validate_command= self.on_albedo_set,
                       location= [0,2], size = 20) 
        self.frame_dict['Mtg'] = tbf.entry_form_frame(self.parent,
                       self.src['Mtg'],'List Entry',
                       location= [1,0], size= 20)
        self.frame_dict['UIS'] = tbf.entry_form_frame(self.parent,
                       self.src['UIS'],'Data Entry',
                       location= [1,1], size= 5)
        self.frame_dict['SIP'] = tbf.entry_form_frame(self.parent,
                       self.src['SIP'],'Data Entry',
                       location= [1,2], size= 5)
        
        self.frame_dict['m_mfg'] = tbf.entry_form_frame(self.parent,
                       self.src['m_mfg'],'List Entry',
                       validate_command= self.on_mfg_set,
                       location= [4,0], size= 50)
        
        self.frame_dict['m_mdl'] = tbf.entry_form_frame(self.parent,
                       self.src['m_mdl'],'List Entry',
                       validate_command= self.on_mdl_set,
                       location= [4,1], size= 50)
    
        self.frame_dict['Name'] = tbf.entry_form_frame(self.parent,
                       self.src['Name'], 'Data Entry',
                       location= [5,0], size= 80, colspan = 3)
    
        self.frame_dict['Technology'] = tbf.entry_form_frame(self.parent,
                       self.src['Technology'],'Data Entry',
                       location= [6,0], size= 20)
        self.frame_dict['A_c'] = tbf.entry_form_frame(self.parent,
                       self.src['A_c'],'Data Entry',
                       location= [6,1], size= 5)
        self.frame_dict['N_s'] = tbf.entry_form_frame(self.parent,
                       self.src['N_s'],'Data Entry',
                       location= [6,2], size= 5)
    
        self.frame_dict['T_NOCT'] = tbf.entry_form_frame(self.parent,
                       self.src['T_NOCT'],'Data Entry',
                       location= [7,0], size= 10)
        self.frame_dict['V_mp_ref'] = tbf.entry_form_frame(self.parent,
                       self.src['V_mp_ref'],'Data Entry',
                       location= [7,1], size= 10)
        self.frame_dict['I_mp_ref'] = tbf.entry_form_frame(self.parent,
                       self.src['I_mp_ref'],'Data Entry',
                       location= [7,2], size= 10)
    
        self.frame_dict['V_oc_ref'] = tbf.entry_form_frame(self.parent,
                       self.src['V_oc_ref'],'Data Entry',
                       location= [8,0], size= 10)
        self.frame_dict['I_sc_ref'] = tbf.entry_form_frame(self.parent,
                       self.src['I_sc_ref'],'Data Entry',
                       location= [8,1], size= 10)
     
        ttk.Frame(self, padding= '0.8i').grid(row = 9, column= 0, sticky= (E, W)) 
        
            
    def on_mfg_set(self, val):
        """ Triggered by a Manufacturer Validation Event """
        self.src['m_mfg'].write_data(val)
        lst = self.src['m_mfg'].get_list()
        osrc = self.src['m_mdl'].get_option_source()
        mdf = osrc[osrc['Manufacturer'].isin(lst)]
        nol = sorted(list(set(mdf['Model'])))
        self.src['m_mdl'].update_list(nol)
        self.frame_dict['m_mdl'].make_frame()
        return True
        
    def on_mdl_set(self, val):
        """ Triggered by a Model Validation Event """
        self.src['m_mdl'].write_data(val)
        lst = self.src['m_mdl'].get_list()
        osrc = self.src['m_mdl'].get_option_source()
        mdf = osrc[osrc['Manufacturer'].isin([self.src['m_mfg'].read_data()]) & osrc['Model'].isin(lst)]            
        if len(mdf) == 1:
            self.src['Name'].write_data(mdf.index.values[0])
            self.frame_dict['Name'].make_frame() 
            self.src['Selected_Module'] = mdf
            for ky in self.frame_dict.keys():
                if ky in mdf.columns:
                    self.src[ky].write_data(mdf[ky].values[0])
                    self.frame_dict[ky].make_frame()                    
        if len(mdf) > 1 and self.src['Selected_Module'] is not None:
            self.src['Selected_Module'] = None
            for ky in self.frame_dict.keys():
                if ky in mdf.columns:
                    self.src[ky].reset_value()
                    self.frame_dict[ky].make_frame()                                    
            return False
        return True 


    def on_albedo_set(self, val):
        self.src['albedo'].write_data(val)
        self.src['albedo'].update_list(list(filter(lambda x: x.startswith(val), 
                       list(self.src['albedo'].get_option_source()))))
        sd = self.src['albedo'].get_option_source()
        if val in sd:
            self.src['alb_fac'].write_data(sd[val])
            self.frame_dict['albedo'].make_frame()
            return True
        else:
            self.src['albedo'].update_list(list(filter(lambda x: x.startswith(val), list(sd))))
            self.src['alb_fac'].write_data(0.0)
            self.frame_dict['albedo'].make_frame()
            return True
            
    def on_albedo_change(self, val):
        pass
        
class invdata(tbf.data_entry_frame):
    """ Creates the Solar Panel data input Form """
    def __init__(self, parent_frame, data_src, location = None, show_actions = None):
        
        tbf.data_entry_frame.__init__(self, parent_frame, data_src, location, show_actions)
        
    def make_frames(self):
                     
        self.frame_dict['i_mfg'] = tbf.entry_form_frame(self.parent,
                       self.src['i_mfg'],'List Entry',
                       validate_command= self.on_mfg_set,
                       location= [0,0], size= 50)
        self.frame_dict['i_mdl'] = tbf.entry_form_frame(self.parent,
                       self.src['i_mdl'],'List Entry',
                       validate_command= self.on_mdl_set,
                       location= [0,1], size= 50)
    
        self.frame_dict['Name'] = tbf.entry_form_frame(self.parent,
                       self.src['Name'], 'Data Entry',
                       location= [2,0], size= 80, colspan = 3)
    
        self.frame_dict['Vac'] = tbf.entry_form_frame(self.parent,
                       self.src['Vac'],'Data Entry',
                       location= [3,0], size= 10)
        self.frame_dict['Paco'] = tbf.entry_form_frame(self.parent,
                       self.src['Paco'],'Data Entry',
                       location= [3,1], size= 10)

        self.frame_dict['Vdco'] = tbf.entry_form_frame(self.parent,
                       self.src['Vdco'],'Data Entry',
                       location= [4,0], size= 10)
        self.frame_dict['Pdco'] = tbf.entry_form_frame(self.parent,
                       self.src['Pdco'],'Data Entry',
                       location= [4,1], size= 10)
   
        self.frame_dict['Vdcmax'] = tbf.entry_form_frame(self.parent,
                       self.src['Vdcmax'],'Data Entry',
                       location= [5,0], size= 10)
        self.frame_dict['Idcmax'] = tbf.entry_form_frame(self.parent,
                       self.src['Idcmax'],'Data Entry',
                       location= [5,1], size= 10)
             
        self.frame_dict['Mppt_low'] = tbf.entry_form_frame(self.parent,
                       self.src['Mppt_low'],'Data Entry',
                       location= [6,0], size= 10)
        self.frame_dict['Mppt_high'] = tbf.entry_form_frame(self.parent,
                       self.src['Mppt_high'],'Data Entry',
                       location= [6,1], size= 10)
          
    def on_mfg_set(self, val):
        """ Triggered by a Manufacturer Validation Event """
        self.src['i_mfg'].write_data(val)
        lst = self.src['i_mfg'].get_list()
        osrc = self.src['i_mdl'].get_option_source()
        mdf = osrc[osrc['Manufacturer'].isin(lst)]
        nol = sorted(list(set(mdf['Model'])))
        self.src['i_mdl'].update_list(nol)
        self.frame_dict['i_mdl'].make_frame()
        return True
        
    def on_mdl_set(self, val):
        """ Triggered by a Model Validation Event """
        print('Inverter Model set', val)
        self.src['i_mdl'].write_data(val)
        osrc = self.src['i_mdl'].get_option_source()
        i_mfg = self.src['i_mfg'].read_data()
        i_mdl = self.src['i_mdl'].read_data()
        print ('Selecting;', i_mfg, i_mdl)
        mfg = osrc['Manufacturer']  == self.src['i_mfg'].read_data()
        mdl = osrc['Model']  == self.src['i_mdl'].read_data()
        mdf = osrc[mfg & mdl]
        print(len(mdf))
        if len(mdf) == 1:
            print('Inverter mdf = 1\n', mdf.head())
            self.src['Name'].write_data(mdf.index.values[0])
            self.frame_dict['Name'].make_frame() 
            self.src['Selected_Inverter'] = mdf
            for ky in self.frame_dict.keys():
                if ky in mdf.columns:
                    self.src[ky].write_data(mdf[ky].values[0])
                    self.frame_dict[ky].make_frame()                    
        if len(mdf) > 1 and self.src['Selected_Inverter'] is not None:
            print ('Inverter mdf > 1\n', mdf.head())
            self.src['Selected_Inverter'] = None
            for ky in self.frame_dict.keys():
                if ky in mdf.columns:
                    self.src[ky].reset_value()
                    self.frame_dict[ky].make_frame()                                    
            return True
        return False    
       

def main():
    pass


if __name__ == '__main__':
    main()