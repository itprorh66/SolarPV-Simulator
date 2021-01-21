#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 12:57:18 2018
Modified on 02/22/2019 - for version 0.1.0
modified on 1/8/2021 - to adapt to pvlib 0.8 requirements for cell 
                        temperature model definition

@author: Bob Hentz

-------------------------------------------------------------------------------
  Name:        PVPanel.py
  Purpose:     Provides for the methods & data structures associated with
               Implementing the Solar Panel for a Solar PV System

  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)

               This program is distributed WITHOUT ANY WARRANTY;
               without even the implied warranty of MERCHANTABILITY
               or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""
from tkinter import GROOVE, EW, CENTER, RIGHT
from FormBuilder import DataForm
from Component import Component
from FieldClasses import data_field, option_field
from Parameters import panel_racking, albedo_types, panel_types, temp_model_xlate

#from pvlib import *
from pvlib.pvsystem import PVSystem
#from pvlib.solarposition import spa_python
#from pvlib.irradiance import aoi, get_total_irradiance
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS 

class PVArray(Component):
    """ Methods associated with the definition, display, and operation of a
        Solar Panel Array """
    def __init__(self, master, **kargs):
        Component.__init__(self, master, 'PV Array', **kargs)

              
    def _define_attrbs(self):
        self.args = {
                'tilt': data_field('tilt', 'Tilt Angle (Degrees):', 0.0),
                'azimuth': data_field('azimuth', 'Azimuth (Degrees):', 0.0),
                'mtg_cnfg': option_field('mtg_cnfg', 'Mounting Configuration:', '',
                                                panel_racking, panel_racking),
                'mtg_spc': data_field('mtg_spc', 'Space under Panel (cm):', 0.0),
                'mtg_hgt': data_field('mtg_hgt', 'Mounting Height (m):', 0.0),
                'gnd_cnd': option_field('gnd_cnd', 'Ground Surface Condition:', '',
                                                   list(albedo_types), albedo_types),
                'albedo': data_field('albedo', 'Albedo:', 0.0),
                'uis': data_field('uis', 'Units in Series:', 1),
                'sip': data_field('sip', 'Strings in Parallel:', 1),
                'ary_Vmp': data_field('ary_Vmp', 'Array Vmp:', 0.0),
                'ary_Imp': data_field('ary_Imp', 'Array Imp:', 0.0),
                'ary_tpnl': data_field('ary_tpnl', 'Total Panels:', 1), 
                }
        
        
    def check_arg_definition(self):
        """ Check Array definition """
        msg = ''
        bf, bmsg = self.parts[0].check_arg_definition()
        if not bf:
            return bf, bmsg
        if ((self.read_attrb('tilt') == 0.0 and
            self.read_attrb('azimuth')  == 0.0) or
            self.read_attrb('mtg_cnfg') == "" or
            self.read_attrb('gnd_cnd') == "" or
            self.read_attrb('ary_Vmp') == 0.0):           
            msg = 'Array Specification incomplete or undefined'
            return False, msg 
        return True, msg
  

    def validate_gnd_cnd_setting(self):        
        """ Triggered by a gnd_cnf field validation event
            Updates albedo based on selection """
        val = self.form.wdg_dict['gnd_cnd'].get_val()
        if val in albedo_types:
            self.set_attribute('albedo', albedo_types[val])
            self.form.wdg_dict['albedo'].set_val()
            return True
        return False

    def validate_size_setting(self):
        """ triggerd by change in UIS or SIP """
        uis =  float(self.form.wdg_dict['uis'].get_val())
        sip =  float(self.form.wdg_dict['sip'].get_val())
        self.set_attribute('ary_tpnl', uis * sip )
        self.form.wdg_dict['ary_tpnl'].set_val()
        if len(self.parts) > 0:
            pnl = self.parts[0]
            pvm = pnl.read_attrb('V_mp_ref')
            pim = pnl.read_attrb('I_mp_ref')
            self.set_attribute('ary_Vmp', uis * pvm )
            self.set_attribute('ary_Imp', sip * pim )
            self.form.wdg_dict['ary_Vmp'].set_val()
            self.form.wdg_dict['ary_Imp'].set_val()
        return True

    def display_input_form(self, parent_frame):
        """ Generate the data input form """
        self.parent_frame = parent_frame
        if len(self.parts) > 0:
            pnl = self.parts[0]
            pvm = pnl.read_attrb('V_mp_ref')
            pim = pnl.read_attrb('I_mp_ref')
            self.set_attribute('ary_Vmp', self.read_attrb('uis') * pvm )
            self.set_attribute('ary_Imp', self.read_attrb('sip') * pim )
        self.form = ArrayForm(parent_frame, self, row=1, column=1,  width= 300, height= 300,
                      borderwidth= 5, relief= GROOVE, padx= 10, pady= 10, ipadx= 5, ipady= 5)
        return self.form

    def define_array_performance(self, times, cur_site, cur_inv, stat_win):
        inv_name = None
        inv_parameters = None
        if cur_inv is not None:
            inv_name = cur_inv.read_attrb('Name')
            inv_parameters = cur_inv.get_parameters()
        surf_tilt = self.read_attrb('tilt')
        surf_azm = self.read_attrb('azimuth')
        surf_alb = self.read_attrb('albedo')
        mdl_series = self.read_attrb('uis')
        mdl_sip = self.read_attrb('sip')
        loc = cur_site.get_location()
        mdl_rack_config =self.read_attrb('mtg_cnfg')
        pnl_name = self.parts[0].read_attrb('Name')
        pnl_parms = self.parts[0].get_parameters()
        temp_model = temp_model_xlate[mdl_rack_config][0]
        temp_type = temp_model_xlate[mdl_rack_config][1]
        temp_parms = TEMPERATURE_MODEL_PARAMETERS[temp_model][temp_type]
        air_temp = cur_site.get_air_temp(times, stat_win)['Air_Temp']
        wnd_spd = cur_site.get_wind_spd(times, stat_win)['Wind_Spd']
        pvsys = PVSystem(surf_tilt, surf_azm, surf_alb,
                         module= pnl_name, module_parameters= pnl_parms,
                         temperature_model_parameters = temp_parms,
                         modules_per_string= mdl_series, 
                         strings_per_inverter= mdl_sip,
                         inverter= inv_name,
                         inverter_parameters= inv_parameters,
                         racking_model= mdl_rack_config,
                         name= loc.name)
        """Define 'apparent_elevation', 'apparent_zenith', 'azimuth',  
           'elevation', 'equation_of_time', and 'zenith'   """
        solpos = loc.get_solarposition(times, pressure= None, temperature= air_temp)
        
        """Define 'airmass_relative'  & 'airmass_absolute' """       
        airmass = loc.get_airmass(times, solar_position=solpos, model='kastenyoung1989')

        """ Compute ghi, dni, & dhi """
        csky= loc.get_clearsky(times, model='ineichen')
        """ Compute 'aoi' """
        aoi = pvsys.get_aoi(solpos['zenith'], solpos['azimuth'])
         
        
        """ Compute 'poa_global',  'poa_direct',  'poa_diffuse',
            'poa_sky_diffuse', & 'poa_ground_diffuse' """
        total_irrad = pvsys.get_irradiance(solpos['zenith'], solpos['azimuth'], 
                                           csky['dni'], csky['ghi'], csky['dhi'],
                                           dni_extra=None, airmass=airmass, 
                                           model='haydavies')        
        
        """ Compute 'temp_cell' & 'temp_module'  """
        temps = pvsys.sapm_celltemp(total_irrad['poa_global'], air_temp, wnd_spd)
        vars_dict = panel_types[self.parts[0].read_attrb('Technology')]
        egrf = vars_dict.pop('EgRef', 1.121)
        dgdt = vars_dict.pop('dEgdT', -0.0002677)
        
        photocurrent, saturation_current, resistance_series, resistance_shunt, nNsVth = (
            pvsys.calcparams_desoto(total_irrad['poa_global'],
                                             temp_cell= pnl_parms['T_NOCT']))
                 
        """ Compute Total Array  'i_sc',  'v_oc',  'i_mp',  'v_mp',
            'p_mp',  'i_x', &  'i_xx' """
        array_out = pvsys.scale_voltage_current_power( pvsys.singlediode(photocurrent, 
                                             saturation_current, 
                                             resistance_series, 
                                             resistance_shunt, nNsVth))
        array_out.index.name = 'Time'
        return array_out

class ArrayForm(DataForm):
    def __init__(self, parent_frame, data_src, **kargs):
        DataForm.__init__(self, parent_frame, data_src, **kargs)

    def define_layout(self):
        self.wdg_dict = {
                'blank1': self.create_space(40, row= 0, column= 0, sticky=(EW),
                                           columnspan= 10),
                'lbl_tilt':self.create_label(self.src.get_attrb('tilt'),
                                            row= 1, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc11': self.create_space(2, row= 2, column= 1, sticky= (EW)),
                'tilt': self.create_entry(self.src.get_attrb('tilt'),
                                           row= 1, column= 2, sticky=(EW),
                                           justify= CENTER),
                'spc13': self.create_space(30, row= 1, column= 3, sticky= (EW)),                                                          
                'lbl_azm':self.create_label(self.src.get_attrb('azimuth'),
                                            row= 1, column= 4, justify= RIGHT,
                                            sticky= (EW)),
                'spc15': self.create_space(2, row= 1, column= 5, sticky= (EW)),
                'azimuth': self.create_entry(self.src.get_attrb('azimuth'),
                                           row= 1, column= 6, sticky=(EW),
                                           justify= CENTER),               
                'blank2': self.create_space(40, row= 2, column= 0, sticky=(EW),
                                           columnspan= 10),
                'lbl_mc':self.create_label(self.src.get_attrb('mtg_cnfg'),
                                            row= 3, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc31': self.create_space(2, row= 3, column= 1, sticky= (EW)),
                'mtg_cnfg': self.create_dropdown(self.src.get_attrb('mtg_cnfg'),
                                           row= 3, column= 2, sticky=(EW), 
                                           columnspan = 4, width = 40),
                'lbl_ms':self.create_label(self.src.get_attrb('mtg_spc'),
                                            row= 4, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc41': self.create_space(2, row= 4, column= 1, sticky= (EW)),
                'mtg_spc': self.create_entry(self.src.get_attrb('mtg_spc'),
                                           row= 4, column= 2, sticky=(EW),
                                           justify= CENTER),
                'spc43': self.create_space(30, row= 4, column= 3, sticky= (EW)),                                                          
                'lbl_mh':self.create_label(self.src.get_attrb('mtg_hgt'),
                                            row= 4, column= 4, justify= RIGHT,
                                            sticky= (EW)),
                'spc45': self.create_space(2, row= 4, column= 5, sticky= (EW)),
                'mtg_hgt': self.create_entry(self.src.get_attrb('mtg_hgt'),
                                           row= 4, column= 6, sticky=(EW),
                                           justify= CENTER),               
                'lbl_gc':self.create_label(self.src.get_attrb('gnd_cnd'),
                                            row= 5, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc51': self.create_space(2, row= 5, column= 1, sticky= (EW)),
                'gnd_cnd': self.create_dropdown(self.src.get_attrb('gnd_cnd'),
                                           row= 5, column= 2, validate= 'focusout',
                                           validatecommand= self.src.validate_gnd_cnd_setting),                                                         
                'spc53': self.create_space(2, row= 5, column= 3, sticky= (EW)),
                'lbl_alb':self.create_label(self.src.get_attrb('albedo'),
                                            row= 5, column= 4, justify= RIGHT,
                                            sticky= (EW)),
                'spc55': self.create_space(2, row= 5, column= 5, sticky= (EW)),
                'albedo': self.create_entry(self.src.get_attrb('albedo'),
                                           row= 5, column= 6, sticky=(EW),
                                           justify= CENTER),                                                             
                'blank3': self.create_space(40, row= 6, column= 0, sticky=(EW),
                                           columnspan= 10),

                'lbl_uis':self.create_label(self.src.get_attrb('uis'),
                                            row= 7, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc71': self.create_space(2, row= 7, column= 1, sticky= (EW)),
                'uis': self.create_entry(self.src.get_attrb('uis'),
                                           row= 7, column= 2, sticky=(EW),
                                           justify= CENTER, validate= 'focusout',
                                           validatecommand= self.src.validate_size_setting),
                'spc73': self.create_space(30, row= 7, column= 3, sticky= (EW)),                                                          
                'lbl_sip':self.create_label(self.src.get_attrb('sip'),
                                            row= 7, column= 4, justify= RIGHT,
                                            sticky= (EW)),
                'spc75': self.create_space(2, row= 7, column= 5, sticky= (EW)),
                'sip': self.create_entry(self.src.get_attrb('sip'),
                                           row= 7, column= 6, sticky=(EW),
                                           justify= CENTER, validate= 'focusout',
                                           validatecommand= self.src.validate_size_setting),               
                'lbl_tp':self.create_label(self.src.get_attrb('ary_tpnl'),
                                            row= 8, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc81': self.create_space(2, row= 8, column= 1, sticky= (EW)),
                'ary_tpnl': self.create_entry(self.src.get_attrb('ary_tpnl'),
                                           row= 8, column= 2, sticky=(EW),
                                           justify= CENTER),
                'lbl_vmp':self.create_label(self.src.get_attrb('ary_Vmp'),
                                            row= 9, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc91': self.create_space(2, row= 9, column= 1, sticky= (EW)),
                'ary_Vmp': self.create_entry(self.src.get_attrb('ary_Vmp'),
                                           row= 9, column= 2, sticky=(EW),
                                           justify= CENTER),
                'spc93': self.create_space(30, row= 9, column= 3, sticky= (EW)),                                                          
                'lbl_imp':self.create_label(self.src.get_attrb('ary_Imp'),
                                            row= 9, column= 4, justify= RIGHT,
                                            sticky= (EW)),
                'spc95': self.create_space(2, row= 9, column= 5, sticky= (EW)),
                'ary_Imp': self.create_entry(self.src.get_attrb('ary_Imp'),
                                           row= 9, column= 6, sticky=(EW),
                                           justify= CENTER),               
                
                }


def main():
    print ('PV Array Definition Check')



if __name__ == '__main__':
    main()
