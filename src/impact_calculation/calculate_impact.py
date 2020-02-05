import numpy as np
import math
import pandas as pd
from pandas import DataFrame
import os
from numpy.random import uniform
import glob
import sys
from pathlib import Path
from climada.hazard import Hazard
from climada.entity import Exposures
from climada.entity import ImpactFunc, ImpactFuncSet
from climada.engine import Impact

from define_if import impact_functions_random,call_impact_functions
from define_hazard import call_hazard
import gc
from scipy.sparse import csr_matrix

#This function calls a random hazard and impact function and take the given exposures to calculate an impact.
# The positional arguments are the directory for the hazard file, the impact functions directory, the years, the variables in which to pick in a distribution, a dictionary of the exposures, their name?. Other default variables can be set if needed 



def calculate_impact(directory_hazard,scenario,year,EXPOSURES,exposures_name,uncertainty_variable='all',
					 working_hours=None,kanton=None,sun_protection=False,efficient_buildings=False,
					 save_median_mat=False):

    
	IMPACT = {}
	
	if save_median_mat == True:
		matrices = {}
		save_mat = True
	else:
		save_mat = False

	HAZARD = call_hazard(directory_hazard,scenario,year,uncertainty_variable=uncertainty_variable,kanton=kanton,
						 working_hours=working_hours,sun_protection=sun_protection, only_outside=efficient_buildings)
	####################################################################################################

	if uncertainty_variable == 'impactfunction' or uncertainty_variable=='all' or uncertainty_variable == 'model':
		TF = True
	else: 
		TF = False

	if_HW_set = call_impact_functions(TF)


	for e_ in exposures_name: #calculate impact for each type of exposure
		impact = Impact()
		if (e_ == 'inside low expenditure') or (e_ == 'inside moderate expenditure'):
			impact.calc(EXPOSURES[e_],if_HW_set,HAZARD['heat inside'],save_mat=save_mat)
		elif (e_ == 'outside moderate expenditure') or (e_ == 'outside high expenditure'):
			impact.calc(EXPOSURES[e_],if_HW_set,HAZARD['heat outside'],save_mat=save_mat)

		IMPACT[e_]		= np.sum(impact.at_event)
	  
		if save_median_mat:
			matrices[e_]= csr_matrix(impact.imp_mat.sum(axis=0)) #sum all events to get one 1xgridpoints matrix per type of exposures
		del impact
		gc.collect()
	del HAZARD
	gc.collect()

	if save_median_mat:
		return [IMPACT, matrices]
	else:
		return [IMPACT]

