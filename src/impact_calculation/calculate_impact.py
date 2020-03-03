import numpy as np
import math
import pandas as pd
from pandas import DataFrame
import os
from numpy.random import uniform
import glob
import sys
from pathlib import Path
from climada import hazard
from climada.entity import exposures
from climada.entity.impact_funcs import ImpactFunc, ImpactFuncSet
from climada.engine import Impact

from define_if import impact_functions_random, call_impact_functions
from define_hazard import call_hazard
import gc
from scipy.sparse import csr_matrix


# This function calls a random hazard and impact function and take the given exposures to calculate an impact. The
# positional arguments are the directory for the hazard file, the impact functions directory, the years,
# the variables in which to pick in a distribution, a dictionary of the exposures, their name?. Other default
# variables can be set if needed


def calculate_impact(directory_hazard, scenario, year, exposures, uncertainty_variable='all',
                     working_hours=None, kanton=None, sun_protection=False, efficient_buildings=False,
                         save_median_mat=False):
    """compute the impacts once:

                Parameters:
                    directory_hazard (str): directory to a folder containing one tasmax and one tasmin folder with all the
                                            data files
                    scenario (str): scenario for which to compute the hazards
                    year(str): year for which to compute the hazards
                    exposures(Exposures): the exposures which stay fixed for all runs
                    uncertainty_variable(str): variable for which to consider the uncertainty. Default: 'all'
                    kanton (str or None): Name of canton. Default: None (all of Switzerland)
                    branch (str or None): specific economic branch, as given in the 'GIS_data_code' of the
                                            work_intensity.csv file. Default: None
                    sun_protection (bool): rather to consider the adaptation measure sun 'protection'. Default: False
                    working_hours (list): hours where people are working. list with the first number being when they
                            start in the day, the second when they start their midday break,
                            third when they start in the afternoon and last when they finished in the evening
                            Default:[8,12,13,17]
                    efficient_buildings (bool): rather damage occurs only outside (buildings are well insulated from heat)
                            Default: False

                    save_median_mat (bool): rather we save the impact matrix . Default = True

                Returns:
                    Dictionary of impact loss and dictionary of impact matrices if specified
                      """

    impact_dict = {}

    if save_median_mat:
        matrices = {}
        save_mat = True
    else:
        save_mat = False

    hazard = call_hazard(directory_hazard, scenario, year, uncertainty_variable=uncertainty_variable, kanton=kanton,
                         working_hours=working_hours, sun_protection=sun_protection, only_outside=efficient_buildings)
    ####################################################################################################

    if uncertainty_variable == 'impactfunction' or uncertainty_variable == 'all':
        TF = True
    else:
        TF = False

    if_hw_set = call_impact_functions(TF)

    for e_ in exposures:  # calculate impact for each type of exposure
        impact = Impact()
        if (e_ == 'inside low physical activity') or (e_ == 'inside moderate physical activity'):
            impact.calc(exposures[e_], if_hw_set, hazard['heat inside'], save_mat=save_mat)
        elif (e_ == 'outside moderate physical activity') or (e_ == 'outside high physical activity'):
            impact.calc(exposures[e_], if_hw_set, hazard['heat outside'], save_mat=save_mat)

        impact_dict[e_] = np.sum(impact.at_event)

        if save_median_mat:
            matrices[e_] = csr_matrix(impact.imp_mat.sum(axis=0))
        # sum all events to get one 1xgridpoints matrix per type of exposures

    del hazard

    if save_median_mat:
        output = [impact_dict, matrices]
    else:
        output = [impact_dict]

    return output