import numpy as np
from scipy import sparse
import pickle
from ast import literal_eval
import ast

import sys

sys.path.append('../../src/impact_calculation')
sys.path.append('../../src/write_entities')
sys.path.append('../../src/util/')

from impact_monte_carlo_parallel import impact_monte_carlo


def Convert(string):
    li = list(string.split(","))
    return li

directory_output = '../../output/impact_sensitivity/'
directory_hazard = sys.argv[1]  # first input from the bash script.

n_mc = literal_eval(sys.argv[2])

# check the second input, which determines if the input should be calculated for Switzerland,
# all cantons indepentently or for one specific canton:
if sys.argv[3] == 'CH':
    kantons = [None]
else:
    kantons = [sys.argv[3]]
    directory_output = '../../output/impact_cantons/'

# get fourth input, the years for which to compute the impact
years_list = [int(i) for i in Convert(sys.argv[4])]

# get fith input, the scenarios for which to compute the impact
scenarios = Convert(sys.argv[5])
# check if any branches where given, or if the impact for all cathegories should be computed

branch = None
branches_str = 'all_branches'


# check if any adaptation measures where given
adaptation_str = ''
working_hours = None
efficient_buildings = False
sun_protection = False

# determine if the median damage matrix should be saved as output



# in this basic model run, all uncertainties are taken into accout.
# his is not the case in the sensibility testing code where all are taken seperatly.
if (sys.argv[6]) == '1':
    uncertainty_variables_list   = ['hourly_temperature','sun_or_shadow','t_to_wbgt','temp_in','impactfunction','simulations']
    uncertainty = 'all_uncertainties_independently'
elif (sys.argv[6]) == '2':
    uncertainty_variables_list   = ['year']
    uncertainty = 'natural_variability_uncertainty'

save_median_mat = False

for kanton in kantons:  # loop through given kantons, one file per element in the kantons loop will be produced.
    # If cantons only contains None, only one file corresponding to all of Switzerland is produced,
    # otherwise one per canton will be written.

    if kanton is None:
        kanton_name = 'CH'
    else:
        kanton_name = kanton

    IMPACT = impact_monte_carlo(directory_hazard, scenarios, years_list, n_mc,
                                uncertainty_variables_list=uncertainty_variables_list, kanton=kanton,
                                branch=branch, working_hours=working_hours, sun_protection=sun_protection,
                                efficient_buildings=efficient_buildings, save_median_mat=save_median_mat)

    with open(''.join([directory_output, 'damage_cost_', branches_str, '_', str(n_mc), 'mc_',
                       uncertainty, '_', adaptation_str, kanton_name, '.pickle']), 'wb') as handle:
        pickle.dump(IMPACT[0], handle, protocol=pickle.HIGHEST_PROTOCOL)
