#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 22 12:59:16 2018

@author: Bob Hentz

-------------------------------------------------------------------------------
  Name:        FormBuilder.py
  Purpose:     Provides for the methods & data structures associated with
               Defining the atributes of a Solar PV System

  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)

               This program is distributed WITHOUT ANY WARRANTY;
               without even the implied warranty of MERCHANTABILITY
               or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""

from tkinter import *
import tkinter.ttk as ttk
from FieldClasses import *


class DataForm(ttk.Frame):
    
    def __init__(self, parent, data_src, **kw):
        self.parent = parent
        self.src = data_src
        self.wdg_dict = dict()
        self.form_close = kw.pop("Formclose", None)
        frargs, gdargs = build_args(kw)
        ttk.Frame.__init__(self, self.parent, **frargs)
        self.grid(**gdargs)
        self.define_layout()
#        self.make_widgets()
 
    def define_layout(self):
        pass
        
    def make_widgets(self):
        for itm in range(len(self.layout)):
            self.wdg_dict[itm[0]] = itm[1]
 
    def create_text(self, **kw):
        lkw, gkw = build_args(kw)
        txt = ttk.Label(self, **lkw)
        txt.grid(gkw)
       
    def create_label(self, data_obj, **kw):
        kw['text'] = data_obj.get_label()
        lkw, gkw = build_args(kw)
        lbl = ttk.Label(self, **lkw)
        lbl.grid(**gkw)
        return lbl
     
    def create_space(self, sze, **kw):
        kw['text']  = ' '*sze      
        spc = self.create_text(**kw)
        return spc
    
    def create_entry(self, data_obj, **kw):
        dc = data_cell(self, data_obj, **kw)
        return dc

    def create_dropdown(self, data_obj, **kw):
        lc = list_cell(self, data_obj, **kw)
        return lc
                
    def create_option_selector(self, rw, col, data_obj, **osargs):
        pass
                
    def on_form_change(self, attrb, val):
        pass

        
    def on_form_close(self):
        for ky in self.wdg_dict.keys():
            if ky in self.src.args:
                self.src.args[ky].write_data(self.wdg_dict[ky].get_val())
        if self.form_close is not None:
            self.form_close()
            
        
        
def main():
    print ('FormBuilder Startup check')
    
    
if __name__ == '__main__':
    main()