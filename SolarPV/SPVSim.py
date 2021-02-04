#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  9 19:25:00 2018
Modified on 11/27/2018 to Clean up comments
Modified on 12/01/2018 to resolve Save/Import Issue #1
Modified 0n 12/04/2018 to resolve Import Load Error - Issue #11
Modified on 02/25/2019 for version 0.1.0
Modified on 3/4/2019 for Issue #18
modified 1/8/2021 to clean up code as part of upgrade for pvlib 0.8
Modified 01/20/2021 to fix issue with inverter & chgcontrlr functions

@author: Bob Hentz
-------------------------------------------------------------------------------
  Name:        SPVSim.py
  Purpose:     Implement the GUI Features & logic required to implement the
               SPVSim Application.

  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)
              This program is distributed WITHOUT ANY WARRANTY;
              without even the implied warranty of MERCHANTABILITY
              or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""

from tkinter import Tk, GROOVE
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename

from datetime import datetime
import os.path
import pickle
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters

from PVSite import PVSite
from PVBattery import PVBattery
from PVBatBank import PVBatBank
from PVPanel import PVPanel
from PVArray import PVArray
from PVInverter import PVInverter
from PVChgControl import PVChgControl
from SiteLoad import SiteLoad
import guiFrames as tbf
from PVUtilities import (read_resource, hourly_load, create_time_indices, 
                         build_monthly_performance, build_overview_report,
                         computOutputResults)
from SPVSwbrd import spvSwitchboard
# from NasaData import *
# from Parameters import panel_types
# import dateutil.parser


class SPVSIM:
    def __init__(self):
        register_matplotlib_converters()
        self.debug = False
        self.perf_rept = False
        self.errflg = False
        self.wdir = os.getcwd()
        self.mdldir = os.path.join(self.wdir, 'Models')
        self.rscdir = os.path.join(self.wdir, 'Resources')
        self.rptdir = os.path.join(self.wdir, 'Reports')
        self.countries = read_resource('Countries.csv', self.rscdir)
        self.modules = read_resource('CEC Modules.csv', self.rscdir)
        self.inverters = read_resource('CEC Inverters.csv', self.rscdir)
        self.sdw = None      # System Description Window
        self.rdw = None      # Results Display Window
        self.stw = None      # Status Reporting Window

        self.array_list = list()
        self.filename = None         # Complete path to Current File
        self.site = PVSite(self)
        self.bat = PVBattery(self)
        self.pnl = PVPanel(self)
        self.ary = self.create_solar_array(self)
        self.array_list.append(self.ary)
        self.sec_ary = self.create_solar_array(self)
        self.array_list.append(self.sec_ary)
        self.bnk = PVBatBank(self)
        self.bnk.uses(self.bat)
        self.inv = PVInverter(self)
        self.load = SiteLoad(self)
        self.chgc = PVChgControl(self)
        self.array_out = None   # The Solar Array Output by hour
        self.times = None
        self.array_out = None
        self.power_flow = None
        self.outrec = None
        self.outfile = None
        self.bringUpDisplay()

    def bringUpDisplay(self):
        """ Create the Display GUI """
        self.root = Tk()
        self.root.title("SolarPV System Simulator")
        self.root.protocol('WM_DELETE_WINDOW', self.on_app_delete)
        self.buildMasterDisplay()
        self.root.mainloop()

    def define_menuBar(self):
        """ Format the Menu bar at top of display """
        self.menuoptions = {'File': [('Save', self.save_file),
                                     ('Save as', self.save_file),
                                     ('Load File', self.import_file),
                                     ('Exit', self.on_app_delete)],
                            'Display': [('Daily Load', self.show_load_profile),
                                        {'Array Performance': [
                                         ('Overview', self.show_array_performance),
                                         ('Best Day', self.show_array_best_day),
                                         ('Worst Day',  self.show_array_worst_day)]},
                                        {'Power Delivery': [
                                               ('Performance', self.show_pwr_performance),
                                                ('Best Day', self.show_pwr_best_day ),
                                                ('Worst Day', self.show_pwr_worst_day )]},
                                        {'Battery Performance': [
                                         ('Overview', self.bnk.show_bank_overview),
                                         ('Bank Drain', self.bnk.show_bank_drain),
                                         ('Bank SOC',  self.bnk.show_bank_soc)]}
                                        ],
                            'Report': [('System Description',
                                       self.create_overview_report),
                                      ('Site Load', self.print_load)]}

    def buildMasterDisplay(self):
        """ Build the Display Window """
        self.define_menuBar()
        tbf.build_menubar(self.root, self.menuoptions)
        self.sdw = ttk.LabelFrame(self.root, text="System Description", borderwidth= 5,
                                width= 500, height= 500, padding= 15, relief= GROOVE)
        self.sdw.grid(row= 1, column= 1)

        self.rdw = ttk.Labelframe(self.root, text='Results', borderwidth= 5,
                                width= 500, height= 500, padding= 15, relief= GROOVE)
        self.rdw.grid(row=1, column=3)
        self.stw = tbf.status_window(self.root, 'Status Reporting', [2, 1], 3 )
        self.buildSwitchboard()

    def buildSwitchboard(self):
        """ Method to Build Switchboard Display & Switching Logic """
        self.swb = spvSwitchboard(self, location= [0,0], parent= self.sdw,
                                  menuTitle= 'Project Details')
    def on_app_delete(self):
        """ User has selected Window Abort """
        if tbf.ask_question('Window Abort', 'Save Existing File?'):
            self.save_file()
        if tbf.ask_question('Exit Application', 'Exit?'):
            self.root.destroy()

    def write_file(self, fn):
        """ Write DataDict to specified file  """
        dd = {'fn': self.filename,
              'atoms': self.site.atmospherics,
              'site': self.site.args,
              'bat': self.bat.args,
              'pnl': self.pnl.args,
              'ary': self.ary.args,
              'ary_2':self.sec_ary.args,
              'bnk': self.bnk.args,
              'inv': self.inv.args,
              'load': self.load.export_frame(),
              'chgr': self.chgc.args
              }

        fo = open(fn, 'wb')
        pickle.dump(dd, fo)
        fo.close()

    def read_file(self, fn):
        """ Read specified file into DataDict """
        fo = open(fn, 'rb')
        dd = pickle.load(fo)
        fo.close()
        self.filename = dd.pop('fn', None)
        self.site.atmospherics = dd.pop('atoms', None)
        load_in = dd.pop('load', None)
        if load_in is not None:
            self.load.purge_frame()
            if type(load_in) is dict:
                self.load.import_frame(load_in)
            # This test is for backwards compatability
            else:
                ldi = load_in.df.to_dict('Index')
                self.load.import_frame(ldi)
        if self.load.master is None:
            self.load.master = self
        self.site.write_parameters(dd.pop('site', None))
        self.bat.write_parameters(dd.pop('bat', None))
        self.pnl.write_parameters(dd.pop('pnl', None))
        self.ary.write_parameters(dd.pop('ary', None))
        self.sec_ary.write_parameters(dd.pop('ary_2', None))
        self.bnk.write_parameters(dd.pop('bnk', None))
        self.inv.write_parameters(dd.pop('inv', None))
        self.chgc.write_parameters(dd.pop('chgr', None))

    def import_file(self):
        """ Import Project Data File """
        fn = None
        while fn is None:
            fn = askopenfilename(parent= self.root, title= 'Load Project',
                               defaultextension= '.spv',
                               initialdir= self.mdldir)
        if fn != '' and type(fn) is not tuple:
            # print (fn)
            self.filename = fn
            self.read_file(fn)

    def save_file(self):
        """ Method to Create New Project File """
        fn = None
        while fn is None:
            fn = asksaveasfilename(parent= self.root, title= 'New File',
                                   defaultextension= '.spv',
                                   initialfile = self.filename,
                                   initialdir= self.mdldir)
        if fn != ''and type(fn) is not tuple:
            self.write_file(fn)
            self.filename = fn

    def create_solar_array(self, src):
        sa = PVArray(src)
        sa.uses(self.pnl)
        return sa

    #TODO Should combine_arrays move to PVUtilities
    def combine_arrays(self):
        """ Combine primary & secondary array outputs to from a unified output
            using individual array outputs to include the following:
                Array Voltage (AV) = mim voltage for all arrays
                Array Current (AI) = sum (ac(i)*AV/av(i))
                Array Power (AP) = AV * AC
        """
        if len(self.array_list)> 0:
            frst_array = self.array_list[0].define_array_performance(self.times.index,
                                            self.site, self.inv, self.stw)
            rslt = pd.DataFrame({'ArrayVolts':frst_array['v_mp'],
                                 'ArrayCurrent':frst_array['i_mp'],
                                 'ArrayPower':frst_array['p_mp']},
                                  index = self.times.index)
            for ar in range(1, len(self.array_list)):
                sarf  =  self.array_list[ar].is_defined()
                if sarf:
                   sec_array = self.array_list[ar].define_array_performance(self.times.index,
                                                    self.site, self.inv, self.stw)
                   for rw in range(len(rslt)):
                       if rslt['ArrayPower'].iloc[rw] > 0 and sec_array['p_mp'].iloc[rw] >0:
                           v_out = min(rslt['ArrayVolts'].iloc[rw], sec_array['v_mp'].iloc[rw])
                           i_out = (rslt['ArrayCurrent'].iloc[rw] *
                                    (v_out/rslt['ArrayVolts'].iloc[rw]) +
                                    sec_array['i_mp'].iloc[rw]  *
                                    (v_out/sec_array['v_mp'].iloc[rw]))
                           rslt['ArrayVolts'].iloc[rw] = v_out
                           rslt['ArrayCurrent'].iloc[rw] = i_out
                           rslt['ArrayPower'].iloc[rw] = v_out * i_out
                       elif sec_array['p_mp'].iloc[rw] > 0:
                           rslt['ArrayVolts'].iloc[rw] = sec_array['v_mp'].iloc[rw]
                           rslt['ArrayCurrent'].iloc[rw] = sec_array['i_mp'].iloc[rw]
                           rslt['ArrayPower'].iloc[rw] = sec_array['p_mp'].iloc[rw]
            rslt = rslt.assign(Month= self.times['Month'],
                                         DayofMonth= self.times['DayofMonth'],
                                     DayofYear= self.times['DayofYear'])
            rslt = rslt.join(hourly_load(self.times.index,
                                    self.load.get_load_profile()))
            return rslt
        return None

    #TODO Should compute_powerFlows move to PVUtilities
    def compute_powerFlows(self):
        """ Computes the distribution of Array power to loads and
            a battery bank if it exists.  Returns a DataFrame containing
            performance data
            """
        self.array_out = self.combine_arrays()
        PO = np.zeros(len(self.array_out))  # amount of total load satisfied
        PS = np.zeros(len(self.array_out))  # fraction of load satisfied Power_out/TotLoad
        DE = np.zeros(len(self.array_out))  # amount of Array Power used to provide load
        BS = np.zeros(len(self.array_out))  # battery soc
        BD = np.zeros(len(self.array_out))  # power drawn from battery
        BP = np.zeros(len(self.array_out))  # remaining amount of usable Battery Power
        SL = np.zeros(len(self.array_out))  # load imposed by system chgCntlr * inverter
        EM = np.empty(len(self.array_out), dtype=object) # recorded error messages
        hdr = ' Indx \t ArP  \t ArI  \t ArV  \t dcLd \t acLd \t ttLd '
        hdr += '\t  PO  \t  PS  \t  DE  \t  SL  \t  BP  \t  BD  \t  BS  \t  EM\n'
        outln = '{0:06}\t{1:6.2f}\t{2:6.2f}\t{3:6.2f}\t{4:6.2f}\t'
        outln += '{5:6.2f}\t{6:6.2f}\t{7:6.2f}\t{8:6.2f}\t{9:6.2f}\t'
        outln += '{10:6.2f}\t{11:6.2f}\t{12:6.2f}\t{13:6.2f}\t{14}\n'
        bflg = self.bnk.is_defined()
        self.out_rec = hdr
        for tindx in range(len(self.array_out)):
            wkDict = dict()
            ArP = self.array_out['ArrayPower'].iloc[tindx]
            ArV = self.array_out['ArrayVolts'].iloc[tindx]
            ArI = self.array_out['ArrayCurrent'].iloc[tindx]
            # Correct for possible power backflow into array
            if ArP <= 0 or ArV <= 0 or ArI <= 0:
                ArP = 0.0
                ArV = 0.0
                ArI = 0.0
            dcLd = self.array_out['DC_Load'].iloc[tindx]
            acLd = self.array_out['AC_Load'].iloc[tindx]
            sysAttribs = {'Inv': self.inv, 'Chg': self.chgc, 'Bnk': self.bnk}
            computOutputResults(sysAttribs,  ArP, ArV, ArI, acLd, dcLd, wkDict)

            # update arrays for tindx
            PO[tindx] = wkDict.pop('PO', 0.0)
            PS[tindx] = wkDict.pop('PS', 0.0)
            DE[tindx] = wkDict.pop('DE', 0.0)
            SL[tindx] = wkDict.pop('SL', 0.0)
            if bflg:
                BS[tindx] = wkDict.pop('BS', self.bnk.get_soc())*100
                BD[tindx] = wkDict.pop('BD', 0.0)
                BP[tindx] = wkDict.pop('BP', self.bnk.current_power())
            msg = ''
            errfrm = None
            if 'Error' in wkDict.keys():
                days: int = 1 + tindx//24
                errfrm = wkDict['Error']
                msg = 'After {0} days '.format(days)
                EM[tindx] = msg + errfrm[0].replace('\n', ' ')
            else:
                EM[tindx]= ""
            self.out_rec += outln.format(tindx, ArP, ArV, ArI,
                                         dcLd, acLd, dcLd+acLd,
                                         PO[tindx], PS[tindx], DE[tindx],
                                         SL[tindx], BP[tindx], BD[tindx],
                                         BS[tindx], EM[tindx])
            if self.debug and errfrm != None:
                if self.errflg == False and errfrm[1] != 'Fatal':
                    self.errflg = True
                    self.stw.show_message(msg + errfrm[0], errfrm[1])
                if errfrm[1] == 'Fatal':
                    msg = 'After {0} days '.format(days)
                    self.errflg = True
                    self.stw.show_message(msg + errfrm[0], errfrm[1])
                    break

        # Create the DataFrame
        rslt = pd.DataFrame({'PowerOut': PO,
                             'ArrayPower': self.array_out['ArrayPower'],
                           'Service': PS,
                           'DelvrEff': DE,
                           'BatSoc': BS,
                           'BatDrain': BD,
                           'BatPwr': BP
                           }, index = self.times.index)

        rslt = rslt.assign(Month= self.times['Month'],
                                     DayofMonth= self.times['DayofMonth'],
                                 DayofYear= self.times['DayofYear'])
        rslt = rslt.join(hourly_load(self.times.index,
                                self.load.get_load_profile()))
        return rslt

    def execute_simulation(self):
        """ Perform System Analysis     """
        if self.rdw.children is not None:
            kys = list(self.rdw.children.keys())
            while len(kys) > 0:
                self.rdw.children[kys.pop()].destroy()

        if self.perform_base_error_check():
            self.errflg = False
            rt = datetime.now()
            ft = 'run_{0}_{1:02}_{2}_{3:02}{4:02}{5:02}.txt'
            self.outfile = ft.format(rt.year, rt.month, rt.day,
                                     rt.hour, rt.minute, rt.second)
            self.outrec = None
            bnkflg = self.bnk.is_defined()
            if self.stw is not None:
                self.stw.show_message('Starting System Analysis')
            self.loc = self.site.get_location()
            self.times = create_time_indices(self.site.read_attrb('tz'))
            self.site.get_atmospherics(self.times.index, self.stw)
            if bnkflg:
                self.bnk.initialize_bank()
            self.array_out = self.combine_arrays()
            self.mnthly_array_perfm = build_monthly_performance(self.array_out,
                                                                'ArrayPower')
            dl = np.array([self.load.get_daily_load()]*12)
            dlf = pd.DataFrame({'Daily Load':dl},
                               index=self.mnthly_array_perfm[0].index.values)
            self.mnthly_array_perfm[0] = self.mnthly_array_perfm[0].join(dlf)
            if self.stw is not None and self.errflg == False:
                self.stw.show_message('Panel Analysis Completed')

            if self.stw is not None:
                self.stw.show_message('Starting Power Analysis')
            self.power_flow = self.compute_powerFlows()
            self.mnthly_pwr_perfm = build_monthly_performance(self.power_flow,
                                                              'PowerOut')
            self.mnthly_pwr_perfm[0] = self.mnthly_pwr_perfm[0].join(dlf)
            if self.stw is not None and self.errflg == False:
                self.stw.show_message('Power Analysis Completed')

            if self.stw is not None:
                if self.errflg == False:
                    srvchrs = self.power_flow['Service'].sum()
                    dmndhrs = self.load.get_demand_hours()*365
                    if dmndhrs > 0:
                        k = srvchrs/dmndhrs
                        ms = 'System Design provides Power to Load {0:.2f}% of the time'.format(k*100)
                        if k < 100:
                            ms += '\n\tDesign delivers required load {0:.2f} hours out of {1} demand hours per year'.format(k*dmndhrs, dmndhrs)
                        if self.bnk.check_definition():
                            ms += '\n\tAnnual Battery Charging Cycles = {0:.2f} out of {1} specified lifetime cycles'.format(self.bnk.tot_cycles,
                                                                   self.bnk.max_dischg_cycles)
                        self.stw.show_message(ms)
                    else:
                        self.stw.show_message('Analysis complete')
            if self.debug:
                self.debug_next()

    def debug_next(self):
        """ Handy function for debugging  """
#        print(self.times)
#        calndr = create_calendar_indices(self.site.read_attrb('tz'))
#        print(calndr.head())
#        print(calndr.index)
        if self.perf_rept:
            fo = open(self.outfile, 'w')
            fo.write(self.out_rec)
            fo.close()

    def perform_base_error_check(self):
        """ method to conduct basic error checks
            returns True if and only if no errors are found """
        # Tests for Site Definition """
        bflg = False
        invflg = False

        if not self.site.check_definition():
            return False

        #Tests for panel & Array definition
        if not self.ary.check_definition():
            return False

        # Tests for proper inverter definition """
        if sum(self.load.get_load_profile()['AC']) > 0:
            if not self.inv.check_definition():
                return False
            else:
                invflg = True

        if self.bnk.check_definition():
            bflg = True

        """Tests for Charge Controller definition
           (only read if an inverter or battery is defined) """
        if bflg and not invflg and not self.chgc.check_definition():
            return False

        return True

    #TODO in Print Load improve formatting control for better tabular results
    def print_load(self):
        """ Method to build a print the load profile  """
        s = str(self.load)
        rpt_ttl = 'Load Report'
        self.output_report(rpt_ttl, s)

    def create_overview_report(self):
        """ Create a formated overview of Project Design data """
        s = build_overview_report(self)
        rpt_ttl = 'Overview Report'
        self.output_report(rpt_ttl, s)

    def output_report(self, rpt_ttl, s):
        """ Method to ask wheteher to print or create an output file for contents
            of s """
        if tbf.ask_question(rpt_ttl, 'Save Report to File?'):
            fn = None
            while fn is None:
                fn = asksaveasfilename(parent= self.root, title= 'Report Save',
                                       defaultextension= '.txt',
                                       initialfile = '',
                                       initialdir= self.rptdir)
            if fn != '':
                self.filename = fn
                fo = open(fn, 'w')
                fo.write(s)
                fo.close()
        else:
            print(s)

    def show_load_profile(self):
        """ Method to build & display the load profile graphic """
        self.load.show_load_profile(self.rdw)
    
    #TODO can all of these show methods be combined and controlled by variables?
    def show_pwr_performance(self):
        """ Create graphic of Annual Power Delivery vice Load  """
        if self.array_out is not None:
            mpi = self.mnthly_pwr_perfm[0]
            xaxis = np.arange(1,13)
            pltslist = [{'label':'Avg Power', 'data':mpi.loc[:,'Avg PowerOut'],
                        'type': 'Bar', 'color': 'b', 'width': 0.2, 'xaxis': xaxis},
                        {'label':'Best Power', 'data':mpi.loc[:,'Best PowerOut'],
                        'type': 'Bar', 'color': 'g', 'width': 0.2,
                        'xaxis':np.arange(1,13) - 0.2},
                         {'label':'Worst Power', 'data':mpi.loc[:,'Worst PowerOut'],
                        'type': 'Bar', 'color': 'y', 'width': 0.3,
                        'offset': 0.3, 'xaxis':np.arange(1,13) + 0.2},
                          {'label':'Daily Load', 'data':mpi.loc[:,'Daily Load'],
                        'type': 'Line', 'color': 'r', 'xaxis': xaxis,
                        'width': 4.0, 'linestyle': 'solid' }
                        ]
            tbf.plot_graphic(self.rdw, 'Month of Year', 'Watts Relative to Load',
                                  np.arange(1,13),
                                  pltslist, 'Power Output Performance',
                                  (6,4))

    def show_pwr_best_day(self):
        """ Create graphic of Solar Array Best Day Performance  """
        if self.array_out is not None:
            best_day_perform = self.power_flow.loc[self.power_flow['DayofYear'] == self.mnthly_pwr_perfm[1]]
            xlabels = np.arange(24)
            pltslist = [{'label': 'Power Output',
                         'data': best_day_perform['PowerOut'],
                         'type': 'Line', 'xaxis': xlabels,
                         'width': 2.0, 'color': 'b'},
                {'label': 'Hourly Load',
                         'data': best_day_perform['Total_Load'],
                         'type': 'Line', 'xaxis': xlabels ,
                         'width': 2.0, 'color': 'r'}]
            tbf.plot_graphic(self.rdw, 'Time of Day', 'Watts', xlabels,
                                  pltslist,
                                  'Best Day Power Output', (6,4))

    def show_pwr_worst_day(self):
        """ Create graphic of Solar Array Best Day Performance  """
        if self.array_out is not None:
            worst_day_perform = self.power_flow.loc[self.power_flow['DayofYear'] == self.mnthly_pwr_perfm[2]]
            xlabels = np.arange(24)
            pltslist = [{'label': 'Power Output',
                         'data': worst_day_perform['PowerOut'],
                         'type': 'Line', 'xaxis': xlabels,
                         'width': 2.0, 'color': 'b'},
                {'label': 'Hourly Load',
                         'data': worst_day_perform['Total_Load'],
                         'type': 'Line', 'xaxis': xlabels ,
                         'width': 2.0, 'color': 'r'}]
            tbf.plot_graphic(self.rdw, 'Time of Day', 'Watts', xlabels,
                                  pltslist,
                                  'Worst Day Power Output', (6,4))

    def show_array_performance(self):
        """ Create graphic of Annual Solar Array Performance """
        if self.array_out is not None:
            mpi = self.mnthly_array_perfm[0]
            xaxis = np.arange(1,13)
            pltslist = [{'label':'Avg Power', 'data':mpi.loc[:,'Avg ArrayPower'],
                        'type': 'Bar', 'color': 'b', 'width': 0.2, 'xaxis': xaxis},
                        {'label':'Best Power', 'data':mpi.loc[:,'Best ArrayPower'],
                        'type': 'Bar', 'color': 'g', 'width': 0.2,
                        'xaxis':np.arange(1,13) - 0.2},
                         {'label':'Worst Power', 'data':mpi.loc[:,'Worst ArrayPower'],
                        'type': 'Bar', 'color': 'y', 'width': 0.3,
                        'offset': 0.3, 'xaxis':np.arange(1,13) + 0.2},
                          {'label':'Daily Load', 'data':mpi.loc[:,'Daily Load'],
                        'type': 'Line', 'color': 'r', 'xaxis': xaxis,
                        'width': 4.0, 'linestyle': 'solid' }
                         ]
            tbf.plot_graphic(self.rdw, 'Month of Year', 'Watts',
                                  np.arange(1,13),
                                  pltslist, 'Annual Array Performance',
                                  (6,4))

    def show_array_best_day(self):
        """ Create graphic of Solar Array Best Day Performance  """
        if self.array_out is not None:
            best_day_perform = self.array_out.loc[self.array_out['DayofYear'] == self.mnthly_array_perfm[1]]
            xlabels = np.arange(24)
            pltslist = [{'label': 'Array Power',
                         'data': best_day_perform['ArrayPower'],
                         'type': 'Line', 'xaxis': xlabels,
                         'width': 2.0, 'color': 'b'},
                {'label': 'Hourly Load',
                         'data': best_day_perform['Total_Load'],
                         'type': 'Line', 'xaxis': xlabels ,
                         'width': 2.0, 'color': 'r'}]
            tbf.plot_graphic(self.rdw, 'Time of Day', 'Watts', xlabels,
                                  pltslist,
                                  'Best Day Array Output', (6,4))

    def show_array_worst_day(self):
        """ Create graphic of Solar Array Worst Day Performance  """
        if self.array_out is not None:
            worst_day_perform = self.array_out.loc[self.array_out['DayofYear'] == self.mnthly_array_perfm[2]]
            xlabels = np.arange(24)
            pltslist = [{'label': 'Array Power',
                         'data': worst_day_perform['ArrayPower'],
                         'type': 'Line', 'xaxis': xlabels,
                         'width': 2.0, 'color': 'b'},
                {'label': 'Hourly Load',
                         'data': worst_day_perform['Total_Load'],
                         'type': 'Line', 'xaxis': xlabels ,
                         'width': 2.0, 'color': 'r'}]
            tbf.plot_graphic(self.rdw, 'Time of Day', 'Watts', xlabels,
                                  pltslist, 'Worst Day Array Output', (6,4))


def main():
    """ Starts the GUI and enables processing all functions """
    SPVSIM()

if __name__ == '__main__':
    main()
