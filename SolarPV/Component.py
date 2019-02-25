#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 18 19:06:23 2018
Modified on 02/22/2019 for version 0.1.0

@author: Bob Hentz

-------------------------------------------------------------------------------
  Name:        Component.py
  Purpose:     Provides for the methods & data structures associated with
               Implementing a Subsystem/Component of a Solar PV System

  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)

               This program is distributed WITHOUT ANY WARRANTY;
               without even the implied warranty of MERCHANTABILITY
               or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""

class Component():
    
    def __init__(self, master, Component_Name, **kargs):
        self.master = master
        self.name = Component_Name
        self.args = None
        self.used_in = []
        self.parts = []
        self._define_attrbs()
        self._check_args(kargs)
        self.form = None 
        self.print_order = None

    def _define_attrbs(self):
        """ Overridden by each instantiation to define component attributes """
        raise NotImplementedError('Method not Implemented in Child Class')
     
    def _check_args(self, kargs):
        """ internal method to update descriptive arguments and detect illegal
            parameters.
            returns:
                True if parameters are valid
                False if an error occurred
       """         
        for ky in kargs.keys():
            if ky in self.args:
                self.args[ky].write_data(kargs[ky])
            else:
                em = '{0} does not support attribute {1}'.format(self.name, ky)
                raise AttributeError(em)
                return False
        return True

    def uses(self, new_part):
        """ assign sub-parts to this component """
        self.parts.append(new_part)
        new_part.set_assy(self)
    
    def get_parameters(self):
        """ Build dictionary of parameter values """
        parms= dict()
        for ky in self.args.keys():
            parms[ky] = self.read_attrb(ky)
        return parms
    
    def write_parameters(self, prm_dict):
        """ use prm_dict to set component attribute values """
        if prm_dict is not None:
            for ky in self.args.keys():
                self.args[ky] = prm_dict.pop(ky, self.read_attrb(ky))
    
    def set_assy(self, subsystem):
        """ add to list of components using this component """
        self.used_in.append(subsystem)
        
        
    def _attributes(self):
        """ Create a String containing self.args contents """
        s = '{0}\n'.format(self.name)
        cs = '\t'
        for ky in self.args.keys():
            ns = self.args[ky].__str__()
            if len(ns) + len(cs) > 30:
                s += cs + ns + '\n'
                cs = '\t'
            else:
                cs += ns +'\t'
        if len (cs) > 1:
            s += cs
        return s + '\n'

        
    def _parts_list(self):
        """ Create a parts list for this component """
        s = ''
        if len(self.parts) > 0:
            s += '\nComposed of units including:\n'
            for p in self.parts:
                s += p.__str__()
        return s

    def get_attrb_name(self, attrb):
        """ Return the name of the attribute """
        return self.get_attrb(attrb).get_name()
    
    def get_attrb(self, attr):
        """ Return Contents of Attribute defined by attr """
        if attr in self.args:
            return self.args[attr]
        em = '{0} does not support attribute {1}'.format(self.name, attr)
        raise AttributeError(em)
    
    def read_attrb(self, attr):
        """ Read data for selected attribute """
        return self.get_attrb(attr).read_data()
    
    def part_assigned(self):
        """ Get list of parts assigned to this component """
        return len(self.parts) > 0
    
    def set_attribute(self, attr, val):
        """ Set Contents of Attribute defined by attr to val
            Return True if value set, else False   """
        if attr in self.args:
            self.args[attr].write_data(val)
            return True
        em = '{0} does not support attribute {1}'.format(self.name, attr)
        raise AttributeError(em)
        return False

    def check_arg_definition(self):
        """ Unique to each Component """
        """ Verifies the component has been properly defined """
        raise NotImplementedError('Method not Implemented in Child Class')

    def update_attributes(self): 
        """ Unique to each Component """
        """ Updates the attributes of this component based on a change """
        raise NotImplementedError('Method not Implemented in Child Class')

    def report_error(self, msg, level, error_class):
        """ generate Error Report """
        if self.master.stw is None:
            if error_class is None:
                print('{0} Error: {1}'.format(level, msg))
            else:
                raise error_class(msg)
        else:
            self.master.stw.show_message(msg, level)

    def is_defined(self):
        """ Checks if Component is defined """
        rslt, msg = self.check_arg_definition() 
        return rslt
                
    def check_definition(self):
        """ Check Component Definition and if rslt is False
            Report in status window if identified else raise a 
            Python Attribute Error 
            return rslt """
        rslt, msg = self.check_arg_definition() 
        if not rslt:
            self.report_error(msg, "Fatal", AttributeError )
        return rslt

    def display_input_form(self, parent_frame):
        """ Unique to each Component """
        """ Display the data entry form for this component """
        return self.form

    def on_form_change(self, attrb, val):
        """ Update attributes on current form and any dependent components """
        if attrb in self.args:
            self.set_attribute( attrb, val)
            self.perform_unique_updates(attrb, val)
            for itm in self.used_in:
                itm.update_attributes()
        
    def perform_unique_updates(self, attrib, val):
        """ Unique to each Component """
        pass
            
    def __str__(self):
        """ Create a string containing Component Description """
        s = self._attributes()
        s += self._parts_list()
        return s        
 
def main():
     pass

        
    
    


if __name__ == '__main__':
    main()               
    