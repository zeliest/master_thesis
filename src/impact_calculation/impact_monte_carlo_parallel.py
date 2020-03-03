import numpy as np
import pandas as pd
from pandas import DataFrame
import gc
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
from calculate_impact import calculate_impact
from define_exposures import call_exposures
from multiprocessing import cpu_count
from scipy.sparse import csr_matrix, vstack


def impact_monte_carlo(directory_hazard, scenarios, years_list, n_mc, uncertainty_variables_list=['all'], kanton=None,
                       branch=None, working_hours=[8, 12, 13, 17], sun_protection=False,
                       efficient_buildings=False, save_median_mat=True):
    """Monte Carlo Simulation of the impacts:

                Parameters:
                    directory_hazard (str): directory to a folder containing one tasmax and one tasmin folder with all the
                                            data files
                    scenarios (list): scenarios for which to compute the hazards
                    years_list (list): years for which to compute the hazard
                    uncertainty_variables_list (list): variables for which to consider the uncertainty. Default: ['all']
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
                    impacts for each Monte Carlo run, year, scenario, exposure category, optionally impact matrix
                      """

    # the exposures are called outside the loop as their is no uncertainty in this entitiy.
    exposures = call_exposures(kanton=kanton, branch=branch, only_outside=efficient_buildings)

    if uncertainty_variables_list != ['all']:
        impact_uncertainty_variable = {}  # initiate dictionary for the uncertainty variables, if not 'all'
    for uncertainty_variable in uncertainty_variables_list:

        ###########################################################################################################
        # loop over years

        impact_scenario = {}  # initiate dictionary for the scenarios

        if save_median_mat:
            matrices_scenario = {}  # if we save the matrices, make dictionary for those

        for scenario in scenarios:

            ###################################################################################################
            # loop over variable with an uncertainty

            impact_year = {}  # for the years

            if save_median_mat:
                matrices_year = {}  # for the matrices and years

            for year in years_list:

                #######################################################################################
                # monte carlo calculating the impact for the given scenario, year and variable

                ncores_max = cpu_count()  # get the number of cores available

                impact = Parallel(n_jobs=ncores_max)(delayed(calculate_impact)(directory_hazard,
                                                                               scenario, year, exposures,
                                                                               uncertainty_variable=uncertainty_variable,
                                                                               kanton=kanton,
                                                                               sun_protection=sun_protection,
                                                                               working_hours=working_hours,
                                                                               efficient_buildings=efficient_buildings,
                                                                               save_median_mat=save_median_mat)
                                                     for i in range(0, n_mc))  # calculate the impact on different cores
                ########################################################################################

                impact_year[str(year)] = pd.DataFrame()  # panda dataframe of the impacts for the different exposures
                # and runs
                for e_ in exposures:
                    impact_year[str(year)][e_] = np.zeros(n_mc)

                if save_median_mat:
                    matrices_year[str(year)] = {}  # for the matrices, we save them in yet another dictionary as we
                # can't have a panda dataframe of matrices

                for e_ in exposures:
                    for i_ in range(0, n_mc):
                        impact_year[str(year)][e_][i_] = impact[i_][0][e_]  # change the order of the monte carlo
                    # output to fit the panda dataframe

                    if save_median_mat:  # calculate the median for each grid point from the n runs
                        # we could also here save the max and min matrix to reproduce some of the plots
                        # with the error included
                        matrices_year[str(year)][e_] = csr_matrix(np.median(vstack(impact[i_][1][e_]
                                                                                   for i_ in range(n_mc)).todense(),
                                                                            axis=0))

            del impact
            impact_scenario[scenario] = impact_year

            if save_median_mat:
                matrices_scenario[scenario] = matrices_year

        if uncertainty_variable != 'all':
            impact_uncertainty_variable[uncertainty_variable] = impact_scenario

    if uncertainty_variable == 'all':
        if not save_median_mat:
            return [impact_scenario]  # return only the total loss for each category
        else:
            return [impact_scenario, matrices_scenario]  # return the loss and the matrices

    else:
        return [impact_uncertainty_variable]  # in the case of the sensibility analysis, the dictionary of the output
    # has an extra level with corresponding to the variable varied
