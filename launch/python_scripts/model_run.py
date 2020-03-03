import numpy as np
from scipy import sparse
import pickle
from ast import literal_eval
import ast
import sys

# append the pathways to all modules used in the model
sys.path.append('../../src/impact_calculation')
sys.path.append('../../src/write_entities')
sys.path.append('../../src/util/')

from impact_monte_carlo_parallel import impact_monte_carlo


def convert(string):  # function that converts 'lists' from the bash input (strings) to python lists
    li = list(string.split(","))
    return li


directory_output = '../../output/impact_ch/'  # where to save to output
directory_hazard = sys.argv[1]  # first input from the bash script, which is the directory to the temperature files.

n_mc = literal_eval(sys.argv[2])  # number of Monte Carlo runs

# check the third input, which determines if the input should be calculated for Switzerland,
# all cantons indepentently or for one specific canton:
if sys.argv[3] == 'CH':
    kantons = [None]  # the None is put into a list, as we further loop through the cantons given
else:
    kantons = convert(sys.argv[3])
    directory_output = '../../output/impact_cantons/'  # in case a canton is given, the output is saved to the file
    # impact_cantons. However if an adaptation measure is specified later on, the output goes to impact_adaptation
    # even if considering a specific canton

# get fourth input, the years for which to compute the impact
years_list = [int(i) for i in convert(sys.argv[4])]

# get fifth input, the scenarios for which to compute the impact
scenarios = convert(sys.argv[5])

# check if any branches where given, or if the impact for all categories should be computed
if sys.argv[6] == '0':
    branch = None
    branches_str = 'all_branches'
else:
    branch = convert(sys.argv[6])
    branches_str = "_".join(branch)  # string to name the file later on

# set default for adaptation measures:
adaptation_str = ''
working_hours = [8, 12, 13, 17]
efficient_buildings = False
sun_protection = False

# check if any adaptation measures where given:

if literal_eval(sys.argv[7]) != 0:
    adaptation = convert(sys.argv[7])
    directory_output = '../../output/impact_adaptation/'
    adaptation = list(adaptation)
    adaptation_str = 'adaptation_measures'
    for a_ in adaptation:
        if a_ == '1':
            sun_protection = True
            adaptation_str = "".join([adaptation_str, a_, '_'])  # string to name the file

        if a_ == '2':
            efficient_buildings = True
            adaptation_str = "".join([adaptation_str, a_, '_'])
        if a_ == '3':
            working_hours = [int(w_) for w_ in convert(sys.argv[8])]
            adaptation_str = "".join([adaptation_str, a_, '_', str(working_hours[0]), 'h', str(working_hours[1]),
                                      'h', str(working_hours[2]), 'h', str(working_hours[3]), 'h', '_'])

# determine if the median damage matrix should be saved as output
if sys.argv[8] == '0':
    save_median_mat = False
else:
    save_median_mat = True

# in this base model run, all uncertainties are taken into account.
# This is not the case in the sensibility testing code where all are taken one by one.
uncertainty_variables_list = ['all']
uncertainty = 'all_uncertainties'

for kanton in kantons:  # loop through given kantons, one file per element in the kantons loop will be produced.
    # If cantons only contains None, only one file corresponding to all of Switzerland is produced,
    # otherwise one per canton will be written.

    if kanton is None:
        kanton_name = 'CH'
    else:
        kanton_name = kanton

    # compute the impact. impact[0] is the loss for each category and Monte Carlo run, impact[0] is the impact matrix
    # for each category and Monte Carlo run

    IMPACT = impact_monte_carlo(directory_hazard, scenarios, years_list, n_mc,
                                uncertainty_variables_list=uncertainty_variables_list, kanton=kanton,
                                branch=branch, working_hours=working_hours, sun_protection=sun_protection,
                                efficient_buildings=efficient_buildings, save_median_mat=save_median_mat)

    with open(''.join([directory_output, 'loss_', branches_str, '_', str(n_mc), 'mc_',
                       uncertainty, '_', adaptation_str, kanton_name, '.pickle']), 'wb') as handle:
        pickle.dump(IMPACT[0], handle, protocol=pickle.HIGHEST_PROTOCOL)
    if save_median_mat:
        with open(''.join([directory_output, 'matrix_',
                           branches_str, '_', str(n_mc), 'mc_', uncertainty, '_', adaptation_str, kanton_name,
                           '.pickle']) , 'wb') as handle:
            pickle.dump(IMPACT[1], handle, protocol=pickle.HIGHEST_PROTOCOL)
