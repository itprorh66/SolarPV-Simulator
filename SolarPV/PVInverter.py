#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  4 17:37:01 2018
Modified on 02/22/2019 for version 0.1.0
Modified on 3/4/2019 for issue #17


@author: Bob Hentz

-------------------------------------------------------------------------------
  Name:        PVPanel.py
  Purpose:     Provides for the methods & data structures associated with
               Implementing the Inverter for a Solar PV System

  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)

               This program is distributed WITHOUT ANY WARRANTY;
               without even the implied warranty of MERCHANTABILITY
               or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""
from FormBuilder import *
from PVUtilities import *
from Component import *
from FieldClasses import data_field, option_field

class PVInverter(Component):
    """ Methods associated with the definition, display, and operation of an
        Inverter """
    def __init__(self, master, **kargs):
        Component.__init__(self, master, 'PV Inverter', **kargs)

    def _define_attrbs(self):
        self.args = {
                 'i_mfg':option_field('m_mfg', 'Manufactuerer:', '',
                                    sorted(list(set(self.master.inverters['Manufacturer']))),
                                    self.master.inverters),
                 'i_mdl':option_field('m_mdl', 'Model:', '',
                                    sorted(list(set(self.master.inverters['Model']))),
                                    self.master.inverters),
                 'Name':data_field('Name', 'Description:', ''),
                 'Vac':data_field('Vac', 'AC Voltage (Vac):', 0.0),
                 'Paco':data_field('Paco', 'AC Power (Watts):', 0.0),
                 'Pdco':data_field('Pdco', 'DC Power Panel(Watts):', 0.0),
                 'Vdco':data_field('Vdco', 'DC Voltage (Vdc):', 0.0),
                 'Pnt':data_field('Pnt', 'Night Time Power (Watts):', 0.0),
                 'Vdcmax':data_field('Vdcmax', 'Max DC Voltage (Vdcmax):', 0.0),
                 'Idcmax':data_field('Idcmax','Max DC Current (Idcmax):', 0.0),
                 'Mppt_low':data_field('Mppt_low', 'Mppt_low (Vdc):', 0.0),
                 'Mppt_high':data_field('Mppt_high', 'Mppt_high (Vdc)', 0.0),
                 }


    def check_arg_definition(self):
        """ Check Inverter definition """
        if self.read_attrb('i_mfg') == "" or self.read_attrb('i_mdl') == '':
            return False, 'PV Inverter is undefined'
        if self.read_attrb('Paco') < self.master.site.read_attrb('gv'):
            return False, 'Inverter Output less than Grid Voltage'
        return True, ''


    def compute_dc_power(self, ac_load):
        """ Given an required AC_Load, return required input DC
             Power required by Inverter"""
        paco = self.read_attrb('Paco')
        pdco = self.read_attrb('Pdco')
        ie_ref = 0.9637
        if ac_load > 0:
            return (1+ ac_load*((pdco - paco)/paco))/ie_ref
        return 0.0

    def validate_mfg_setting(self):
        """ Triggered by a mfg field validation event
            Updates Model list based on  mfg selection """
        val = self.form.wdg_dict['i_mfg'].get_val()

        "clear the model attributes if the latest manufacturer has changed from previous"
        if self.args['i_mfg'].read_data() != val:
            self.set_attribute('i_mdl', None)
            for ky in self.args.keys():
                if ky == 'i_mdl' or ky == 'Name':
                    self.set_attribute(ky, '')
                    self.form.wdg_dict[ky].set_val()
                elif ky == 'i_mfg':
                    pass
                else:
                    self.set_attribute(ky, 0)
                    self.form.wdg_dict[ky].set_val()

        self.set_attribute('i_mfg', val)
        osrc = self.args['i_mfg'].get_option_source()
        nol = sorted(list(set(osrc['Manufacturer'])))
        lst = list(filter(lambda x: x.startswith(val), nol))

        if val != "":
            mdf = osrc[osrc['Manufacturer'].isin([self.args['i_mfg'].read_data()])]
            nol = sorted(list(set(mdf['Model'])))
            self.form.wdg_dict['i_mdl']['values']= nol
            self.args['i_mdl'].update_list(nol)
        else:
            for ky in self.args.keys():
                self.args[ky].reset_value()
                self.form.wdg_dict[ky].set_val()
                self.form.wdg_dict['i_mdl']['values']= nol
                self.args['i_mdl'].update_list(nol)
        return True

    def validate_mdl_setting(self):
        """ Triggered by a model field validation event """
        val = self.form.wdg_dict['i_mdl'].get_val()
        osrc = self.args['i_mdl'].get_option_source()
        lst = list(filter(lambda x: x.startswith(val), sorted(list(set(osrc['Model'])))))
        if len(lst) == 1:
            mdf = (osrc[osrc['Manufacturer'].
                           isin([self.form.wdg_dict['i_mfg'].get_val()]) &
                           osrc['Model'].isin(lst)])
            self.set_attribute('Name', mdf.index.values[0])
            self.form.wdg_dict['Name'].set_val()
            for ky in self.args.keys():
                if ky in mdf.columns:
                    self.set_attribute(ky, mdf[ky].values[0])
                    self.form.wdg_dict[ky].set_val()
        if len(lst) > 1 and self.get_attrb('Name') != "":
            self.args['Name'].reset_value()
            self.form.wdg_dict['Name'].set_val()
            for ky in self.args.keys():
                mdf = osrc
                if ky in mdf.columns:
                    self.args[ky].reset_value()
                    self.form.wdg_dict[ky].set_val()
        return True

    def display_input_form(self, parent_frame):
        """ Generate the data entry form """
        self.parent_frame = parent_frame
        self.form = InverterForm(parent_frame, self, row=1, column=1,  width= 300, height= 300,
                      borderwidth= 5, relief= GROOVE, padx= 10, pady= 10, ipadx= 5, ipady= 5)
        return self.form

class InverterForm(DataForm):
    def __init__(self, parent_frame, data_src, **kargs):
        DataForm.__init__(self, parent_frame, data_src, **kargs)

    def define_layout(self):
        self.wdg_dict = {
                'blank1': self.create_space(40, row= 1, column= 0, sticky=(EW),
                                           columnspan= 10),
                'lbl_mfg':self.create_label(self.src.get_attrb('i_mfg'),
                                            row= 2, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan = 3),
                'spc21': self.create_space(2, row= 2, column= 4, sticky= (EW)),
                'i_mfg': self.create_dropdown(self.src.get_attrb('i_mfg'),
                                           row= 2, column= 5, sticky=(EW),
                                           width= 45, justify= CENTER, columnspan= 5,
                                           validate= 'focusin',
                                           validatecommand= self.src.validate_mfg_setting),
                'lbl_mdl': self.create_label(self.src.get_attrb('i_mdl'),
                                            row= 3, column= 0, justify= RIGHT,
                                            columnspan = 3),
                'spc31': self.create_space(2, row= 3, column= 5, sticky= (EW)),
                'i_mdl': self.create_dropdown(self.src.get_attrb('i_mdl'),
                                           row= 3, column= 5, sticky=(EW),
                                           justify= CENTER, width= 35, columnspan= 5,
                                           validate= 'focusin',
                                           validatecommand= self.src.validate_mdl_setting),
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

                'lbl_paco':self.create_label(self.src.get_attrb('Paco'),
                                             row= 6, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc61': self.create_space(2, row= 6, column= 1, sticky= (EW)),
                'Paco': self.create_entry(self.src.get_attrb('Paco'),
                                             row= 6, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
               'spc62': self.create_space(2, row= 6, column= 3, sticky= (EW)),
               'lbl_pdco': self.create_label(self.src.get_attrb('Pdco'),
                                             row= 6, column= 4, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
                'Pdco': self.create_entry(self.src.get_attrb('Pdco'),
                                             row= 6, column= 6, justify= CENTER,
                                            sticky= (EW), width= 10),
                'lbl_pnt':self.create_label(self.src.get_attrb('Pnt'),
                                             row= 6, column= 8, justify= RIGHT,
                                            sticky= (EW)),
                'spc71': self.create_space(2, row= 6, column= 9, sticky= (EW)),
                'Pnt': self.create_entry(self.src.get_attrb('Pnt'),
                                             row= 6, column= 10, justify= CENTER,
                                            sticky= (EW), width= 10),
               'lbl_vac': self.create_label(self.src.get_attrb('Vac'),
                                             row= 7, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
               'spc71': self.create_space(2, row= 7, column= 1, sticky= (EW)),
                'Vac': self.create_entry(self.src.get_attrb('Vac'),
                                             row= 7, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
               'lbl_vdc': self.create_label(self.src.get_attrb('Vdco'),
                                             row= 7, column= 4, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
               'Vdco': self.create_entry(self.src.get_attrb('Vdco'),
                                             row= 7, column= 6, justify= CENTER,
                                            sticky= (EW), width= 10),
              'lbl_vdmx': self.create_label(self.src.get_attrb('Vdcmax'),
                                             row= 8, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
               'Vdcmax': self.create_entry(self.src.get_attrb('Vdcmax'),
                                             row= 8, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
               'lbl_idmx': self.create_label(self.src.get_attrb('Idcmax'),
                                             row= 8, column= 4, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
                'Idcmax': self.create_entry(self.src.get_attrb('Idcmax'),
                                             row= 8, column= 6, justify= CENTER,
                                            sticky= (EW), width= 10),
               'lbl_mplow': self.create_label(self.src.get_attrb('Mppt_low'),
                                             row= 9, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
                'Mppt_low': self.create_entry(self.src.get_attrb('Mppt_low'),
                                             row= 9, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
               'lbl_mphgh': self.create_label(self.src.get_attrb('Mppt_high'),
                                             row= 9, column= 4, justify= RIGHT,
                                            sticky= (EW)),
                'Mppt_high': self.create_entry(self.src.get_attrb('Mppt_high'),
                                             row= 9, column= 6, justify= CENTER,
                                            sticky= (EW), width= 10),
                'blank4': self.create_space(40, row= 15, column= 0, sticky=(EW),
                                           columnspan= 10)
                }



def main():
    print ('Inverter Definition Check')



if __name__ == '__main__':
    main()
