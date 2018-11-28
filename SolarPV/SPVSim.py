#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  9 19:25:00 2018

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

from tkinter import *
from tkinter.filedialog import *
from datetime import date
import os.path


from PVSite import *
from PVBattery import *
from PVBatBank import *
from PVPanel import *
from PVArray import *
from PVInverter import *
from PVChgControl import *
from SiteLoad import *
import guiFrames as tbf
from PVUtilities import *
from SPVSwbrd import *
from NasaData import *
from Parameters import panel_types
import dateutil.parser


#TODO Create ArrayCombo Class to allow for implementing multiple Array configs
#TODO Implement handling of DC Loads as well as AC loads
#TODO Improve performance by implementing DataFrame vectored operations
class SPVSIM():
    def __init__(self):
        self.debug = False
        self.wdir = os.getcwd()
        self. mdldir = os.path.join(self.wdir, 'Models')
        self.rscdir = os.path.join(self.wdir, 'Resources')
        self.rptdir = os.path.join(self.wdir, 'Reports')
        self.countries = read_resource('Countries.csv', self.rscdir)
        self.modules = read_resource('CEC Modules.csv', self.rscdir)
        self.inverters = read_resource('CEC Inverters.csv', self.rscdir)
        self.sdw = None
        self.rdw = None
        self.stw = None
        
        self.filename = None         #Complete path to Current File
        self.site = PVSite(self)
        self.bat = PVBattery(self)
        self.pnl = PVPanel(self)
        self.ary = PVArray(self)
        self.bnk = PVBatBank(self)
        self.bnk.uses(self.bat)
        self.ary.uses(self.pnl)
        self.inv = PVInverter(self)
        self.load = SiteLoad(self)
        self.array_out = None   #The Solar Array Output by hour
        self.times = None
        self.months = None
        self.days_of_year = None
        self.days_of_month = None
        self.array_out = None
        self.batDrain = None
        self.bringUpDisplay()
        

    def bringUpDisplay(self):
        self.root = Tk()
        self.root.title("SolarPV System Simulator")
        self.root.protocol('WM_DELETE_WINDOW', self.on_app_delete)
        self.buildMasterDisplay()
        self.root.mainloop()

        
    def define_menuBar(self):
        self.menuoptions = {'File':[('Save',self.save_file),
                                    ('Save as', self.save_as), 
                                    ('Load File', self.import_file),
                                    ('Exit', self.on_app_delete)],
                            'Display':[('Daily Load', self.show_load_profile),
                                       {'Array Performance':[('Overview', 
                                                              self.show_array_performance), 
                                                             ('Best Day', 
                                                              self.show_array_best_day), 
                                                             ('Worst Day', 
                                                              self.show_array_worst_day)]},
                                       {'Battery Performance':[('Overview', 
                                                                self.bnk.show_bank_overview), 
                                                               ('Bank Drain', 
                                                                self.bnk.show_bank_drain),
                                                               ('Bank SOC', 
                                                                self.bnk.show_bank_soc)
                                               ]}
                                                ],
#                                       ('System Performance', self.dummy)],
                            'Report':[('System Description', 
                                       self.create_overview_report),
                                      ('Site Load', self.print_load)]}        
    
    def buildMasterDisplay(self):
        """ Build the Display Window """
        self.define_menuBar()
        mb = tbf.build_menubar(self.root, self.menuoptions)
        self.sdw = ttk.LabelFrame(self.root, text="System Description", borderwidth= 5,
                                width = 500, height = 500, padding= 15, relief= GROOVE)
        self.sdw.grid(row=1, column=1)
    
        self.rdw =ttk.Labelframe(self.root, text='Results', borderwidth= 5,
                                width = 500, height = 500, padding= 15, relief= GROOVE)
        self.rdw.grid(row=1, column=3)
        self.stw = tbf.status_window(self.root, 'Status Reporting', [2,1], 3 )
        self.buildSwitchboard()
        
    def buildSwitchboard(self):
        """ Method to Build Switchboard Display & Switching Logic """
        self.swb = spvSwitchboard(self, location = [0,0], parent= self.sdw, 
                                  menuTitle = 'Project Details')
    
    def on_app_delete(self):
        """ User has selected Window Abort """
        if tbf.ask_question('Window Abort', 'Save Existing File?'):
            self.save_file()
        if tbf.ask_question('Exit Application', 'Exit?'):
            self.root.destroy()
                         
    def save_as(self):
        """ Method to save existing project under new Filename """
        self.filename = None
        self.save_file
    
    def write_file(self, fn):
        """ Write DataDict to specified file  """
        dd = {'fn': self.filename,
              'atoms': self.site.atmospherics,
              'site': self.site.args,
              'bat': self.bat.args,
              'pnl': self.pnl.args,
              'ary': self.ary.args,
              'bnk': self.bnk.args,
              'inv': self.inv.args,
              'load': self.load,
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
        self.load = dd.pop('load', None)
        if self.load.master is None:
            self.load.master = self
        self.site.write_parameters(dd.pop('site', None)) 
        self.bat.write_parameters(dd.pop('bat', None)) 
        self.pnl.write_parameters(dd.pop('pnl', None)) 
        self.ary.write_parameters(dd.pop('ary', None)) 
        self.bnk.write_parameters(dd.pop('bnk', None))         
        self.inv.write_parameters(dd.pop('inv', None))

                     
    def import_file(self):
        """ Import Project Data File """
        fn = None
        while fn is None:
            fn = askopenfilename(parent= self.root, title= 'Load Project',
                               defaultextension= '.spv', 
                               initialdir= self.mdldir)
        if fn is not '':
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
        if fn is not '':
            self.filename = fn
            self.write_file(fn)

    def execute_simulation(self):
        """ Perform System Analysis     """
        if self.rdw.children is not None:
            kys = list(self.rdw.children.keys())
            while len(kys) > 0:
                self.rdw.children[kys.pop()].destroy()
          
        if self.perform_base_error_check():
            if self.stw is not None:
                self.stw.show_message('Starting System Analysis')
            self.loc = self.site.get_location()
            self.create_time_indices(self.site.read_attrb('tz'))
            self.site.get_atmospherics(self.times, self.stw)
            self.array_out = self.ary.define_array_performance(self.times, 
                                                self.site, self.inv, self.stw)
            self.array_out = self.array_out.assign(Month= self.months, 
                                             DayofMonth= self.days_of_month, 
                                         DayofYear= self.days_of_year)        
            self.array_out =self.array_out.assign(Load = hourly_load(self.times,
                                        self.load.get_load_profile()))
            self.build_monthly_performance(self.site.read_attrb('tz'))
            if self.stw is not None:
                self.stw.show_message('Panel Analysis Completed')
            self.batDrain  = self.bnk.define_battery_drain(self.array_out, 
                                                           self.inv.get_parameters())
            if self.stw is not None:
                srvc = self.batDrain['Service']
                nosrvc = srvc[srvc == False]
                k = 100* (len(srvc) - len(nosrvc))/len(srvc)
                ms = 'System Design provides Power to Load {0:.2f}% of the time'.format(k)
                if k < 100:
                    ms += '\n\tDesign fails to deliver required load {0} hours out of {1} hours per year'.format(len(nosrvc), len(srvc))
                ms += '\n\tAnnual Battery Charging Cycles = {0:.2f} out of {1} lifetime cycles'.format(self.bnk.tot_cycles, 
                                                           self.bnk.max_dischg_cycles)
                self.stw.show_message(ms)
            if self.debug:
                self.debug_next()
    
    def debug_next(self):
        """ Find a way to clear the results window on starting an analysis  """
        pass
        
#        suns = self.site.get_sun_times(self.times)
#        print(self.batDrain.head())
#        sr_soc = np.zeros(len(suns))
#        ss_soc = np.zeros(len(suns))
#        day = [None]*len(suns)
#        for i in range(len(suns)):
#            snr = suns['Sunrise'].iloc[i]
#            sns = suns['Sunset'].iloc[i]
#            snrtm = create_time_mask(snr, 'Lead')
#            snstm = create_time_mask(sns, 'Lag')
#            day[i] = snrtm
#            sr_soc[i] = self.batDrain.loc[snrtm]['Bat_SOC']
#            ss_soc[i] = self.batDrain.loc[snstm]['Bat_SOC']
#        bat_ovr = pd.DataFrame(data={'Sunrise':sr_soc, 'Sunset':ss_soc},
#                               index= day)
#        
#        bat_ovr.plot( kind= 'Line', title='Bank Overview') 
#        plt.show()
    
    
    
    def perform_base_error_check(self):
        """ method to conduct basic error checks 
            returns True if and only if no errors are found """            
        # Tests for Site Definition """
        if not self.site.check_definition():
            return False
            
        # Tests for Load Definition
        if not self.load.check_definition():
            return False
           
        #Tests for battery & bank definition
        if not self.bnk.check_definition():
            return False
    
        #Tests for panel & Array definition
        if not self.ary.check_definition():
            return False
    
        # Tests for proper inverter definition """
        if not  self.inv.check_definition():
            return False

        return True       

    def create_time_indices(self, tm_z):
        """ Create Base Dastaframe indicies for use in running simulations """
        now = date.today()
        self.baseyear = now.year-2
        if self.baseyear%4 == 0:
            # Don't use leap year 
            self.baseyear -= 1
        st = '{0}0101T0000{1:+}'.format(self.baseyear, tm_z) 
        nt = '{0}1231T2300{1:+}'.format(self.baseyear, tm_z) 
        self.times = pd.DatetimeIndex(start= st,
                                 end= nt,
                                 freq='H')
        self.months = month_timestamp(self.times).astype(int)
        self.days_of_year = doy_timestamp(self.times).astype(int)
        self.days_of_month = dom_timestamp(self.times).astype(int)

    #TODO Update monthly performance to combine multiple array_out dataFrames by summing p_mp data                       
    def build_monthly_performance(self, tm_z):
        """ Using Array Performance data create Monthly Synopsis of 
            system performance  """
        self.mpi = build_monthly_performance_info(self.array_out, 'p_mp')
        dl = np.array([self.load.get_daily_load()]*12)
        dlf = pd.DataFrame({'Daily Load':dl}, index=np.arange(1,13))
        self.mpi = self.mpi.join(dlf)
        min_mnth, min_day = find_worst_day(self.mpi)
        max_mnth, max_day = find_best_day(self.mpi)
        wds = dateutil.parser.parse('{0}{1:02}{2:02}T0000{3:+}'.format(self.baseyear, min_mnth, min_day, tm_z) )
        wde = dateutil.parser.parse('{0}{1:02}{2:02}T2300{3:+}'.format(self.baseyear, min_mnth, min_day, tm_z) )
        self.worst_day = [wds, wde]
        self.worst_day_perform = self.array_out.loc[pd.Timestamp(wds):pd.Timestamp(wde)]
        bds = dateutil.parser.parse('{0}{1:02}{2:02}T0000{3:+}'.format(self.baseyear, max_mnth, max_day, tm_z) )
        bde = dateutil.parser.parse('{0}{1:02}{2:02}T2300{3:+}'.format(self.baseyear, max_mnth, max_day, tm_z) ) 
        self.best_day_perform = self.array_out.loc[pd.Timestamp(bds):pd.Timestamp(bde)]
        self.best_day = [bds, bde]
        
   
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
            if fn is not '':
                self.filename = fn
                fo = open(fn, 'w')
                fo.write(s)
                fo.close()         
        else:
            print(s)        
                            
    #TODO fix SiteLoad Class to load or set master during initialization 
    def show_load_profile(self):
        """ Method to build & display the load profile graphic """ 
        self.load.show_load_profile(self.rdw)

        

    #TODO Move show_array_performance to PVArray Combo Class          
    def show_array_performance(self):
        """ Create graphic of Annual Solar Array Performance """
        if self.array_out is not None:
            xaxis = np.arange(1,13)
            pltslist = [{'label':'Avg Power', 'data':self.mpi.loc[:,'Avg Power'],
                        'type': 'Bar', 'color': 'b', 'width': 0.2, 'xaxis': xaxis},
                        {'label':'Best Power', 'data':self.mpi.loc[:,'Best Power'],
                        'type': 'Bar', 'color': 'g', 'width': 0.2, 
                        'xaxis':xaxis.copy() - 0.2},
                         {'label':'Worst Power', 'data':self.mpi.loc[:,'Worst Power'],
                        'type': 'Bar', 'color': 'y', 'width': 0.3, 
                        'offset': 0.3, 'xaxis':xaxis.copy() + 0.2},
                          {'label':'Daily Load', 'data':self.mpi.loc[:,'Daily Load'],
                        'type': 'Line', 'color': 'r', 'xaxis': xaxis, 
                        'width': 4.0, 'linestyle': 'solid' }
                         ]
            dp = tbf.plot_graphic(self.rdw, 'Month of Year', 'Watts', 
                                  np.arange(1,13),
                                  pltslist, 'Annual Array Performance', 
                                  (6,4))

    #TODO Move show_array_best_day to PVArray Combo Class       
    def show_array_best_day(self):
        """ Create graphic of Solar Array Best Day Performance  """
        if self.array_out is not None:
            xlabels = np.arange(24)
            pltslist = [{'label': 'Array Power', 
                         'data': self.best_day_perform['p_mp'],
                         'type': 'Line', 'xaxis': xlabels, 
                         'width': 2.0, 'color': 'b'},
                {'label': 'Hourly Load', 
                         'data': self.best_day_perform['Load'],
                         'type': 'Line', 'xaxis': xlabels , 
                         'width': 2.0, 'color': 'r'}]
            dp = tbf.plot_graphic(self.rdw, 'Time of Day', 'Watts', xlabels, 
                                  pltslist, 
                                  'Best Day Array Output', (6,4))

    #TODO Move show_array_worst_day to PVArray Combo Class   
    def show_array_worst_day(self):
        """ Create graphic of Solar Array Worst Day Performance  """
        if self.array_out is not None:
            xlabels = np.arange(24)
            pltslist = [{'label': 'Array Power', 
                         'data': self.worst_day_perform['p_mp'],
                         'type': 'Line', 'xaxis': xlabels, 
                         'width': 2.0, 'color': 'b'},
                {'label': 'Hourly Load', 
                         'data': self.worst_day_perform['Load'],
                         'type': 'Line', 'xaxis': xlabels , 
                         'width': 2.0, 'color': 'r'}]
            dp = tbf.plot_graphic(self.rdw, 'Time of Day', 'Watts', xlabels, 
                                  pltslist, 'Worst Day Array Output', (6,4))
            
    #TODO Remve when no more stiubs are required
    def dummy(self):
        """ Spur for all undefined Menu action methods """
        pass

        
def main():
    """ Starts the GUI and enables processing all functions """
    spv = SPVSIM()
       
if __name__ == '__main__':
    main()