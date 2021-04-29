#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct  2 12:40:59 2018
Modified on 02/22/2019 for version 0.1.0
Modified on 3/4/2019 for issue #17

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
#from PVUtilities import *
from tkinter import *
from Component import Component
from FormBuilder import DataForm
from FieldClasses import data_field, option_field

class PVPanel(Component):
    """ Methods associated with the definition, display, and operation of a
        Solar Panel """
    def __init__(self, master, **kargs):
        self.pnlparms = None
        Component.__init__(self, master,'PV Panel', **kargs)

    def _define_attrbs(self):
        self.args = {
                 'm_mfg':option_field('m_mfg', 'Manufactuerer:', '',
                                    sorted(list(set(self.master.modules['Manufacturer']))),
                                    self.master.modules),
                 'm_mdl':option_field('m_mdl', 'Model:', '',
                                    sorted(list(set(self.master.modules['Model']))),
                                    self.master.modules),
                 'Name':data_field('Name', 'Description:', ''),
                 'Technology':data_field('Technology','Cell Type:  ', ''),
                 'T_NOCT':data_field('T_NOCT', 'Nominal Operating Cell Temp:', 0.0),
                 'V_mp_ref':data_field('V_mp_ref','Voltage at Max Power (Vmp):', 0.0),
                 'I_mp_ref':data_field('I_mp_ref', 'Current at Max Power (Imp):', 0.0),
                 'V_oc_ref':data_field('V_oc_ref','Open Circuit Voltage (Voc):', 0.0),
                 'I_sc_ref':data_field('I_sc_ref','Short Circuit Current (Isc):', 0.0),
                 'PTC':data_field('PTC', 'Power Rating Pmpp (W):', 0.0),
                 'A_c':data_field('A_c', 'Cell Size(cm):', 0.0),
                 'N_s':data_field('N_s', 'Number of cells:', 0),
                 'R_s':data_field('R_s', 'Series Resistance (ohms):', 0.0),
                 'R_sh_ref':data_field('R_sh_ref','Shunt Resistance (ohms):', 0.0),
                 'BIPV':data_field('BIPV', 'BIPV:', 0.0),
                 'alpha_sc':data_field('alpha_sc', 'alpha_sc:', 0.0),
                 'beta_oc':data_field('beta_oc', 'beta_oc:', 0.0),
                 'a_ref':data_field('a_ref', 'a_ref:', 0.0),
                 'I_L_ref':data_field('I_L_ref', 'I_L_ref:', 0.0),
                 'I_o_ref':data_field('I_o_ref', 'I_o_ref:', 0.0),
                 'Adjust':data_field('Adjust', 'Adjust:', 0.0),
                 'gamma_r':data_field('gamma_r', 'gamma_r:', 0.0)
                 }


    def check_arg_definition(self):
        """ Check Panel definition """
        if self.read_attrb('m_mfg') == "" or self.read_attrb('m_mdl') == '':
            return False, 'PV Panel is undefined'
        return True, ''


    def validate_mfg_setting(self):
        """ Triggered by a mfg field validation event
            Updates Model list based on  mfg selection """
        val = self.form.wdg_dict['m_mfg'].get_val()

        "clear the model attributes if the latest manufacturer has changed from previous"
        if self.args['m_mfg'].read_data() != val:
            self.set_attribute('m_mdl', None)
            for ky in self.args.keys():
                if ky == 'm_mdl' or ky == 'Name':
                    self.set_attribute(ky, '')
                    self.form.wdg_dict[ky].set_val()
                elif ky == 'm_mfg':
                    pass
                else:
                    self.set_attribute(ky, 0)
                    self.form.wdg_dict[ky].set_val()

        self.set_attribute('m_mfg', val)
        osrc = self.args['m_mfg'].get_option_source()
        nol =  sorted(list(set(osrc['Manufacturer'])))
        lst = list(filter(lambda x: x.startswith(val), nol))
        if val != "":
            mdf = osrc[osrc['Manufacturer'].isin([self.args['m_mfg'].read_data()])]
            nol = sorted(list(set(mdf['Model'])))
            self.form.wdg_dict['m_mdl']['values']= nol
            self.args['m_mdl'].update_list(nol)
        else:
            for ky in self.args.keys():
                self.args[ky].reset_value()
                self.form.wdg_dict[ky].set_val()
                self.form.wdg_dict['m_mdl']['values']= nol
                self.args['m_mdl'].update_list(nol)
        return True

    def validate_mdl_setting(self):
        """ Triggered by a model field validation event """
        val = self.form.wdg_dict['m_mdl'].get_val()
        self.set_attribute('m_mdl', val)
        osrc = self.args['m_mdl'].get_option_source()
        lst = list(filter(lambda x: x.startswith(val), sorted(list(set(osrc['Model'])))))
        if len(lst) == 1:
            mdf = (osrc[osrc['Manufacturer'].
                           isin([self.form.wdg_dict['m_mfg'].get_val()]) &
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
        self.parent_frame = parent_frame
        self.form = PanelForm(parent_frame, self, row=1, column=1,  width= 300, height= 300,
                      borderwidth= 5, relief= GROOVE, padx= 10, pady= 10, ipadx= 5, ipady= 5)
        return self.form


#Define the data entry form for the Solar Panel
class PanelForm(DataForm):
    def __init__(self, parent_frame, data_src, **kargs):
        DataForm.__init__(self, parent_frame, data_src, **kargs)

    def define_layout(self):
        self.wdg_dict = {
                'blank1': self.create_space(40, row= 1, column= 0, sticky=(EW),
                                           columnspan= 10),
                'lbl_mfg':self.create_label(self.src.get_attrb('m_mfg'),
                                            row= 2, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan = 3),
                'spc21': self.create_space(2, row= 2, column= 4, sticky= (EW)),
                'm_mfg': self.create_dropdown(self.src.get_attrb('m_mfg'),
                                           row= 2, column= 5, sticky=(EW),
                                           name= self.src.get_attrb_name('m_mfg'),
                                           width= 45, justify= CENTER, columnspan= 5,
                                           validate= 'focusin',
                                           validatecommand= self.src.validate_mfg_setting),
                'lbl_mdl': self.create_label(self.src.get_attrb('m_mdl'),
                                            row= 3, column= 0, justify= RIGHT,
                                            columnspan = 3),
                'spc35': self.create_space(2, row= 3, column= 5, sticky= (EW)),
                'm_mdl': self.create_dropdown(self.src.get_attrb('m_mdl'),
                                           row= 3, column= 5, sticky=(EW),
                                           justify= CENTER, width= 35, columnspan= 5,
                                           validate= 'focusin',
                                           validatecommand= self.src.validate_mdl_setting),
                'lbl_desc': self.create_label(self.src.get_attrb('Name'),
                                            row= 4, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc41': self.create_space(2, row= 4, column= 1, sticky= (EW)),
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

                'lbl_PTC':self.create_label(self.src.get_attrb('PTC'),
                                             row= 6, column= 0, justify= RIGHT,
                                            sticky= (EW)),
                'spc61': self.create_space(2, row= 6, column= 1, sticky= (EW)),
                'PTC': self.create_entry(self.src.get_attrb('PTC'),
                                             row= 6, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
               'spc62': self.create_space(2, row= 6, column= 3, sticky= (EW)),
               'lbl_vmp': self.create_label(self.src.get_attrb('V_mp_ref'),
                                             row= 6, column= 4, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
                'V_mp_ref': self.create_entry(self.src.get_attrb('V_mp_ref'),
                                             row= 6, column= 6, justify= CENTER,
                                            sticky= (EW), width= 10),
                'lbl_imp':self.create_label(self.src.get_attrb('I_mp_ref'),
                                             row= 6, column= 8, justify= RIGHT,
                                            sticky= (EW)),
                'spc71': self.create_space(2, row= 6, column= 9, sticky= (EW)),
                'I_mp_ref': self.create_entry(self.src.get_attrb('I_mp_ref'),
                                             row= 6, column= 10, justify= CENTER,
                                            sticky= (EW), width= 10),

               'lbl_voc': self.create_label(self.src.get_attrb('V_oc_ref'),
                                             row= 7, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
               'spc71': self.create_space(2, row= 7, column= 1, sticky= (EW)),
                'V_oc_ref': self.create_entry(self.src.get_attrb('V_oc_ref'),
                                             row= 7, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
               'lbl_isc': self.create_label(self.src.get_attrb('I_sc_ref'),
                                             row= 7, column= 4, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
                'I_sc_ref': self.create_entry(self.src.get_attrb('I_sc_ref'),
                                             row= 7, column= 6, justify= CENTER,
                                            sticky= (EW), width= 10),
               'lbl_tech': self.create_label(self.src.get_attrb('Technology'),
                                             row= 7, column= 8, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
                'Technology': self.create_entry(self.src.get_attrb('Technology'),
                                             row= 7, column= 10, justify= CENTER,
                                            sticky= (EW)),

              'lbl_rs': self.create_label(self.src.get_attrb('R_s'),
                                             row= 8, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
                'R_s': self.create_entry(self.src.get_attrb('R_s'),
                                             row= 8, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
               'lbl_rsh': self.create_label(self.src.get_attrb('R_sh_ref'),
                                             row= 8, column= 4, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
                'R_sh_ref': self.create_entry(self.src.get_attrb('R_sh_ref'),
                                             row= 8, column= 6, justify= CENTER,
                                            sticky= (EW), width= 10),
                'lbl_noct':self.create_label(self.src.get_attrb('T_NOCT'),
                                             row= 8, column= 8, justify= RIGHT,
                                            sticky= (EW)),
               'spc71': self.create_space(2, row= 8, column= 9, sticky= (EW)),
                'T_NOCT': self.create_entry(self.src.get_attrb('T_NOCT'),
                                             row= 8, column= 10, justify= CENTER,
                                            sticky= (EW), width= 10),
               'lbl_ac': self.create_label(self.src.get_attrb('A_c'),
                                             row= 9, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
                'A_c': self.create_entry(self.src.get_attrb('A_c'),
                                             row= 9, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
               'lbl_ns': self.create_label(self.src.get_attrb('N_s'),
                                             row= 9, column= 4, justify= RIGHT,
                                            sticky= (EW)),
                'N_s': self.create_entry(self.src.get_attrb('N_s'),
                                             row= 9, column= 6, justify= CENTER,
                                            sticky= (EW), width= 10),
                'lbl_bipv':self.create_label(self.src.get_attrb('BIPV'),
                                             row= 9, column= 8, justify= RIGHT,
                                            sticky= (EW)),
                'BIPV': self.create_entry(self.src.get_attrb('BIPV'),
                                             row= 9, column= 10, justify= CENTER,
                                            sticky= (EW), width= 10),
               'lbl_asc': self.create_label(self.src.get_attrb('alpha_sc'),
                                             row= 10, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
                'alpha_sc': self.create_entry(self.src.get_attrb('alpha_sc'),
                                             row= 10, column= 2, justify= LEFT,
                                            sticky= (EW), width= 20),
               'lbl_boc': self.create_label(self.src.get_attrb('beta_oc'),
                                             row= 10, column= 4, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
                'beta_oc': self.create_entry(self.src.get_attrb('beta_oc'),
                                             row= 10, column= 6, justify= CENTER,
                                            sticky= (EW), width= 10),
                'lbl_aref':self.create_label(self.src.get_attrb('a_ref'),
                                             row= 10, column= 8, justify= RIGHT,
                                            sticky= (EW)),
#               'spc71': self.create_space(2, row= 11, column= 1, sticky= (EW)),
                'a_ref': self.create_entry(self.src.get_attrb('a_ref'),
                                             row= 10, column= 10, justify= CENTER,
                                            sticky= (EW), width= 10),
#               'spc72': self.create_space(2, row= 11, column= 3, sticky= (EW)),
               'lbl_ilref': self.create_label(self.src.get_attrb('I_L_ref'),
                                             row= 11, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
#               'spc62': self.create_space(2, row= 6, column= 5, sticky= (EW)),
                'I_L_ref': self.create_entry(self.src.get_attrb('I_L_ref'),
                                             row= 11, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),
               'lbl_ioref': self.create_label(self.src.get_attrb('I_o_ref'),
                                             row= 11, column= 4, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
                'I_o_ref': self.create_entry(self.src.get_attrb('I_o_ref'),
                                             row= 11, column= 6, justify= LEFT,
                                            sticky= (EW), width= 20),

                'lbl_adj':self.create_label(self.src.get_attrb('Adjust'),
                                             row= 11, column= 8, justify= RIGHT,
                                            sticky= (EW)),
#               'spc71': self.create_space(2, row= 12, column= 1, sticky= (EW)),
                'Adjust': self.create_entry(self.src.get_attrb('Adjust'),
                                             row= 11, column= 10, justify= CENTER,
                                            sticky= (EW), width= 10),
#               'spc72': self.create_space(2, row= 12, column= 3, sticky= (EW)),
               'lbl_gmr': self.create_label(self.src.get_attrb('gamma_r'),
                                             row= 12, column= 0, justify= RIGHT,
                                            sticky= (EW), columnspan = 2),
#               'spc62': self.create_space(2, row= 6, column= 5, sticky= (EW)),
                'gamma_r': self.create_entry(self.src.get_attrb('gamma_r'),
                                             row= 12, column= 2, justify= CENTER,
                                            sticky= (EW), width= 10),


                'blank4': self.create_space(40, row= 15, column= 0, sticky=(EW),
                                           columnspan= 10)
                }



def main():
    print ('PVPanel Definition Check')



if __name__ == '__main__':
    main()
