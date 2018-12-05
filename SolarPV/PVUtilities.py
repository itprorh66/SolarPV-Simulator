#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 11 09:37:49 2018
Modified on 11/27/2018 to clean up comments
Modified   Wed Dec  5 2018 (Fix Issue 2, Handle DC Loads)

@author: Bob Hentz
-------------------------------------------------------------------------------
  Name:        PVUtilities.py
  Purpose:     Define utilities found useful in building PV System Simulator               
  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)
               This program is distributed WITHOUT ANY WARRANTY;
               without even the implied warranty of MERCHANTABILITY
               or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""
import numpy as np
import math
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os.path
import pickle
import requests
import csv
from urllib.request import urlopen
from pvlib.irradiance import total_irrad


def dfcell_is_empty(cell_value):
    """ Return True if Dataframe cell contains NaN """
    return np.isnan(cell_value)

def entry_is_empty(data):
    """ Tests for a null data field  """
    if data == None or data == "":
        return True
    return False

def eval_dfcell(cell_value):
    """ Returns None if cell is NaN else, the value """
    if dfcell_is_empty(cell_value):
        return None
    return cell_value

def convert_string_to_hrs(info):
    """ Returns the Hour component of a time string """
    st = info.find('T')+1
    tlist = info[st:].split(':')
    h = 0.0
    h += float(tlist[0])
    h += float(tlist[1])/60
    h += float(tlist[2])/3600
    return h

def convert_to_dec_hrs(time):    
    """ Returns the decimal Hour for a time string of form HH:MM:SS.xxx """
    h= time.hour*1.0
    h += time.minute/60.0
    h += time.second/3600.0
    return h

def month_timestamp(ts):
    """ Produces an Numpy Array of the Integer Month
        from a Panda DateTimeIndex Series """
    k = list()
    for t in ts:
        k.append(t.month)
    return np.array(k)

def doy_timestamp(ts):
    """ Produces an Numpy Array of the Integer Day Of Year
        from a Panda DateTimeIndex Series """
    k = list()
    for t in ts:
        k.append(t.dayofyear)
    return np.array(k)

def dom_timestamp(ts):
    """ Produces an Numpy Array of the Integer Day Of Month
        from a Panda DateTimeIndex Series """
    k = list()
    mon = -1
    doy = -1
    dom = 0
    for t in ts:
        m = t.month
        if mon != m:
            dom = 1
            doy = t.dayofyear
            mon = m
        elif t.dayofyear != doy:
            dom += 1
            doy = t.dayofyear
        k.append(dom)
    return np.array(k)


def hourly_load(times, load):
    """ Create a Data Frame of Hourly Load in Watts"""
    lngth = len(times)
    hlc = np.zeros((lngth, 3))
    for i in range(lngth):
        hlc[i, 0] = load['AC'].iloc[i%24]
        hlc[i, 1] = load['DC'].iloc[i%24]
        hlc[i, 2] = load['Total'].iloc[i%24]
    return pd.DataFrame(data=hlc, index=times, 
                        columns=['AC_Load', 'DC_Load', 'Total_Load'])

def create_time_mask(time_val, adjust=None):
    """ Create a Pandas Timestamp defined by
        time_val, Adjust to nearest hour beased on value of adjust.
    """
    strMask= '{0}-{1:02}-{2:02} {3:02}:00:00{4:+03}'
    rslt = [time_val.year, time_val.month, 
            time_val.day, time_val.hour, 
            int(str(time_val.utcoffset()).split(':')[0])]    
    if adjust is not None:
        mn = time_val.minute
        if adjust == "Lead":
            if mn > 30:
                rslt[3] += 1
        else:
            if mn < 30:
                rslt[3] -= 1
    rstr = strMask.format(rslt[0], rslt[1], rslt[2], rslt[3], rslt[4])
    return pd.to_datetime(rstr)                
        
        
def hourly_temp(avT, maxT, minT, cur_t, rise_t, set_t, trans_t, offset= 2):
    """ Estimate hourly temperature for cur_t of day
        assumes, temp follows sine curve, with max temp at
        solar noon plus offset (typically 2hrs)  """
    ct = convert_string_to_hrs(cur_t)
    sunrise = convert_to_dec_hrs(rise_t)
    sunset = convert_to_dec_hrs(set_t)
    dur = convert_to_dec_hrs(set_t)
    pkhr = sunrise + 0.5*dur + offset
    d_tmp = maxT - minT
    z = avT + d_tmp*math.sin(2*np.pi*((ct-pkhr)/24))
    return z
                              
def hourly_speed(avS, maxS, minS, cur_t, rise_t, set_t, trans_t, offset= 2):
    """ Estimate hourly temperature for cur_t of day
        assumes, temp follows sine curve, with max temp at
        solar noon plus offset (typically 2hrs)  """ 
    ct = convert_string_to_hrs(cur_t)
    sunrise = convert_to_dec_hrs(rise_t)
    sunset = convert_to_dec_hrs(set_t)
    dur = convert_to_dec_hrs(set_t)
    pkhr = sunrise + 0.5*dur + offset
    d_spd = (maxS - minS) 
    return abs(avS - d_spd*math.sin(2*np.pi*(ct-pkhr)/24))
   
    
def read_resource(filename, dirptr):
    """ Method to retrieve data from the resources csv file and generate a 
        Panadas Dataframe of the contents """
    fn = os.path.join(dirptr, filename)
    return pd.read_csv(fn, index_col=0, skiprows=[1,2])
    

def read_web_resource(url, dirptr, filename):
    """  Method to retireve data from web url and create a file
         with filename within the designated dirptr  """
    fp = os.path.join(dirptr, filename)
    try:
        response = urlopen(url)
        cr = csv.reader(response.read().decode('utf-8'))
        return True
    except requests.exceptions.ConnectionError:
        return False

def build_monthly_performance_info(df, parm):
    dom = [None]*13
    curday = 0
    for ri in range(len(df)):
        row = df.iloc[ri]
        val = row[parm]
        mn = int(row['Month'])
        dm = int(row['DayofMonth'])
        if dom[mn] is None:
            dom[mn] = [mn, val]
        else:
            if len(dom[mn]) <= dm:
                dom[mn].append(val)
            else:
                dom[mn][dm] += val
    months = np.arange(1,13)
    total = np.zeros(12)
    avg = np.zeros(12)
    bestday = np.zeros(12)
    bestval = np.zeros(12)
    worstday = np.zeros(12)
    worstval = np.zeros(12)
    for i in range(len(months)):
        bv = -1.0
        wv = 100000000.0
        m = months[i]
        if dom[m] is not None:
            curmon = dom[m]
            days = len(dom[m][1:])
            for day in range(1, days+1):
                vals = dom[m]
                curval = vals[day]
                total[i] += curval
                if curval < wv:
                    worstval[i] = curval
                    wv = curval
                    worstday = day
                if curval > bv:
                    bestval[i] = curval
                    bv = curval
                    bestday = day
            avg[i] = total[i]/(days*1.0)
    df = pd.DataFrame({'Total Power':total, 'Avg Power':avg, 
                       'Best Power':bestval, 'Best Day': bestday, 
                       'Worst Power':worstval, 'Worst Day': worstday},
                       index= months) 
    df.index.name = 'Month'
    return df
   
def find_worst_day(df):
    """ return the worst performance day from the timestamp indexed dataframe """
    min_power = np.min(np.array(df['Worst Power']))
    minP_day = df[df['Worst Power'] == min_power]
    dom = minP_day['Worst Day'].values[0].astype(int)
    mnth = minP_day.index.values[0].astype(int)
    return mnth, dom
    

def find_best_day(df):
    """ return the best performance day from the timestamp indexed dataframe """
    max_power = np.max(np.array(df['Best Power']))
    maxP_day = df[df['Best Power'] == max_power]
    dom = maxP_day['Best Day'].values[0].astype(int)
    mnth = maxP_day.index.values[0].astype(int)
    return mnth, dom
    

def build_overview_report(mdl):
    """ Create a formated overview of Project Design data """
    s = 'Overview Report for Project {0}'.format( 
            mdl.site.read_attrb('proj'))
    s +='\n\n\tDescription: '.format(
            mdl.site.read_attrb('p_desc'))
    s +='\n\t\tClient: {0}\tCity: {1}\tCountry: {2}'.format(
            mdl.site.read_attrb('client'),
            mdl.site.read_attrb('city'), 
            mdl.site.read_attrb('cntry'))
    s +='\n\t\tLat: {0},\tLon: {1},\tElev: {2}'.format(
            mdl.site.read_attrb('lat'),
            mdl.site.read_attrb('lon'), 
            mdl.site.read_attrb('elev'))
    elp = mdl.load.get_load_profile()
    sum_elp = sum(elp)
    if sum_elp > 0:
       s += '\n\n\tUser Load Description' 
       s +='\n\t\tDaily Load = {0} KWatts\t Peak Hourly Load = {1} KWatts'.format(sum_elp/1000, max(elp)/1000)
    
    if mdl.bat.read_attrb('b_mfg') is not "":
        s += '\n\n\tBattery Specification'
        s += '\n\t\tMFG: {0},\t Model: {1}'.format( 
                   mdl.bat.read_attrb('b_mfg'),
                   mdl.bat.read_attrb('b_mdl'))
        s += '\n\t\tDescription: {0}'.format( 
                   mdl.bat.read_attrb('b_desc'))
        s += '\n\t\tType: {0}, \tVnom: {1} volts, \tInternal Resistance: {2} Ohms'.format(
                    mdl.bat.read_attrb('b_typ'),
                    mdl.bat.read_attrb('b_nomv'),
                    mdl.bat.read_attrb('b_ir'))
        s += '\n\t\tRated Capacity: {0} Amp-Hrs,\tHour Basis for Rating: {1} Hrs'.format(
                    mdl.bat.read_attrb('b_rcap'),
                    mdl.bat.read_attrb('b_rhrs'))
        s += '\n\t\tRated temperature: {0} C,\tTemp Coeficient: {1}/C'.format(
                    mdl.bat.read_attrb('b_stdTemp'),
                    mdl.bat.read_attrb('b_tmpc'))
        s += '\n\t\tMax No. of Discharge Cycles: {0},\tDepth of Discharge for Lifecycle: {1}%'.format(
                    mdl.bat.read_attrb('b_mxDschg'),
                    mdl.bat.read_attrb('b_mxDoD'))
        s += '\n\n\tBank Specification'
        s += '\n\t\tDOA: {0}, \tDOD: {1}%'.format(
                    mdl.bnk.read_attrb('doa'),
                    mdl.bnk.read_attrb('doc'))
        s += '\n\t\tUnits in Series: {0}, \tStrings in Parallel: {1}'.format(
                    mdl.bnk.read_attrb('bnk_uis'),
                    mdl.bnk.read_attrb('bnk_sip'))
    if mdl.pnl.read_attrb('Name') is not '':
        s += '\n\n\tSolar Panel Specification'
        s += '\n\t\tMFG: {0},\t Model: {1}'.format( 
                   mdl.pnl.read_attrb('m_mfg'),
                   mdl.pnl.read_attrb('m_mdl'))
        s += '\n\t\tDescription: {0}'.format( 
                   mdl.pnl.read_attrb('Name'))
        s += '\n\t\tType: {0}, \tV(mp): {1} volts, \tI(mp): {2} Amps'.format(
                    mdl.pnl.read_attrb('Technology'),
                    mdl.pnl.read_attrb('V_mp_ref'),
                    mdl.pnl.read_attrb('I_mp_ref'))
        s += '\n\n\tSolar Array Specification'
        s += '\n\t\tTilt: {0} Degrees, \tAzimuth: {1} Degrees'.format(
                    mdl.ary.read_attrb('tilt'),
                    mdl.ary.read_attrb('azimuth'))
        s += '\n\t\tMounting Config: {0}'.format(mdl.ary.read_attrb('mtg_cnfg'))

        s += '\n\t\tSpace under Panel: {0} cm, \tMounting Height: {1} m'.format(
                    mdl.ary.read_attrb('mtg_spc'),
                    mdl.ary.read_attrb('mtg_hgt'))
        s += '\n\t\tGround Surface Condition: {0}'.format(mdl.ary.read_attrb('gnd_cnd'))
        s += '\n\t\tUnits in Series: {0}, \tStrings in Parallel: {1}'.format(
                    mdl.ary.read_attrb('uis'),
                    mdl.ary.read_attrb('sip'))
    if mdl.inv.read_attrb('Name') is not '':
        s += '\n\n\tInverter Specification'
        s += '\n\t\tMFG: {0},\t Model: {1}'.format( 
                   mdl.inv.read_attrb('i_mfg'),
                   mdl.inv.read_attrb('i_mdl'))
        s += '\n\t\tDescription: {0}'.format( 
                   mdl.inv.read_attrb('Name'))        
    return s

          
def dataframe_selection_to_dict(df, sel_itm):
    """ Return a Dict for  DF Frame row defined by sel_itm index """
    dd = {'Name':sel_itm}
    sdf = df.loc[sel_itm]
    for id in sdf.index.values:
        dd[id] = sdf[id]
    return dd
            
def process_inverters_csv(drcty):
    """ Separate out MFG from model and append these columns to base data 
        frame """        
    dp = os.path.join(os.getcwd(), drcty)
    fp = os.path.join(dp, 'CEC Inverters.csv')
    df = pd.read_csv(fp, index_col=0, skiprows=[1,2])
    names = list(df.index.values)
    mfgs = list()
    models = list()
    for nm in names:
        k = nm.split(":")
        mfgs.append(k[0].strip())
        models.append(k[1].strip())
    df['Manufacturer'] = pd.Series(np.array(mfgs), index=df.index)
    df['Model'] = pd.Series(np.array(models), index=df.index)
    return df
     
def locate_mfg_split(val):
    """Identify the split between Module Manufaturer and Model Number
       The CEC data is not clearly deliniated between Model Number & Mfg,
       so do the best you can.  The rest is up to the user to sort out,
       when selecting a product.
    """
    schvals = [ 'REC Solar ', 'Photronic ', 'Science & Technology ', ') ', 'USA ', 'Holdings ', 
               'Holding ', 'Frontier ', ' Liberty ', 'Industries ', 'Hong Kong ', 
               'Q CELLS ', 'Q-Cells', 'nologies ',  'Semiconductor ', 'Wind ','CO ', 'Singapore ', 
                'o. ', 'ogy ', 'ies ', 'ade ', 'ble ','ms ', 'nal ','ing ',
                'rgy ', 'Ontario ', 'Korea ', 'are ', 'Universal ', 'nt ', 
               'da ', 'wer ', 'da ', 'eed ', 'le ', 'ry ', 'ica ','rik ',
               'ue ', 'cis ', 'ech ', 'ics ', 'EC ', 'Solar ', 'ar ', 'oy ', 
               'ek ', 'BIPV ', 'den ', 'enn ', 'any ', 'tts ', 'nal ', 'eed', 
               'sis ', 'psun ', 'ght ', 'ASOL ', 'SEG PV ', 'son ', 'rray ', 'iva ',
               'Inc. ', 'eme ', 'evo ', 'fab ', 'ray ', 'ity ', 'orld ', 'bine ',
               'nnel ', 'ria ', 'max ', 'ace ', 'tec ', 'iosun ', 'gees ', 'llo ', 'ion ',
               'gsu ', 'tric ', 'com ', 'umos ', 'uxco ', 'voltaic ', 'ICOR ', 'Sun ', 'iene ',
               'fersa ', 'oton ', 'SPV ', 'eka ', 'Won ', 'eta ', 'MAR ', 'nix ', 'ital ', 'arp ',
               'ick ', 'SDI ', 'oup ', 'BHD ',  'att ', 'olt ', ' '
             ]
    while True:
        for sc in schvals:
            if val.find(sc) > 0:
                found = True
                return val.find(sc) + len(sc)
        print ('No Match for', val)
        return -1

                  
def process_modules_csv(drcty):
    """ Separate out MFG from model and append these columns to base data 
        frame """
    dp = os.path.join(os.getcwd(), drcty)
    fp = os.path.join(dp, 'CEC Modules.csv')
    df = pd.read_csv(fp, index_col=0, skiprows=[1,2])
    names = list(df.index.values)
    mfgs = list()
    models = list()
    for nm in names:
        ptr = locate_mfg_split(nm)
        if ptr > 0:
            mfgs.append(nm[0:ptr].strip())
            models.append(nm[ptr:].strip())
        else:
            mfgs.append(nm)
            models.append(nm)
    df['Manufacturer'] = pd.Series(np.array(mfgs), index=df.index)
    df['Model'] = pd.Series(np.array(models), index=df.index)
    return df    

def import_new_resource(file_type ):
    dpo = os.path.join(os.getcwd(), 'Resources')
    dpi = os.path.join(os.getcwd(), 'Raw-Input')
    if file_type is 'Modules':
        df = process_modules_csv(dpi)
        df.to_csv(os.path.join(dpo, 'CEC Modules.csv'))
    else:    
        df = process_inverters_csv(dpi)
        df.to_csv(os.path.join(dpo, 'CEC Inverters.csv'))
    
  
def main():
    pass

if __name__ == '__main__':
    main()    

