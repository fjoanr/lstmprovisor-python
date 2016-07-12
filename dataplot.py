import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import sys

def plot_file(fn):
    with open(fn,'r') as f:
        legend = f.readline()

    colnames = legend.strip().split(', ')
    data = np.loadtxt(fn, skiprows=1, delimiter=',')

    markers = ".ov^<>12348sp*hH+xDd"
    colors = "bgrcmyk"

    skip=100
    timestep = data[::skip,0]
    handles = []
    for i,colname in enumerate(colnames[1:]):
        val = data[::skip,1+i]
        handles.append(plt.scatter(timestep, val, marker=markers[i%len(markers)], color=colors[i%len(colors)]))

    plt.legend(handles, colnames[1:])
    plt.show()

if __name__ == '__main__':
    plot_file(sys.argv[1])