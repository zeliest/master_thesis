import numpy as np
import pandas as pd
from pandas import DataFrame
import gc
import matplotlib.pyplot as plt
from joblib import Parallel, delayed
from calculate_impact import calculate_impact
from define_exposures import call_exposures
from multiprocessing import cpu_count
from scipy.sparse import csr_matrix,vstack


def impact_monte_carlo(directory_hazard,scenarios,years_list,n_mc,uncertainty_variables_list=['all'],kanton=None,
					   branch = None, working_hours=None, sun_protection=False,
					   efficient_buildings=False, save_median_mat=False)	:

	#the exposures are called outside the loop as their is no uncertainty in this class
	#lonlat = None

	EXPOSURES, exposures_name	 = call_exposures(kanton=kanton,branch=branch,only_outside=efficient_buildings)


	RMSE_hourly_t				 = 0.028530743129040116


	IMPACT_uncertainty_variable = {}
	for uncertainty_variable in uncertainty_variables_list:


		###########################################################################################################
		#loop over years
			

		IMPACT_scenario = {}

		if save_median_mat:
			MATRICES_scenario = {}

		for scenario in scenarios:

			###################################################################################################
			#loop over variable with an uncertainty
			
			IMPACT_year  = {}

			if save_median_mat:
				MATRICES_year = {}
			
			for year in years_list:
				
				#######################################################################################
				#monte carlo calculating the impact for the given scenario, year and variable

				
			   

				NCORES_MAX = cpu_count()
				
				
				IMPACT	  = Parallel(n_jobs=NCORES_MAX)(delayed(calculate_impact)(directory_hazard, scenario, year, EXPOSURES, exposures_name, uncertainty_variable=uncertainty_variable, kanton=kanton, sun_protection=sun_protection, working_hours = working_hours, efficient_buildings = efficient_buildings, save_median_mat = save_median_mat) for i in range(0,n_mc))
				########################################################################################
				
				IMPACT_year[str(year)] = pd.DataFrame()
				for e_ in exposures_name:
					IMPACT_year[str(year)][e_] = np.zeros(n_mc)

				if save_median_mat:
					MATRICES_year[str(year)] = {}
				
				for e_ in exposures_name:
					for i_ in range(0,n_mc):
						IMPACT_year[str(year)][e_][i_] = IMPACT[i_][0][e_]
					if save_median_mat:
						MATRICES_year[str(year)][e_] = csr_matrix(np.median(vstack(IMPACT[i_][1][e_]
																				   for i_ in range(n_mc)).todense(),axis=0))

			del IMPACT
			gc.collect()
			IMPACT_scenario[scenario] = IMPACT_year
			
			if save_median_mat:
				MATRICES_scenario[scenario] = MATRICES_year 

		if uncertainty_variable != 'all':	 
			IMPACT_uncertainty_variable[uncertainty_variable] = IMPACT_scenario
		
	if uncertainty_variable == 'all':
		if not save_median_mat:
			return [IMPACT_scenario]
		else:
			return [IMPACT_scenario, MATRICES_scenario]
				
	else:
		return [IMPACT_uncertainty_variable]


