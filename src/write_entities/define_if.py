import numpy as np
import math
import pandas as pd
from pandas import DataFrame
import os
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from climada.entity import ImpactFunc, ImpactFuncSet

def sigmoid(x, L ,x0, k, b):
        y = L / (1 + np.exp(-k*(x-x0)))+b
        return (y)
    
def truncated_normal(mean, stddev, minval, maxval):
        return np.clip(np.random.normal(mean, stddev), minval, maxval)

def impact_functions_random(file,intensity,error=True): 

    data  =  file[['wbgt','best estimate']]
    data  = data.dropna()
    xdata = data['wbgt']
    
    
    if error == True:
        if intensity   == 'high':
            mult=truncated_normal(1,0.3,0.2,1.8)
        elif intensity == 'moderate':
            mult=truncated_normal(1,0.3,0.2,1.8)
        else:
            mult=truncated_normal(1,0.3,0.2,1.8)
    else:
        mult=1
            
        
    ydata = data['best estimate'] * mult
    ydata = np.append(ydata,[100,100,100])
    ydata = np.append(ydata,[0,0,0])
    xdata = np.append(xdata,[60,61,62])    
    xdata = np.append(xdata,[20,21,22])    

    p0 = [max(ydata), np.median(xdata), 1,min(ydata)] # this is an mandatory initial guess

    fit, pcov = curve_fit(sigmoid, xdata, ydata,p0, method='dogbox')
    return fit



# In[8]:


def call_impact_functions(with_without_error):
       
    directory_if = '../../input_data/impact_functions/'
    

    file_low = pd.read_csv(''.join([directory_if,'impact_low.csv']))
    function_low=impact_functions_random(file_low,'low',with_without_error)

    file_moderate = pd.read_csv(''.join([directory_if,'impact_moderate.csv'])) 
    function_moderate=impact_functions_random(file_moderate,'moderate',with_without_error)


    file_high = pd.read_csv(''.join([directory_if,'impact_high.csv']))
    function_high=impact_functions_random(file_high,'high',with_without_error)


    ################################################################################################        
    if_HW_set = ImpactFuncSet()        
    x         = np.linspace(20, 40, num=30)
    ################################################################################################
    if_HW1                   = ImpactFunc() 
    if_HW1.haz_type          = 'HW'
    if_HW1.id                = 1
    if_HW1.name              = 'Low Expenditure'
    if_HW1.intensity_unit    = 'Degrees C'
    if_HW1.intensity         = x
    if_HW1.mdd               = (sigmoid(x, *function_low))/100
    if_HW1.mdd[if_HW1.mdd<0] = 0
    if_HW1.mdd[if_HW1.mdd>100] = 100
    if_HW1.paa               = np.linspace(1, 1, num=30)
    if_HW_set.append(if_HW1)
    #################################################################################################
    if_HW2                   =  ImpactFunc() 
    if_HW2.haz_type          =  'HW'
    if_HW2.id                =  2
    if_HW2.name              =  'Medium Expenditure'
    if_HW2.intensity_unit    =  'Degrees C'
    if_HW2.intensity         =  x
    if_HW2.mdd               =  (sigmoid(x, *function_moderate))/100
    if_HW2.mdd[if_HW2.mdd<0] =  0
    if_HW2.mdd[if_HW2.mdd>100] =  100
    if_HW2.paa               =  np.linspace(1, 1, num=30)
    if_HW_set.append(if_HW2)
    ##################################################################################################
    if_HW3                   =  ImpactFunc() 
    if_HW3.haz_type          =  'HW'
    if_HW3.id                =  3
    if_HW3.name              =  'High Expenditure'
    if_HW3.intensity_unit    =  'Degrees C'
    if_HW3.intensity         =   x
    if_HW3.mdd               =  (sigmoid(x, *function_high))/100
    if_HW3.mdd[if_HW3.mdd<0] =  0
    if_HW3.mdd[if_HW3.mdd>100] =  100
    if_HW3.paa               =  np.linspace(1, 1, num=30)
    if_HW_set.append(if_HW3)
    #################################################################################################

    return if_HW_set

