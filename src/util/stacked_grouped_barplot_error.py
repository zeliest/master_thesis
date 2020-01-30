import random
import pandas as pd
import matplotlib.cm as cm
import numpy as np
import matplotlib.pyplot as plt
def plot_clustered_stacked_with_error(dataframe, minimums,maximums, color = None):
    fig, ax = plt.subplots()
    labels_graph = list(dataframe[list(dataframe.keys())[0]])
    lc = len(dataframe[list(dataframe.keys())[0]].columns)
    width = 0.2
    b_width = 0.2
    hatches = ['','//','//////']
    if color==None:
        color = ["#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]) for i in range(lc)]
    else:
        color = color

    for j_,s_ in enumerate(dataframe):
        dataframe[s_].columns = (name_ for name_ in range(lc))
        H = hatches[j_]
        N= len(dataframe[s_])
        index=np.arange(N)
        labels=dataframe[s_].index
        for p_ in range(lc):
            if p_ == 0:
                bottom=None
            else:
                bottom = sum(dataframe[s_].iloc[:,b_] for b_ in range(0,p_))
            if p_ == len(dataframe[s_].columns)-1:
                err = np.array([minimums[s_]['total'],maximums[s_]['total']])
            else:
                err = None
                #error_kw = None
            ax.bar(index +j_*b_width, dataframe[s_].iloc[:,p_],data=dataframe[s_],width = 0.2,hatch = H,bottom = bottom,
                   color = color[p_],edgecolor ='white',label = labels_graph[p_], yerr = err,
                   error_kw=dict(barsabove=True,elinewidth=1, capsize=3,ecolor='gray'))


        ax.set_ylabel('Annual Expected Damage')
        if j_ == 0:
            plt.xticks(index+b_width, labels)

            ax.legend(loc=[1.01, 0.5])
            #ax.legend(h[:lc], l[:lc], loc=[1.01, 0.5])
            #ax.add_artist(l2)

    return(ax)
