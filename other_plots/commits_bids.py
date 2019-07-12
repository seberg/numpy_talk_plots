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
             # "--no-merges",
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
    if False:
        # Filter by time, so autoscaling works...
        commits = commits.iloc[(commits["time"] > datetime.datetime(2013, 1, 1)).values]

    commits = commits.set_index("time")

    _all_community = set()

    def find_bids(row):
        name = row["name"]
        time = row.name

        if "eric wieser" in name.lower():
            return "Community"

        if "mattip" in name.lower() or "matti p" in name.lower():
            if time > datetime.datetime(2018, 3, 31):
                return "BIDS"
            else:
                return "Community"
        if "tyler reddy" in name.lower():
            if time > datetime.datetime(2018, 6, 8):
                return "BIDS"
            else:
                return "Community"
            return "BIDS"
        if "stefan van der walt" in name.lower() or "stefanv" in name.lower():
            # (Second one never happens)
            return "BIDS"

        if "sebastian berg" in name.lower() or "seberg" == name.lower():
            if time > datetime.datetime(2019, 4, 24):
                return "BIDS"
            else:
                return "Community"

        if name not in _all_community:
            # print(name)
            _all_community.add(name)
        return "Community"


    commits["name"] = commits.apply(find_bids, axis=1)

    groups = {}
    for g, comm in commits.groupby("name"):
        resampled = comm["name"].resample("Q").count() / 3
        groups[g] = resampled

    plt.figure(figsize=(4, 4/3*2))

    categories = ["Community", "BIDS"]
    stacked = []
    for color, cat in zip(["C0", "C1"], categories):
        next_stack = groups[cat]

        if len(stacked) > 0:
            prev_vals = stacked[-1].values
            next_stack = next_stack + stacked[-1]
        else:
            prev_vals = np.zeros_like(next_stack.values)

        stacked.append(next_stack)
        plt.fill_between(
            next_stack.index, next_stack.values, prev_vals,
            label=cat, lw=0, zorder=4 if cat == "Community" else 3,
            color=color, alpha=0.8)
        plt.plot(
            next_stack.index, next_stack.values, "o",
            zorder=4 if cat == "Community" else 3, color=color,
            mec="k")

    plt.xlim(datetime.datetime(2013, 1, 1), datetime.datetime(2019, 6, 30))
    plt.ylim(0, 230)


    plt.ylabel("Commits per month")
    plt.xlabel("Quarter")

    plt.tight_layout()
    plt.legend()

    plt.savefig("commits_community_bids.pdf")

    plt.show()