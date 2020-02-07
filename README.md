# Master Thesis on the Loss of Labor Productivity due to Heat in Switzerland

## Prerequisites
PYTHON 3.6+

Anaconda or Miniconda 

CLIMADA 1.3.1+

Access to the CH2018 TASMIN and TASMAX gridded datasets (about 500 GB) needed to run the simulation:
https://www.nccs.admin.ch/nccs/en/home/data-and-media-library/data/ch2018---climate-scenarios-for-switzerland.html

Tutorial to install CLIMADA using Anaconda or Miniconda:
https://climada-python.readthedocs.io/en/stable/guide/install.html

To run the simulation, access to a cluster is necessary as the model requires 1000 runs for the results to stabilise and each run takes about 9 minutes on one core. Getting the damage for Switzerland, three RCP scenarios and three years requires 32 cores to run for about 24 hours.      
The median impact matrix with and without the adaptation measures is saved in the output folder, and enables to calculate the median damage for the different cantons, without having to run the model again. However, to get the full distribution of the damage of a canton, the damage must be computed again. With the same number of cores as before, it takes for example about 4 hours to calculate the damage for the canton of Zurich, and less than 2 for Geneva.

For the installation of CLIMADA on a server or on the ETH Euler Cluster, follow this tutorial:
https://github.com/CLIMADA-project/climada_python/blob/master/doc/guide/install_cluster.rst
joblib must also then added to the CLIMADA conda environment to run the model. On the terminal, from the default shell (without activating the environment), write:

    conda install -n climada_env joblib

## Launch
Once CLIMADA and joblib are installed, navigate to master_thesis_repo/launch/bash_scripts

the model can then be launched from the command line, giving at least the arguments for the location of CLIMADA and the CH2018 data (no need to activate CLIMADA):

    ./model_run.sh -d /path/to/climada -f /path/to/CH2018/

A number of arguments are then optional:

    c) The number of monte carlo simulations. Default=1000
    
    g) Area for which to calculate the impacts. 
        Given as the name of a canton, or list of canton, in the main language of the given cantons. Default=CH
        
    y) Year or list of years for which to compute the damage. Default=2020,2035,2050 
    
    s) Scenario or list of scenarios. Default=RCP26, RCP45,RCP85
    
    b) Branch or list of branches as defined in master_thesis_repo/input_data/exposures/work_intensity.csv 
        in the GIS_data_code column. Default=0 (None) 
        
    a) List of adaptation measures. 0=Non, 1=sun protection, 2=efficient buildings, 3=adapted hours. Default=0
    
    w) Working Hours if a was previously set to 3. 
        The working hours must be precised as a list where the total time worked amounts to 8 hours (e.g. 8,12,13,17) 
        
    m) Rather to only save the damage cost as a total for Switzerland or also save the spatial impact matrix. 
        1=yes, 0=no. Default=0
    
    
To run the simulation on the euler cluster, the arguments for the cluster are given first and the  arguments for the model after. For example to run the entire model for Switzerland for the year 2050, the RCP85 scenario, 1000 monte carlo simulations and saving the median impact matrix:

    bsub -n 32 -R "rusage[mem=4000]" ./model_run.sh -d /path/to/climada -f /path/to/CH2018/ -y 2050 -s RCP85 -c 1000 -m 1

More information on the possible arguments for the cluster can be found here: 
https://scicomp.ethz.ch/wiki/Getting_started_with_clusters#Job_monitoring

## Data Analyis

The results jupyter notebook in master_thesis_repo/data_analysis/notebooks/ shows how to get the numbers and figures from the output of the model.

 



 

