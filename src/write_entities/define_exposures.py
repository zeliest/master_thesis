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


def call_exposures(kanton=None, branch=None, only_outside=False, epsg_output=4326):
    """write the Exposures:

                    Parameters:

                        kanton (str or None): Name of canton. Default: None (all of Switzerland)
                        branch (str or None): specific economic branch, as given in the 'GIS_data_code' of the
                                                work_intensity.csv file. Default: None
                        only_outside (bool): rather to only output the exposures outside,
                                                considering in that case that the people inside
                                                are not exposed to the risk of heat
                        epsg_output (int): EPSG code of the output. Default: 4326.

                    Returns:
                        Dictionary containing one Exposure per category of workers
                          """

    directory = '../../input_data/exposures/'
    exposures = {}  # dictionary of the exposures, where we will further put each category of Exposure as a key
    workers_info = pd.read_csv(
        ''.join([directory, 'work_intensity.csv']))  # file containing the information on the intensity,
    # inside/outside, salary of each branch
    workers_dist = pd.read_csv(''.join([directory, 'lv95_vollzeitequivalente.csv']))
    # file containing the geographical location of the workers by branch
    epsg_data = 2056  # espg of the workers_dist data

    workers_dist_monetary = DataFrame()  # new dataframe where we transform
    # the 'full time equivalents' values in monetary values by multiplying by the salary

    workers_dist_monetary['E_KOORD'] = workers_dist['E_KOORD']  # same coordinates
    workers_dist_monetary['N_KOORD'] = workers_dist['N_KOORD']

    #  get subset of thw workers data for each category
    # inside low:
    i_l = workers_info.loc[(workers_info['Indoor/Outdoor'] == 'I') & (workers_info['Occupation_category'] == 'L')]
    # inside moderate:
    i_m = workers_info.loc[(workers_info['Indoor/Outdoor'] == 'I') & (workers_info['Occupation_category'] == 'M')]
    # outside moderate:
    o_m = workers_info.loc[(workers_info['Indoor/Outdoor'] == 'O') & (workers_info['Occupation_category'] == 'M')]
    # outside high:
    o_h = workers_info.loc[(workers_info['Indoor/Outdoor'] == 'O') & (workers_info['Occupation_category'] == 'H')]

    if branch is None:
        occupation = list(workers_dist)[2:]  # take all branches
    else:
        occupation = branch  # take only the given branches

    for o_ in occupation:
        salary = workers_info.loc[(workers_info['GIS_Data_code'] == o_), 'Hourly salary (CHF/h)'].values[0]
        workers_dist_monetary.loc[:, o_] = workers_dist.loc[:, o_] * salary  # for each occupation multiply by the
        # corresponding salary

    work_type = {}
    if_ref = {}
    exposures_name = set()

    for o_ in occupation:
        in_out = workers_info[workers_info['GIS_Data_code'] == o_]['Indoor/Outdoor'].values[0]  #
        intensity = workers_info[workers_info['GIS_Data_code'] == o_]['Occupation_category'].values[0]

        if not only_outside:  # if we didn't specify that we only wanted the exposures outside

            if in_out == 'I' and intensity == 'L':
                exposures_name.add('inside low physical activity')
                work_type['inside low physical activity'] = i_l
                if_ref['inside low physical activity'] = 1

            if in_out == 'I' and intensity == 'M':
                exposures_name.add('inside moderate physical activity')
                work_type['inside moderate physical activity'] = i_m
                if_ref['inside moderate physical activity'] = 2

        if in_out == 'O' and intensity == 'M':
            exposures_name.add('outside moderate physical activity')
            work_type['outside moderate physical activity'] = o_m
            if_ref['outside moderate physical activity'] = 2

        if in_out == 'O' and intensity == 'H':
            exposures_name.add('outside high physical activity')
            work_type['outside high physical activity'] = o_h
            if_ref['outside high physical activity'] = 3

    for w_ in exposures_name:

        code_i_l = ['E_KOORD', 'N_KOORD']
        if branch is None:
            code_i_l.extend(list(work_type[w_]['GIS_Data_code']))
        else:
            code_i_l.extend(branch)

        workers_sum_intensity = DataFrame()  # last dataframe with monetary value for each intensity
        workers_dist_intensity = workers_dist_monetary[code_i_l]

        workers_sum_intensity['longitude'] = np.asarray(workers_dist_intensity['E_KOORD']).flatten()
        workers_sum_intensity['latitude'] = np.asarray(workers_dist_intensity['N_KOORD']).flatten()
        workers_sum_intensity['value'] = np.asarray(
            workers_dist_intensity[workers_dist_intensity.columns[2:]].sum(axis=1))
        n_exp = len(workers_sum_intensity['value'])

        if kanton:  # test if a canton was specified, in that case
            # we first get a panda geodataframe and define the exposures slightly differently
            shp_dir = '../../input_data/shapefiles/KANTONS_projected_epsg4326/' \
                      'swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET_epsg4326.shp'

            workers_sum_intensity = vector_shapefile_mask(workers_sum_intensity, shp_dir, kanton, epsg_data,
                                                          epsg_output)

            workers_sum_intensity = Exposures(workers_sum_intensity)  # define as Exposure class
            workers_sum_intensity.set_lat_lon()
            n_exp = len(workers_sum_intensity['value'])
            workers_sum_intensity['if_heat'] = np.full((n_exp), if_ref[w_], dtype=int)
            workers_sum_intensity.value_unit = 'CHF'
            workers_sum_intensity.fillna(0)
            workers_sum_intensity.check()

        else:  # normal case, for entire Switzerland

            workers_sum_intensity = Exposures(workers_sum_intensity)
            workers_sum_intensity.set_geometry_points()
            workers_sum_intensity.value_unit = 'CHF'
            workers_sum_intensity['if_heat'] = np.full((n_exp), if_ref[w_], dtype=int)
            workers_sum_intensity.crs = {'init': ''.join(['epsg:', str(epsg_data)])}
            workers_sum_intensity.check()
            workers_sum_intensity.fillna(0)
            workers_sum_intensity.to_crs(epsg=epsg_output, inplace=True)
        name = w_
        exposures[name] = workers_sum_intensity

    return exposures
