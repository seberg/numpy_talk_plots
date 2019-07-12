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
             '--no-merges',
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

    commits = commits.set_index("time")

    plt.figure(figsize=(6, 4))
    plt.title("non merge commits to master")

    def find_category(title):
        """Very crude attempt, note that commits could be in multiple..."""
        if isinstance(title, float):
            return "Other"
        # orig_title = title
        title = title.upper()
        if "BLD" in title or "BUILD" in title:
            return "BLD"
        if "BUG" in title or "FIX" in title:
            return "BUG,FIX"
        if "TST" in title:
            return "TST"
        if "MAINT" in title or "MNT" in title:
            return "MAINT"
        if "STY" in title:
            return "Other"
        if "DOC" in title:
            return "DOC"
        return "Other"

    commits["title"] = commits["title"].apply(find_category)

    groups = {}
    for g, comm in commits.groupby("title"):
        resampled = comm["title"].resample("Q").count()
        groups[g] = resampled

    categories = ["Other", "DOC", "BUG,FIX", "MAINT", "BLD", "TST"]
    stacked = []
    for cat in categories:
        next_stack = groups[cat]

        if len(stacked) > 0:
            next_stack = next_stack + stacked[-1]

        stacked.append(next_stack)
        plt.plot(next_stack.index, next_stack.values, "-",
                 label=cat)

    plt.xlim(datetime.datetime(2013, 1, 1), resampled.index.max())
    plt.ylim(0, None)

    plt.legend()

    plt.show()