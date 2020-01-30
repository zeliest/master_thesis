#!/bin/sh

area='CH'
years='2020,2035,2050'
scenario='RCP26,RCP45,RCP85'
n_mc=100
uncertainties=1

while getopts "d::f::c::g::y::s::u::" opt; do

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
    u) uncertainties="$OPTARG"
    ;;

  esac

done

path_model=$(pwd)

cd $directory_climada

source activate climada_env


cd $path_model


python3 ${path_model}/../python_scripts/test_sensitivity.py $directory_ch2018 $n_mc $area $years $scenario $uncertainties

#conda deactivate

echo 'script completed'
