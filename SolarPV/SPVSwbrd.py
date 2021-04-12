#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  8 14:42:27 2018
Modified on 11/27/2018 to Clean up Comments
Modified on 02/22/2019 for version 0.1.0
Modified 0n 04/11/2021 to implement Record delete function see issue #13
@author: Bob Hentz
-------------------------------------------------------------------------------
  Name:        SPVSwbDisplay.py
  Purpose:     Provide a Switchboard Menu to allow interactive update of the
               Project Definition data (Summary, Load, Batteries, Panels, & 
               Inverters)               
  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)
              This program is distributed WITHOUT ANY WARRANTY;
              without even the implied warranty of MERCHANTABILITY
              or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""

from tkinter import *
import tkinter.ttk as ttk
import guiFrames as tbf
import SiteLoadDisplay as sld

class spvSwitchboard(tbf.switchboard):
    """  Methods to implement Switchboard """
    def __init__(self, prj, location = None, parent= None, menuTitle = None):
        self.tld = None
        self.dsply = None
        self.frm = None
        tbf.switchboard.__init__(self, prj, location, parent, menuTitle)
               
    def define_menu(self):
        """ Method to set specific menu options """
        """ self_actions  is a list of tuples defining each menu item 
            The tuple consists of:
                descript_txt: describing the menu action
                btn_text:     identifying the button text
                command:      directing the action when button is clicked"""    
        self.actions = [('Define Project Overview', 'Project', self.dsplySum),
                       ('Define Energy Load', 'Load', self.dsplyLoad),
                       ('Specify Solar Panel', 'Panel', self.dsplyPnls),
                       ('Define Primary Solar Array', 'Array', self.dsplyAry),
                       ('Define Alternate Solar Array', 'Alt Array', self.dsplyAltAry),
                       ('Specify Battery ', 'Battery', self.dsplyBats),
                       ('Define Battery Bank', 'Bank', self.dsplyBnk),
                       ('Define Charge Controller', 'ChgCnt', self.dsplyChg),
                       ('Specify Inverter', 'Inverter', self.dsplyInvtrs),
                       ('Perform System Analysis', 'Analyze', self.runSim)]

    def dsplySum(self):
        """ Display Site Description Input Form """
        self.define_toplevel('Site/Project')
        self.frm =  self.src.site.display_input_form(self.dsply)
        
    def dsplyLoad(self):
        """ Display Site Electric Load Definition Input Form """
        self.define_toplevel( 'Electrical Load')
        self.frm = sld.Table(self.src.load, self.dsply, "Del")
           
    def dsplyBats(self):
        """ Display Battery Description Input Form """
        self.define_toplevel('Battery')
        self.frm = self.src.bat.display_input_form(self.dsply)

    def dsplyBnk(self):
        """ Display Battery Description Input Form """
        self.define_toplevel('Battery Bank')
        self.frm = self.src.bnk.display_input_form(self.dsply)

    def dsplyAry(self):
        """ Display Solar Array Description Input Form """
        self.define_toplevel('Solar Array')
        self.frm = self.src.ary.display_input_form(self.dsply)
        
    def dsplyAltAry(self):
        """ Display the Alternate Solar Array Description Input Form """
        self.define_toplevel('Secondary Solar Array')
        self.frm = self.src.sec_ary.display_input_form(self.dsply)

    def dsplyPnls(self):
        """ Display Solar Panel Description Input Form """
        self.define_toplevel( 'Solar Panel')
        self.frm = self.src.pnl.display_input_form(self.dsply)

    def dsplyChg(self):
        """ Display Charge Controller Description Input Form """
        self.define_toplevel( 'Charge Controller')
        self.frm = self.src.chgc.display_input_form(self.dsply)

    def dsplyInvtrs(self):
        """ Display Inverter Description Input Form """
        self.define_toplevel('Inverter')
        self.frm = self.src.inv.display_input_form(self.dsply)

    def runSim(self):
        """ Execute a simulation Run """
        self.src.execute_simulation()

    def on_close(self):
        """ Clean up input on Input Form close"""
        self.frm.on_form_close()
        self.dsply.destroy()
        self.dsply = None

    def define_toplevel(self, func):
        """ Open pop up Input Form """
        if self.dsply is not None:
            self.dsply.destroy()           
        self.dsply = Toplevel()
        self.dsply.title('Define {0} Parameters'.format(func))
        self.dsply.protocol('WM_DELETE_WINDOW', self.on_close)
               

def main():    
    root = Tk()
    root.title("Base Frame Testing")
#    swb = spvSwitchboard(projRcd, [1,1], root, 'Solar PV System Description Menu')
    root.mainloop()


if __name__ == '__main__':
    main()
