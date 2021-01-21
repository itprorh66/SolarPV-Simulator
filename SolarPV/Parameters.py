#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  2 13:57:09 2018
Modified   Wed Dec  5 2018 - Update for Issue #2 DC loads
modified   Thu Dec 13 2018 (Issue #5)
Modified on 02/22/2019 for version 0.1.0
modified 1/8/2021 to accomodate pvlib's 0.8 use of Sandia Temperature_model_Parameters

@author: Bob Hentz
-------------------------------------------------------------------------------
  Name:        Parameters.py
  Purpose:     Declare Standardized System Parameters

  Copyright:   (c) Bob Hentz 2018
  License:     GNU General Public License, version 3 (GPL-3.0)

              This program is distributed WITHOUT ANY WARRANTY;
              without even the implied warranty of MERCHANTABILITY
              or FITNESS FOR A PARTICULAR PURPOSE.
 -------------------------------------------------------------------------------
"""
#Declare Energy Load Table Column Headings
load_fields = ['Type', 'Qty', 'Use Factor','Hours', 'Start Hour', 'Watts', 'Mode']

# Declare Energy Load Table Field Types by Column
load_field_types = [str, int, float, float, int, float, str]

"""
# Declare Energy Load Types and Operating Parameters
# Note User can modify these values for specific needs or add non-std entries
# load_types = {namestring:{'Watts':Float }}
# this structure allows for future addition of other types
"""
load_types = {'Light, LED':{'Watts':5.0, 'Mode': "AC"},
              'Light, Incadecent':{'Watts':65.0, 'Mode': "AC"},
              'Light, Compact Flourescent':{'Watts':20.0, 'Mode': "AC"},
              'Light, Flourescent':{'Watts':20.0, 'Mode': "AC"},
              'Computer, Laptop':{'Watts':25.0, 'Mode': "AC"},
              'Computer, Desktop':{'Watts':175.0, 'Mode': "AC"},
              'Light, Halogen':{'Watts':35.0, 'Mode': "AC"},
              'Refrigerator, 18 cf':{'Watts':125.0, 'Mode': "AC"},
              'Refrigerator, 18 cf Std':{'Watts':200.0, 'Mode': "AC"},
              'Freezer, 10 cu. Ft.':{'Watts':150.0, 'Mode': "AC"},
              'TV LCD':{'Watts':25.0, 'Mode': "AC"},
              'TV Regular':{'Watts':100.0, 'Mode': "AC"},
              'Stereo':{'Watts':35.0, 'Mode': "AC"},
              'Printer':{'Watts':30.0, 'Mode': "AC"},
              'Phone Charger':{'Watts':2.0, 'Mode': "AC"},
              'Well Pump AC, 1/2 HP':{'Watts':700.0, 'Mode': "AC"},
              'Well Pump AC, 1 HP':{'Watts':1500.0, 'Mode': "AC"},
              'Well Pump AC, 2 HP':{'Watts':3000.0, 'Mode': "AC"},
              'Refrigerator, DC 18cf':{'Watts': 40, 'Mode':'DC'},
              'Well Pump DC, 1 HP':{'Watts':500.0, 'Mode': "DC"},
              }

# Define the Albedo factor for Site surface conditions
albedo_types = {'Aluminum': 0.85,
                'Asphalt': 0.12,
                'City Environment': 0.18,
                'Concrete': 0.3,
                'Copper': 0.74,
                'Dark Soil': 0.1,
                'Desert Sand': 0.4,
                'Dry Bare Ground': 0.2,
                'Dry Grassland': 0.3,
                'Fresh grass': 0.26,
                'Galvanized Steel (Dirty)': 0.08,
                'Galvanized Steel (New)': 0.35,
                'Pale Soil': 0.3,
                'Red Tiles': 0.33,
                'Snow': 0.65,
                'Vegetation': 	0.2,
                'Water': 0.1
}

# Define bandgap energy coeficients for different panel materials
panel_types = {'Si':{'Descrpt':'Silicon','EgRef': 1.121, 'dEgdT': -0.0002677, 'M': [-1.26E-4, 2.816E-3, -0.024459, 0.086257, 0.918093]},
               'CdTe':{'Descrpt':'Cadmium Telluride','EgRef': 1.475, 'dEgdT': 1.475, 'M':[-2.46E-5, 9.607E-4, -0.0134, 0.0716, 0.9196] },
               'CIS':{'Descrpt':'Copper Indium diSelenide','EgRef': 1.010, 'dEgdT': -0.00011, 'M': [-3.74E-5, 0.00125, -0.01462, 0.0718, 0.9210]},
               'CIGS':{'Descrpt':'Copper Indium Gallium diSelenide ','EgRef': 1.15,  'M':[-9.07E-5, 0.0022, -0.0202, 0.0652, 0.9417] },
               'GaAs':{'Descrpt':'Gallium Arsenide','EgRef': 1.424, 'dEgdT': -0.000433},
               'HIT-Si':{'Descrpt':'Silicon','EgRef': 1.121, 'dEgdT': -0.0002677, 'M': [-1.26E-4, 2.816E-3, -0.024459, 0.086257, 0.918093]},
               'Mono-c-Si':{'Descrpt':'Silicon','EgRef': 1.121, 'dEgdT': -0.0002677, 'M': [-1.26E-4, 2.816E-3, -0.024459, 0.086257, 0.918093]},
               'Multi-c-Si':{'Descrpt':'Silicon','EgRef': 1.121, 'dEgdT': -0.0002677, 'M': [-1.26E-4, 2.816E-3, -0.024459, 0.086257, 0.918093]},
               '1-a-Si':{'Descrpt':'Silicon','EgRef': 1.121, 'dEgdT': -0.0002677, 'M': [-1.26E-4, 2.816E-3, -0.024459, 0.086257, 0.918093]},
               '2-a-Si':{'Descrpt':'Silicon','EgRef': 1.121, 'dEgdT': -0.0002677, 'M': [-1.26E-4, 2.816E-3, -0.024459, 0.086257, 0.918093]},
               '3-a-Si':{'Descrpt':'Silicon','EgRef': 1.121, 'dEgdT': -0.0002677, 'M': [-1.26E-4, 2.816E-3, -0.024459, 0.086257, 0.918093]},
               'a-Si':{'Descrpt':'Silicon','EgRef': 1.121, 'dEgdT': -0.0002677, 'M': [-1.26E-4, 2.816E-3, -0.024459, 0.086257, 0.918093]},
               'a-Si/nc':{'Descrpt':'Silicon','EgRef': 1.121, 'dEgdT': -0.0002677, 'M': [-1.26E-4, 2.816E-3, -0.024459, 0.086257, 0.918093]}
               }

# PVLIB standard descriptions (open_rack_glassback is default)
panel_racking = ['open_rack_cell_glassback',
                 'roof_mount_cell_glassback',
                 'open_rack_cell_polymerback',
                 'insulated_back_polymerback',
                 'open_rack_polymer_thinfilm_steel']


# Transforms PVLIB panel_racking configuration to Sandia temperature model nomenclature
temp_model_xlate = { 'open_rack_cell_glassback':['sapm', 'open_rack_glass_glass'], 
                                 'roof_mount_cell_glassback':['sapm', 'close_mount_glass_glass'],
                                 'open_rack_cell_polymerback':['sapm', 'open_rack_glass_polymer'],
                                 'insulated_back_polymerback':['sapm', 'insulated_back_glass_polymer'],
                                 'open_rack_polymer_thinfilm_steel':['sapm', 'open_rack_glass_glass']
                                 }


# Define battery efficiency factors based on type
battery_types = {'FLA':('Flooded Lead Acid', 0.90),
                 'GEL':('Gelled Electrolyte Sealed Lead-Acid', 0.92 ),
                 'AGM':('Sealed Absorbed Glass Mat Lead-Acid', 0.94)
        }

# Define Charge Controler Types
chgcntl_types = {'PWM':'Pulse Width Modulated', 'MPPT':'Max Power Point'}

def main():
	pass



if __name__ == '__main__':
    main()
