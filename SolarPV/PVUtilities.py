#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 11 09:37:49 2018
Modified on 11/27/2018 to clean up comments
Modified   Wed Dec  5 2018 (Fix Issue 2, Handle DC Loads)
Modified on 02/25/2019 for version 0.1.0
Modified on Wed 01/20/2021 to add computeOutputResults

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
import os.path
import requests
import csv
from urllib.request import urlopen
from datetime import date



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

def create_time_indices(tm_z):
    """ Create Base Dataframe indicies for use in running simulations """
    now = date.today()
    baseyear = now.year-2
    if baseyear%4 == 0:
        # Don't use leap year
        baseyear -= 1
    st = '{0}0101T0000{1:+}'.format(baseyear, tm_z)
    nt = '{0}1231T2300{1:+}'.format(baseyear, tm_z)
    times = pd.date_range(start= st,
                             end= nt,
                             freq='H')

    months = month_timestamp(times).astype(int)
    days_of_year = doy_timestamp(times).astype(int)
    days_of_month = dom_timestamp(times).astype(int)
    timedf = pd.DataFrame({'Month':months,
                             'DayofYear': days_of_year,
                             'DayofMonth': days_of_month},
                        index = times)

    return timedf

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

def build_monthly_summary(df, select_value):
    """ Summarizes df contents for select_value parameter
        over an entire year """    
    month_list = np.array(['Jan', 'Feb', 'Mar', 'Apr',
                           'May', 'Jun', 'Jul', 'Aug',
                           'Sep', 'Oct', 'Nov', 'Dec'])
    dat_list = np.zeros([12,5])
    for indx in range(12):
        smpl_df = df.loc[df['Month'] == indx+1]
        vals = smpl_df[select_value].groupby(smpl_df['DayofMonth']).sum()
        dat_list[indx][0] = vals.sum()
        dat_list[indx][1] = vals.mean()
        dat_list[indx][2] = vals.max()
        dat_list[indx][3] = vals.min()
        dat_list[indx][4] = len(smpl_df)/24
    rslt = pd.DataFrame(dat_list, month_list, 
                        columns=['Total {0}'.format(select_value), 
                                 'Avg {0}'.format(select_value), 
                                 'Best {0}'.format(select_value), 
                                 'Worst {0}'.format(select_value),
                                 'Days' ])
    rslt.index.name= 'Months'
    return rslt


def build_monthly_performance(df, param):
    """ Using the dataframe df create Monthly Synopsis of
        system performance  for selected param 
        return 3 part tuple containing:
            resulting array, 
            best day designator,
            worst day designator
    """
    rslt = []    
    rslt.append( build_monthly_summary(df, param))
    rslt.append( find_best_doy(df, param))
    rslt.append( find_worst_doy(df, param))
    return rslt

def find_worst_doy(df, select_value):
    """ returns a day_of_year where select_value is a minimum """
    rslt_df = df[select_value].groupby(df['DayofYear']).sum()
    mn = rslt_df.min()
    for indx in range(len(rslt_df)):
        if rslt_df.iloc[indx] == mn:
            return indx + 1
    raise IndexError('No worst day value found')
    
def find_best_doy(df, select_value):
    """ returns a day_of_year where select_value is a maximum """
    rslt_df = df[select_value].groupby(df['DayofYear']).sum()
    mx = rslt_df.max()
    for indx in range(len(rslt_df)):
        if rslt_df.iloc[indx] == mx:
            return indx + 1
    raise IndexError('No best day value found')
   
def computOutputResults(attrb_dict,  ArP, ArV, ArI, acLd, dcLd, wkDict):
    """Computes the controlled Voltage & current output used to either power
       the load or charge/discharge a battery bank. Updates the
       battery bank and contents of wkDict based on results of computations"""
       
    """## attrb_dict Contains the following elements:  ###
      'Bnk' - PVBattery Instance
      'Inv' - PVInverter Instance
      'Chg' - PVChgController Instance    
    """
    
    if attrb_dict['Inv'] != None and attrb_dict['Inv'].is_defined():
        invFlg = True
    else:
        invFlg = False
    if attrb_dict['Bnk'] != None and attrb_dict['Bnk'].is_defined():
        bnkFlg = True
    else:
        bnkFlg = False
    if attrb_dict['Chg'] != None and attrb_dict['Chg'].is_defined():
        chgFlg = True
    else:
        chgFlg = False
    
    if not chgFlg and not invFlg:
    # No Charge Controller or Inverter in System
        if dcLd > 0.0 and ArP >0.0:
            # Load to service
            if ArP > dcLd:
                wkDict['PO'] = dcLd
            else:
                wkDict['PO'] = ArP
            wkDict['DE'] = wkDict['PO']/ArP
            wkDict['PS'] = wkDict['PO']/dcLd
    else:    
        #InternalFunction Variables:
        internal_parm = {
                          'stdbyPwr':    (attrb_dict['Inv'].read_attrb('Pnt') if invFlg else 0 +                                       #power draw for cntrlr/inverter units
                                          attrb_dict['Chg'].read_attrb('c_cnsmpt') if chgFlg else 0),        
                          'eff':      min([(attrb_dict['Inv'].read_attrb('Paco')/attrb_dict['Inv'].read_attrb('Pdco')) if invFlg else 1.0,  
                                          (attrb_dict['Chg'].read_attrb('c_eff')/100) if chgFlg else 1.0]),                                   #power conversion efficiency  
                          'pvmxv':    attrb_dict['Inv'].read_attrb('Vdcmax') if invFlg else attrb_dict['Chg'].read_attrb('c_pvmxv'),         #maximum PV Voltage
                          'pvmxi':    ((attrb_dict['Inv'].read_attrb('Pdco')/attrb_dict['Inv'].read_attrb('Vdco')) if invFlg 
                                        else attrb_dict['Chg'].read_attrb('c_pvmxi')),                                                    #maximum PV Current
                          'VmxChg':   attrb_dict['Inv'].read_attrb('Vdcmax') if invFlg else attrb_dict['Chg'].read_attrb('c_mvchg'),        #Maximum Charge Voltage
                          'ImxDchg':  attrb_dict['Inv'].read_attrb('Idcmax') if invFlg else attrb_dict['Chg'].read_attrb('c_midschg'),       #Maximum Discharge Current
                          'cntlType': attrb_dict['Chg'].read_attrb('c_type') if chgFlg else 'MPPT'                                          #Controller Type either MPPT or PWM
        }
         
                
        sysLd = internal_parm['stdbyPwr']
        totUsrLd = dcLd + acLd
        if invFlg:
            sysLd += attrb_dict['Inv'].compute_dc_power(acLd)
        sysLd = ((totUsrLd + sysLd)/internal_parm['eff']) - totUsrLd
        pload = totUsrLd + sysLd
        vout = min(ArV, internal_parm['pvmxv'])
        iout = min(ArI, internal_parm['pvmxi'])
        drain = ArP - pload*1.1
        #Test for Batbank and either charge state or ability to discharge
        if bnkFlg and (drain >= 0 or (drain <0 and  attrb_dict['Bnk'].is_okay())):
            # A battery bank exists and it is usable for charging or discharging
            bv =  attrb_dict['Bnk'].get_volts()
            if bv <= 0:
                bv = 1
            if drain >= 0:
                vout = min(vout, internal_parm['VmxChg'])
                bv = bv*1.2
                if internal_parm['cntlType']  == 'MPPT':
                    iout = max(drain/vout, drain/bv)                                       
                else:                   
                    iout = min(drain/vout, drain/bv)
    
            else:
                # Discharge Battery state
                if abs(drain) <= attrb_dict['Bnk'].current_power():
                    if vout == 0.0 or iout == 0.0:
                        vout = bv
                        iout = min(internal_parm['ImxDchg'], -drain/vout)
                    iout= -1* iout
                else:
                    # Bnk can't provide needed power
                    if ArP < sysLd:
                        msg = 'Insufficient Array & Bank power to sustain System operation'
                        msg += '\n {0:.2f} watts needed but only {1:.2f} watts generated'
                        wkDict['Error'] = (msg.format(sysLd, ArP), 'Warning')
                    else:
                        iout = -1 * ((ArP-sysLd)/vout)
            #update Bank State
            attrb_dict['Bnk'].update_soc(iout, wkDict)
            if ArP - wkDict['BD'] -pload >= 0.0:
                #okay met pload requirements
                wkDict['PO'] = pload
            elif ArP - wkDict['BD'] - sysLd >= 0:
                wkDict['PO'] = ArP - sysLd
            else:
                msg = 'Insufficient Array + Bank power to sustain System operation'
                msg += '\n {0:.2f} watts needed but only {1:.2f} watts generated'
                wkDict['Error'] = (msg.format(sysLd, ArP), 'Warning')
                wkDict['PO'] = 0.0                               
            if totUsrLd > 0: 
                wkDict['PS'] = wkDict['PO']/pload              
            if ArP > 0:
                wkDict['DE'] = wkDict['PO'] /ArP     
        else:
            # No battery exists or battery can't be discharged further
            if ArP < sysLd and totUsrLd > 0:
                msg = 'Insufficient Array power to sustain System operation'
                msg += '\n {0:.2f} watts needed but only {1:.2f} watts available' 
                wkDict['Error'] = (msg.format(sysLd, ArP), 'Warning')
            vout = min(vout, internal_parm['VmxChg'])
            iout = min(iout, internal_parm['ImxDchg'])
            if internal_parm['cntlType'] == 'MPPT':
                iout = max(iout, internal_parm['ImxDchg'])
            pout = min(ArP, vout*iout, pload)
            if ArP > 0 and totUsrLd > 0:
                wkDict['PO'] = pout
                wkDict['DE'] = wkDict['PO']/ArP
            if ArP > pload and totUsrLd > 0:
                wkDict['PS'] = pout/pload



def build_overview_report(mdl):
    """ Create a formated overview of Project Design data """
    s = 'Overview Report for Project {0}'.format( 
            mdl.site.read_attrb('proj'))
    s +='\n\n\tDescription: {0}'.format(
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
    sum_elp = sum(elp['Total'])
    if sum_elp > 0:
       s += '\n\n\tUser Load Description\n'
       pls = '\nPeak Hourly Load KW: Total= {0:4.2f},\tAC= {1:4.2f},\tDC= {2:4.2f}'
       s += pls.format(max(elp['Total'])/1000, max(elp['AC'])/1000, 
                            max(elp['DC'])/1000)
    if mdl.pnl.is_defined():
        for i in range(len(mdl.array_list)):
            if mdl.array_list[i].is_defined():
                s += '\nArray {0}\n'.format(i+1)
                s += '\t' + str(mdl.array_list[i])

    if mdl.bat.is_defined():
        s += '\n\n\t' + str(mdl.bnk)
  
    if mdl.chgc.is_defined():
        s += '\n\n\t' + str(mdl.chgc)

    if mdl.inv.is_defined():
        s += '\n\n\t' + str(mdl.inv)

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
    if file_type == 'Modules':
        df = process_modules_csv(dpi)
        df.to_csv(os.path.join(dpo, 'CEC Modules.csv'))
    else:    
        df = process_inverters_csv(dpi)
        df.to_csv(os.path.join(dpo, 'CEC Inverters.csv'))
    
  
def main():
    pass

if __name__ == '__main__':
    main()    

