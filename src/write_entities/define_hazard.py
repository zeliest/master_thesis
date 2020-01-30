import numpy as np
import math
import pandas as pd
from pandas import DataFrame
import os
import matplotlib.pyplot as plt
import netCDF4
import datetime
from datetime import datetime, timedelta
from netCDF4 import num2date, date2num
import xarray as xr
from netCDF4 import Dataset
from numpy.random import uniform
import random
import glob
from scipy.optimize import curve_fit
import os
from pathlib import Path
from scipy import sparse
np.warnings.filterwarnings('ignore')
from pyproj import Proj, transform
import gc
from shapefile_masks import add_shape_coord_from_data_array
import sys

from climada.hazard import Hazard

T_to_WBGT     = np.poly1d([0.64879697, 4.22085354]) #fit found by analyzing station data from T to WBGT in the shadow
T_to_WBGT_sun = np.poly1d([0.61111305, 6.64870352]) #same in the sun
sd_mean_sun   = 1.686897665324121 #standards deviation
sd_mean       = 1.2956438427881554 # standard deviation
Tin_est       = np.array([ 0.18797175,  0.27614082, -0.05381464,  0.67076506]) # parameters for the inside temperature fitting function

def T_diff_fit(x, a, b, c, phi): #function fitting the difference btw inside and outside temperature
    return a * np.sin(b * x + phi) + c

# In[ ]:


def call_hazard(directory_hazard,scenario,year,uncertainty_variable='all',kanton=None,sun_protection=False,working_hours=None,only_outside= False):
#The function takes in the tmax file directory, the tmin should have the same directory and file name, only replacing the tasmax by tasmin. 
#the variables for which a random value inside the distribution is taken can be set independently or can be set to 'all' or 'None'. These variables are the transformation to wbgt T, the number of hours worked in the sun, the transformation to hourly T, the transformation to inside temperature, which simulation is chosen
#bounds can be given as coordinates to calculate the hazard for a subset of Switzerland. If the espg of these coordinates is not 4326, it must be specified as espg.
    
    
    if working_hours == None:
        working_hours = [8,12,13,17]
    
    if not sun_protection:
        ones_zero_random   = np.random.choice([0, 1], size=(8,)) #randomly pick the number of hours where people working outside are in the sun
    else:
        ones_zero_random   = np.ones(8,dtype=int)

    RMSE_hourly_t          = 0.028530743129040116 #Root mean square error from the hourly T transformation
    error_hourly_t         = np.random.normal(0,RMSE_hourly_t) # error for the transformation from min T and max T to hourly T
    error_temp_in          = np.random.triangular(0,1,1.2) #error for the inside temperature estimation. 
    error_wbgt             = np.random.normal(0,2/3.92) #error for the transformation between T and WBGT
    if uncertainty_variable == 'all' or uncertainty_variable == 'years':
        ny=random.randint(-2, 2) #to be added to the year, so that any year in the +5 to -5 range can be picked
    else: #if we are testing the sensitivity to the change in variables, we always want to be taking the same year and therefore add 0 
        ny = 0

    #simulation_elements = file.split('_')              #save charasteristics of the simulation as fiven in the file
   #simulation          = '_'.join(simulation_elements[4:7]) #mostly not needed but can be useful to study the behavior of the different simulations 
    if uncertainty_variable == 'simulations' or uncertainty_variable == 'all' :
        tasmax_nc = np.random.choice(list(set(glob.glob(''.join([directory_hazard,'*',scenario,'*'])))))
    else:
        tasmax_nc = glob.glob(directory_hazard+'/*SMHI-RCA_NORESM_EUR44*')[0]
    
    tasmin_nc           = tasmax_nc.replace('tasmax', 'tasmin') #take equivalent tasmin file
    TASMAX              = xr.open_dataset(tasmax_nc).sel(time=slice(''.join([str(year+ny),'-01-01']), ''.join([str(year+1+ny),'-01-01']))) #open as xr dataset
    TASMIN              = xr.open_dataset(tasmin_nc).sel(time=slice(''.join([str(year+ny),'-01-01']), ''.join([str(year+1+ny),'-01-01'])))
  

    if kanton:
        shp_dir = '../../input_data/shapefiles/KANTONS_projected_epsg4326/swissBOUNDARIES3D_1_3_TLM_KANTONSGEBIET_epsg4326.shp'
        TASMAX = add_shape_coord_from_data_array(TASMAX,shp_dir,kanton)
        TASMAX = TASMAX.where(TASMAX[kanton]==0, other=np.nan)
        TASMIN = add_shape_coord_from_data_array(TASMIN,shp_dir,kanton)
        TASMIN = TASMIN.where(TASMIN[kanton]==0, other=np.nan)


    TASMIN = TASMIN.where(TASMAX['tasmax'] > 22).dropna(dim='time',how='all') #replace all values under 22 degrees for tasmax by nas in both TASMIN and TASMAX
    TASMAX = TASMAX.where(TASMAX['tasmax'] > 22).dropna(dim='time',how='all')

    #TASMAX = TASMAX.dropna(dim='time',how='all') #get rid of all times with only NAs
    #TASMIN = TASMIN.dropna(dim='time',how='all') #get rid of all times with only NAs


    ndays = len(TASMAX.time) #number of days
    nlats = len(TASMAX.lat) #number of latitudes
    nlons = len(TASMAX.lon) #number of longitudes
    l     = ndays*24  #number of total hours for the time range of the given fil
    sh    = working_hours[0]   #beginning of working day
    eh    = working_hours[3]  #End of working day
    wh    = eh-sh #length of working day


    ########################################################################################################################################    
    #variables needed for the model (h_max is the hour at which the temperature is highest, h_min lowest)

    ld        = len(TASMAX.time)

    nhours    = ld*wh 
    h_max     = 15 #set 15 as the warmest hour of the day
    h_min     = 5 #set 5 as the coldest hour
    pi        = math.pi
    cos       = math.cos 
    temp      = np.zeros([nhours,nlats,nlons])
    wbgt_out  = np.zeros([nhours,nlats,nlons])
    wbgt_in   = np.zeros([nhours,nlats,nlons])
    temp_in   = np.zeros([nhours,nlats,nlons])
    d         = 0 #start at day 0
    h         = sh+1 #start at hour 9
    week_day = d # also start at 0


    #create an array with the maximum, the minimum, the average and the amplitude of the day


    #########################################################################################################################################################
    for t in range(nhours): #loop over time, if the time is in the range of 8 to 17
     
            
        if week_day<6: #ignores 2 out of 7 days (weekend)
        

            if d<(len(TASMAX.tasmax.values)-1): #if d is not the last day of the dataset
                next_day = d+1
            else: 
                next_day = d 
        
            if h<=working_hours[1] or h>working_hours[2]:

                #model to give the hourly temperature based on the maximum and minimum temperature of this day, as well as the min temperature of the next


                if  h_min          <= h < h_max:

                    temp[t,:,:]    = ((TASMAX.tasmax.values[d] + TASMIN.tasmin.values[d]) / 2 -
                                      (TASMAX.tasmax.values[d] - TASMIN.tasmin.values[d]) 
                                      / 2 * cos ( pi *(h-h_min)/(h_max - h_min)))

                if  h_max          <= h:

                    temp[t,:,:]    = (TASMIN.tasmin.values[next_day] +  TASMAX.tasmax.values[next_day]) \
                                     / 2 - ( TASMIN.tasmin.values[next_day] - TASMAX.tasmax.values[d] )\
                                     /2 *cos(pi*(h-h_max) / (h_min-h_max))


                if uncertainty_variable == 'hourly_temperature':
                    temp[t,:,:]    = temp[t,:,:] + error_hourly_t

                #in the case that the wbgt for any of the points on the map is larger then 22, 
                #save the temperature transformed to a wbgt 

                sun_or_shadow_functions = [T_to_WBGT_sun, T_to_WBGT]
                sun_or_shadow_sd        = [sd_mean_sun,sd_mean]

                if uncertainty_variable == 'sun_or_shadow' or uncertainty_variable=='all':
                    one_zero=np.random.choice(ones_zero_random)
                    sun_or_shadow  = sun_or_shadow_functions[one_zero]
                    sd = sun_or_shadow_sd[one_zero] 

                else: 
                    sun_or_shadow = sun_or_shadow_functions[1]
                    sd = sun_or_shadow_sd[1] 


                if uncertainty_variable == 't_to_wbgt' or uncertainty_variable=='all':
                    wbgt_out[t,:,:] = np.random.normal(sun_or_shadow(temp[t,:,:]),sd)+error_wbgt
                else:
                    wbgt_out[t,:,:] = np.random.normal(sun_or_shadow(temp[t,:,:]),sd)

                if not only_outside:
                   
                    
                    if uncertainty_variable == 'temp_in' or uncertainty_variable=='all':

                        temp_in[t,:,:]=temp[t,:,:]*(1+(np.array(T_diff_fit(h,*Tin_est)))*error_temp_in) #transform to inside temperature to make the wbgt>22 test for inside events

                    else:
                        temp_in[t,:,:]=temp[t,:,:]*(1+np.array(T_diff_fit(h,*Tin_est)))



                        #same as above for inside temperature):


                    if uncertainty_variable == 't_to_wbgt' or uncertainty_variable=='all':                            
                        wbgt_in[t,:,:] = (np.random.normal(T_to_WBGT(temp_in[t,:,:]),sd_mean))

                    else:
                        wbgt_in[t,:,:] = (np.random.normal(T_to_WBGT(temp_in[t,:,:]),sd_mean))+error_wbgt


        h = h+1 #add +1 to the hour, if this is the end of the day add 1 to d and go back to hour=1
        if h == eh+1: 
            h = sh+1
            d = d+1
            week_day = week_day + 1
            if week_day ==8:
                week_day = 0
            
                



    l_in  = np.zeros(len(wbgt_in),dtype=bool)
    l_out = np.zeros(len(wbgt_out),dtype=bool)

    for i_ in range(len(wbgt_in)):
        l_out[i_] = np.any(wbgt_out[i_,:,:]>22)
        l_in[i_]  = np.any(wbgt_in[i_,:,:]>22)

    l_in[0]=True



    wbgt_out = wbgt_out[l_out==True]
    wbgt_in  = wbgt_in[l_in==True]

    i = len(wbgt_out)
    j = len(wbgt_in)


    ###########################################################################################################    

    if i>0 and j>0: #if we have both events inside and outside

        nevents      =  [i,j]
        events       = [range(i),range(j)]
        wbgt_data    = [wbgt_out,wbgt_in]
        hazard_types = ['heat outside','heat inside']

   # elif i>0: #if we have only events outside

    #    nevents      = [i]
     #   events       = [range(i)]
      #  wbgt_data    = [wbgt_out]
       # hazard_types = ['heat outside']


    ###########################################################################################################    

    

    ###################################################################################################
    #define an event for each hour where the temperature is over 22 degrees for one geographic point
    HAZARD={}

    for w_ in range(len(wbgt_data)) : #write down the events in Hazard class

        grid_x, grid_y = np.meshgrid(TASMAX.lon.values, TASMAX.lat.values)
        heat                           =  Hazard('HW')
        heat.centroids.set_lat_lon(grid_y.flatten(),grid_x.flatten(),crs={'init': 'epsg:4326'})
        heat.units                     =  'degrees c'
        heat_data                      =  wbgt_data[w_]
        heat_data[np.isnan(heat_data)] =  0.
        heat.intensity                 =  sparse.csr_matrix(heat_data.reshape(nevents[w_],nlons*nlats))
        heat.event_id                  =  np.array(events[w_])
        heat.event_name                =  heat.event_id
        heat.frequency                 =  np.ones(nevents[w_])
        heat.fraction                  =  heat.intensity.copy()
        heat.fraction.data.fill(1)
        heat.check()
        HAZARD[hazard_types[w_]] = heat


    ####################################################################################################
    TASMAX.close()
    TASMIN.close()
    del TASMAX
    del TASMIN
    del wbgt_in
    del wbgt_out
    del temp_in
    del temp
    gc.collect()
  
                    
    #return(HAZARD,i,j,simulation)
    return(HAZARD) #return the hazards, the number of events inside and outside



