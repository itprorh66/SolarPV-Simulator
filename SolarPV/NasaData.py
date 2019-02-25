#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 19:11:58 2018
Modified on 02/22/2019 for version 0.1.0

@author: Bob Hentz

-------------------------------------------------------------------------------
  Name:        NasaData.py
  Purpose:     Retrieve Site specific information from Nasa Power Site using https request
               protocol
               
            Sample SinglePoint Data Request: 
            https://asdc-arcgis.larc.nasa.gov/cgi-bin/power/v1beta/DataAccess.py?
            request=execute&identifier=SinglePoint&parameters=T2M,PS,
            ALLSKY_SFC_SW_DWN&
            startDate=20160301&endDate=20160331&
            userCommunity=SSE&tempAverage=DAILY&
            outputList=JSON,ASCII&lat=36&lon=45&user=anonymous

  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)

               This program is distributed WITHOUT ANY WARRANTY;
              without even the implied warranty of MERCHANTABILITY
              or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""
import numpy as np
import pandas as pd
import seaborn as sns
import scipy as syp
import statistics as stat
import requests
import datetime as dt
from dateutil.parser import parse
import matplotlib.pyplot as plt

""" BaseURL defines the NASA site used to retrieve Lat/Lon specific data """
BaseURL = 'https://power.larc.nasa.gov/cgi-bin/v1/DataAccess.py?'

def stripNaNs(ar):
    """ Strips out No Actual Number (NaN) values from an array """
    out = []
    for elm in ar:
        if np.isnan(elm) == False:
            out.append(elm)
    return out

def getLocationData(dtin):
    """ Retrieves the NASA Location data from the request response 
        Returns tuple of form (Lon, Lat' Elev)  """
    schval = 'coordinates\": ['
    stpt = dtin.find(schval)
    ndpt = dtin.find(']', stpt+len(schval))
    ln = []
    for itm in dtin[stpt+len(schval):ndpt].rstrip().split(','):
        ln.append(float(itm.strip('\n ')))
    return ln

def getOperationsdata(dtin, prm):
    """ Retrieves the NASA Location Atmospheric data for parameter 'parm'
        from the request response """   
    schval = prm +'\": {'
    stpt = dtin.find(schval)
    ndpt = dtin.find('}', stpt+len(schval))
    # Build an np Array
    ar = np.zeros([365,10])
    col = 0
    rw = 0
    for itm in dtin[stpt+len(schval):ndpt].rstrip().split(','):
        if itm.find(':') > 0:
            val = itm.strip('\n ').split(':')
            if val[0][5:-1] != '0229':
                try:
                    ar[rw][col] = float(val[1].rstrip())
                except:
                    print ('Error', val, 'Not numeric')
                if ar[rw][col] <=-900.0:
                    ar[rw][col] = np.NAN
                rw += 1
                if rw >=365:
                    rw = 0
                    col +=1
    #Build the Data Analysis Products
    dap = np.zeros([365,6])
    for row in range(365):
        offst = 0
        dap[row][0] = row+1
        vals = stripNaNs(ar[row])
        dap[row][1] = min(vals)
        dap[row][2] = max(vals)
        if dap[row][1] <= 0:
            offst = -dap[row][1]+1
            for i in range(len(vals)):
                vals[i] += offst
        dap[row][3] = stat.mean(vals) - offst
        dap[row][4] = stat.harmonic_mean(vals) - offst
        dap[row][5] = stat.stdev(vals)
    return pd.DataFrame(dap[0:,1:], dap[0:,0], ['Min','Max', 'S-Mean', 'H-Mean', 'STDEV'])
    
def graphData(df, p):
    """Create a graphical plot of data  """
    sdf = pd.DataFrame(df, columns=['Min','Max', 'S-Mean', 'H-Mean'])
    figTitle = p[1]
    sdf.plot( kind= 'Line', title=figTitle) 
    plt.show()
     
    
def getSiteElevation(lat, lon):
    baseURL = BaseURL
    baseReq = 'request=execute&identifier=SinglePoint&parameters=T2M'
    dateSel = dateSel = '&startDate=20140101&endDate=20140101&userCommunity=SSE'
    outSel = '&tempAverage=DAILY&outputList=JSON,ASCII&'
    locSel = 'lat={0}&lon={1}&user=anonymous'.format(lat, lon)
    cmd = baseURL + baseReq + dateSel + outSel + locSel
    # Request NASA Data from API
    try:
        data = requests.get(cmd).text
        return getLocationData(data)
    except requests.exceptions.ConnectionError:
        return [None, None, None]
    

def LoadNasaData(lat, lon, show= False, selectparms= None): 
    """ Execute a request from NASA API for 10 years of atmospheric data 
        required to prepare daily statistical data used in Solar Insolation
        calculations """
    baseURL = BaseURL
    baseReq = 'request=execute&identifier=SinglePoint&parameters='
    stdparms = [('T10M','Temperature @ 10m (c)'),
                ('T10M_MAX', 'Max Daily Temperature (c)'),
                ('T10M_MIN', 'Min Daily Temperature (c)'),
                ('WS10M','Surface Wind Speed (m/s)'),
                ('WS10M_MAX','Max Daily Wind Speed (m/s)'),
                ('WS10M_MIN','Min Daily Wind Speed (m/s)')]
                
    info_dict = dict()     #dictionary of Nasa data collected
    now = dt.date.today()
    baseyear = now.year-1
    startdate='{0}0101'.format(baseyear-9)
    enddate ='{0}1231'.format(baseyear)
    #  build request parameters
    if selectparms == None:
        parms = stdparms
    else:
        parms = []
        for itm in stdparms:
            if itm[0] in selectparms:
                parms.append(itm)
    reqparms = ''
    for p in range(len(parms)):
        if p > 0:
            reqparms += ','
        reqparms += parms[p][0]
        
    dateSel = '&startDate={0}&endDate={1}&userCommunity=SSE'.format(
            startdate, enddate)
    outSel = '&tempAverage=DAILY&outputList=JSON,ASCII&'
    locSel = 'lat={0}&lon={1}&user=anonymous'.format(lat, lon)
    cmd = baseURL + baseReq + reqparms + dateSel + outSel + locSel
    # Request NASA Data from API
    data = None
    try:
        data = requests.get(cmd).text
    except requests.exceptions.ConnectionError:
        print('Data Retrieval Error')
    if show:
        print ('Data for Location', info_dict['Location'])
    if data is not None:
        for p in parms:
            info_dict[p[0]] = getOperationsdata(data, p[0])
            if show:
                graphData(info_dict[p[0]], p)         
    return info_dict
    


def main():

#    find_parms = ['ALLSKY_SFC_SW_DWN', 'PS']
    d_dict = LoadNasaData(-0.2739, 36.3765, show = False) 
    tav = d_dict['T10M']['S-Mean'].values
    tmx = d_dict['T10M_MAX']['S-Mean'].values
    tmn = d_dict['T10M_MIN']['S-Mean'].values
    wav = d_dict['WS10M']['S-Mean'].values
    wmx = d_dict['WS10M_MAX']['S-Mean'].values
    wmn = d_dict['WS10M_MIN']['S-Mean'].values
    
    for i in range(10):
        st = 'Day: {0}\tAvg Temp: {1:.2f}\tMax Temp: {2:.2f}\tMin Temp: {3:.2f}\n'.format(i, tav[i], tmx[i], tmn[i])
        sw = '\tAvg WS: {0:.2f}\tMax WS: {1:.2f}\tMin WSp: {2:.2f}'.format(wav[i], wmx[i], wmn[i])
        st += sw
        print(st)


if __name__ == '__main__':
    main()    
