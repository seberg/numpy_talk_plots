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
             # '--merges', '--first-parent',
             # '--no-merges',
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

        if year == 2019:
            comms *= 2

        plt.figure(1, figsize=(4, 4/3*2))

        print(comms[:10])

        relative = comms.values / comms.values[0]
        plt.plot(np.arange(1, 11), relative[:10], "-o",
                     label=f"{year}", color=colors[i],
                     alpha=0.35 if year < 2016 else 0.8)

        plt.figure(2, figsize=(4, 4/3*2))


        plt.plot(np.arange(1, 11), comms.values[:10], "-o",
                 label=f"{year}", color=colors[i],
                 alpha=0.35 if year <= 2016 else 0.8)

    plt.figure(1)
    plt.xlabel("Top contributors")
    plt.xticks(np.arange(1, 11))
    plt.ylabel("Relative number of commits")  # non-merge commits

    plt.legend(ncol=2)

    plt.tight_layout()
    plt.savefig("relative_commits_per_year.pdf")

    plt.figure(2)
    plt.xlabel("Top contributors")
    plt.xticks(np.arange(1, 11))
    plt.ylabel("Number of commits")  # non-merge commits

    plt.legend(ncol=2)

    plt.tight_layout()
    plt.savefig("number_commits_per_year.pdf")

    plt.show()