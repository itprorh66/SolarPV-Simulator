#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 19:17:27 2018
Modified   Sat Dec  1 2018 (fix save/import issue)
Modified   Tue Dec  4 2018 (fix Load Import Error Issue #11)
Modified on 02/22/2019 for version 0.1.0
Modified on 04/11/2021 to address Issues #10, 12, & 13 related to improving 
            Site Load Definition performance and ease of use

@author: Bob Hentz

-------------------------------------------------------------------------------
  Name:        DataFrame.py
  Purpose:     Provide General Methods for creating, editing, adding,
                 viewing & saving Pandas DataFrame structures

  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)

               This program is distributed WITHOUT ANY WARRANTY;
              without even the implied warranty of MERCHANTABILITY
              or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""

import pandas as pd


class DataFrame:
    """ Methods for manipulating Pandas dataFrame structures """
    def __init__(self, col_hds, col_typs):
        assert len(col_hds) == len(col_typs)
        self.col_hds = col_hds
        self.col_typs = col_typs
        self.df = pd.DataFrame(None, None, self.col_hds)

    def add_new_row(self, rw_vals):
        """ Add new row to DataFrame and coerce entries to correct type """
        assert len(rw_vals) == len(self.col_hds), 'Len rw_vals = {0}, Len Col Hds = {1}'.format(len(rw_vals), len(self.col_hds))
        ind = dict()
        for itm in enumerate(self.col_hds):
            if rw_vals[itm[0]] == None or rw_vals[itm[0]] == "":
                ind[itm[1]] = ""
            else:
                ind[itm[1]] = self.col_typs[itm[0]](rw_vals[itm[0]])
        self.df = self.df.append(ind, True)

    def delete_row(self, rwid):
        """ Delete a row from the dataframe """
        assert rwid < self.df.shape[0]
        self.df.drop(self.df.index[rwid], inplace=True)
        
    def set_cell_value(self, pos, val):
        """ Update a DataFrame cell value pos = [row,col]  """
        sh = self.df.shape
        row = pos[0]
        col = pos[1]
        if row < sh[0] and pos[1] < sh[1]:
            if val == "":
                self.df.at[row, self.col_hds[col]] = val
            else:
                self.df.at[row, self.col_hds[col]] = self.col_typs[col](val)
            return True
        return False

    def update_row_values(self, rwid, val_list):
        """ Update the contents of the frame row  """
        assert rwid < self.df.shape[0]
        for colid, val in enumerate(val_list):
            self.set_cell_value([rwid, colid], val)
        


    def get_row_count(self):
        """ Return the row size of the DataFrame """
        return self.df.shape[0]

    def get_shape(self):
        """ Returns tuple of (Rows, Columns) in data frame"""
        return self.df.shape

    def get_dataframe(self):
        """ Return the DataFrame """
        return self.df

    def get_row_by_index(self, i):
        """ Return the ith row of the DataFrame """
        if i < self.get_row_count():
            return list(self.df.iloc[i].values)
        return []

    def drop_row_by_index(self, i):
        """ Update DataFrame by Dropping the row at specified index """
        self.df.drop(self.df.index[i], inplace=True)

    def get_headers(self):
        """ Return a list of Column Headings """
        return self.col_hds

    def get_col_types(self):
        """ Return the list of dataframe value types"""
        return self.col_typs

    def get_col_indx(self, col_hd):
        """ If col_hd is a valid Column Label return the column index
            else: return -1"""
        try:
            return self.col_hds.index(col_hd)
        except:
            return -1

    def purge_frame(self):
        """ Clear existing load definition data from the underlying DataFrame"""
        self.df = pd.DataFrame(None, None, self.col_hds)

    def export_frame(self):
        """ create a dict of DataFrame contents keyed to Rows
            used to save the dataframe contents but not the class code"""
        return self.df.to_dict('Index')

    def import_frame(self, dfInput):
        """ Rebuild  DataFrame contents from imported data"""

        rws = list(dfInput.keys())
        rws.sort()
        for rw in rws:
            rwDict = dfInput[rw]
            ar = []
            for i in range(len(self.col_hds)):
                dfval = None
                if self.col_typs[i] is str:
                    dfval = ""
                elif self.col_typs[i] is int:
                    dfval = 0
                else:
                    dfval = 0.0
                ar.append(rwDict.pop(self.col_hds[i], dfval))
            self.add_new_row(ar)


    def __str__(self):
        """ Create printable version of Load Profile """
        rows = self.get_row_count()
        s = ""
        for indx in range(len(self.col_hds)-1):
            s += '{0: >20}\t'.format(self.col_hds[indx])
        for r in range(rows):
            rw = self.get_row_by_index(r)
            if rw[0] != '':
                s += '\n'
                for c in range(len(rw)-1):
                    s += '{0: >20}\t'.format(rw[c])
        return s



""" This is Main"""
def main():
    pass


if __name__ == '__main__':
    main()
