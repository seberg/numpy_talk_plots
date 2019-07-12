#!/usr/bin/env python3

import os, io
import subprocess

import numpy as np
from matplotlib import pyplot as plt
import pandas as pd

import datetime


# The git commands, copied/stolen from Tyler!

def get_commits():
    cwd = os.getcwd()
    os.chdir('/home/sebastian/forks/numpy')
    # subprocess.call(['git', 'checkout', 'master'])

    # built up from: https://stackoverflow.com/a/47213799/2942522
    out = subprocess.check_output(
            ['git', 'log', '--use-mailmap',
             # Add this line to only use merge commits (see Tylers code)
             # However, the filtering does not work for merge commits, I think
             # Tylers may work for them.
             '--merges', '--first-parent',
             #'--no-merges',
             'master', '--format=%aN\t%aI\t%f'])
    os.chdir(cwd)

    out = out.replace(b"+00:00", b"")
    log_data = io.BytesIO()
    log_data.write(b"name\ttime\ttitle\n")
    log_data.write(out)
    del out
    log_data.seek(0)
    commits = pd.read_csv(log_data, parse_dates=["time"], sep="\t")

    return commits


if __name__ == "__main__":
    commits = get_commits()
    if True:
        # Filter by time, so autoscaling works...
        commits = commits.iloc[(commits["time"] > datetime.datetime(2013, 1, 1)).values]

    # commits = commits.set_index("time")
    # could probably change to resample...
    commits["year"] = commits["time"].dt.year

    by_year = commits.groupby("year")

    colors = plt.cm.magma_r(np.linspace(0.1, 0.9, by_year.ngroups))

    for i, (year, comms) in enumerate(by_year):
        comms = comms.groupby("name")["name"].count()
        comms = comms.sort_values()[::-1]

        plt.figure(1)

        print(comms[:10])

        relative = comms.values / comms.values[0]
        plt.semilogy(np.arange(len(relative))+1, relative, "-o",
                     label=f"{year}", color=colors[i])

        plt.figure(2)

        plt.plot(np.arange(len(comms.values))+1, comms.values, "-o",
                 label=f"{year}", color=colors[i])

    plt.figure(1)
    plt.xlabel("contributor")
    plt.ylabel("relative number of merge commits")

    plt.legend()

    plt.savefig("relative_merge_commits_per_year.pdf")

    plt.figure(2)
    plt.xlabel("contributor")
    plt.ylabel("number of non-merge commits")

    plt.legend()

    plt.savefig("number_merge_commits_per_year.pdf")

    plt.show()