import numpy as np
import math
import pandas as pd
from pandas import DataFrame
import os
import matplotlib.pyplot as plt
import geopandas as gdb
from shapely.geometry import Point
from geopandas import GeoDataFrame
import sys
from pathlib import Path
from pyproj import Proj, transform

from climada.entity import Exposures
from shapefile_masks import vector_shapefile_mask

# In[ ]:



def call_exposures(kanton=None, branch = None, only_outside = False, epsg_data=2056, epsg_output=4326):
    directory = '../../input_data/exposures/'
    EXPOSURES = {}

    workers      = pd.read_csv(''.join([directory,'work_intensity.csv']))
    workers_dist = pd.read_csv(''.join([directory,'lv95_vollzeitequivalente.csv']))

###############################################################################################################################################
    #define geographic area if not entire country

    #########################################################################################################################################
    #workers distribution dataframe in terms of of monetary value

    workers_dist_monetary =  DataFrame()

    workers_dist_monetary['E_KOORD'] =  workers_dist['E_KOORD']
    workers_dist_monetary['N_KOORD'] =  workers_dist['N_KOORD']

    i_l = workers.loc[(workers['Indoor/Outdoor']=='I')&(workers['Occupation_category']=='L')]
    i_m = workers.loc[(workers['Indoor/Outdoor']=='I')&(workers['Occupation_category']=='M')]
    o_m = workers.loc[(workers['Indoor/Outdoor']=='O')&(workers['Occupation_category']=='M')]
    o_h = workers.loc[(workers['Indoor/Outdoor']=='O')&(workers['Occupation_category']=='H')]


    if branch == None:
        occupation=list(workers_dist)[2:]
    else:
        occupation = branch

    for o_ in occupation:
        salary = workers.loc[(workers['GIS_Data_code']==o_),'Hourly salary (CHF/h)'].values[0]
        workers_dist_monetary.loc[:,o_]=workers_dist.loc[:,o_]*salary 

    work_type = {}
    if_ref = {}
    exposures_name = set()

    for o_ in occupation:
        in_out    = workers[workers['GIS_Data_code'] == o_]['Indoor/Outdoor'].values[0]
        intensity = workers[workers['GIS_Data_code'] == o_]['Occupation_category'].values[0]

        if only_outside ==False:
        
            if in_out == 'I' and intensity=='L':
                exposures_name.add('inside low expenditure')
                work_type['inside low expenditure'] = i_l
                if_ref['inside low expenditure'] = 1


            if in_out == 'I' and intensity=='M':
                exposures_name.add('inside moderate expenditure')
                work_type['inside moderate expenditure'] = i_m
                if_ref['inside moderate expenditure'] = 2


        if in_out == 'O' and intensity=='M':
            exposures_name.add('outside moderate expenditure')
            work_type['outside moderate expenditure'] = o_m
            if_ref['outside moderate expenditure'] = 2

        if in_out == 'O' and intensity=='H':
            exposures_name.add('outside high expenditure')
            work_type['outside high expenditure'] = o_h
            if_ref['outside high expenditure'] = 3


    for w in exposures_name:


        code_i_l = ['E_KOORD','N_KOORD']
        if branch == None:
            code_i_l.extend(list(work_type[w]['GIS_Data_code']))
        else:
            code_i_l.extend(branch)

        workers_sum_intensity   =  DataFrame()
        workers_dist_intensity  =  workers_dist_monetary[code_i_l]

        workers_sum_intensity['longitude'] =  np.asarray(workers_dist_intensity['E_KOORD']).flatten()
        workers_sum_intensity['latitude']  =  np.asarray(workers_dist_intensity['N_KOORD']).flatten()
        workers_sum_intensity['value']     =  np.asarray(workers_dist_intensity[workers_dist_intensity.columns[2:]].sum(axis=1))
        n_exp                                     =  len(workers_sum_intensity['value'])


        if kanton:
            shp_dir = '../../input_data/shapefiles/KANTONS_projected_epsg4326/swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET_epsg4326.shp'
            workers_sum_intensity = vector_shapefile_mask(workers_sum_intensity,shp_dir,kanton,epsg_data,epsg_output)

            workers_sum_intensity               =  Exposures(workers_sum_intensity)
            workers_sum_intensity.set_lat_lon()
            n_exp                               =  len(workers_sum_intensity['value'])
            workers_sum_intensity['if_HW']      =  np.full((n_exp), if_ref[w], dtype=int)
            workers_sum_intensity.value_unit    =  'CHF'
            workers_sum_intensity.fillna(0)
            workers_sum_intensity.check()       

        else:

            workers_sum_intensity            =  Exposures(workers_sum_intensity)
            workers_sum_intensity.set_geometry_points()
            workers_sum_intensity.value_unit =  'CHF'
            workers_sum_intensity['if_HW']   =  np.full((n_exp), if_ref[w], dtype=int)
            workers_sum_intensity.crs = {'init':''.join(['epsg:',str(epsg_data)])}
            workers_sum_intensity.check()
            workers_sum_intensity.fillna(0)
            workers_sum_intensity.to_crs(epsg=epsg_output,inplace=True)
        name                                    =  w
        EXPOSURES[name]                         =  workers_sum_intensity
    ###########################################################################################################################################


    ###########################################################################################################################################


        exposures_name = list(exposures_name)


        #############################################################################################################
        
        
    return(EXPOSURES,exposures_name)

