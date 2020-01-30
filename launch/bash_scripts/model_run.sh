#!/bin/sh
 
area='CH'
adaptation=0
years='2020,2035,2050'
scenario='RCP26,RCP45,RCP85'
branches=0
save_matrix=0
working_hours='8,12,13,17'
n_mc=100

while getopts "d::f::c::g::y::s::b::a::w::m::" opt; do

  case $opt in

    d) directory_climada="$OPTARG" 
    ;;
    f) directory_ch2018="$OPTARG"
    ;;
    c) n_mc="$OPTARG"    
    ;;
    g) area="$OPTARG" 
    ;;
    y) years="$OPTARG"
    ;;
    s) scenario="$OPTARG"
    ;;
    b) branches="$OPTARG"
    ;;
    a) adaptation="$OPTARG"
    ;;
    w) working_hours="$OPTARG"    
    ;;
    m) save_matrix="$OPTARG"
    ;;

  esac

done

path_model=$(pwd)

cd $directory_climada

source activate climada_env


cd $path_model


python3 ${path_model}/../python_scripts/model_run.py $directory_ch2018 $n_mc $area $years $scenario $branches $adaptation $working_hours $save_matrix

#conda deactivate

echo 'script completed' 






