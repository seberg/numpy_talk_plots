#!/usr/bin/env python3

import numpy as np
from matplotlib import pyplot as plt
import pandas as pd

import utils

import datetime


def get_author_id(name):
    # ugly hack, but I do not care right now:
    names = issues[np.array(issues["author_name"] == "tylerjereddy")]
    return names["author_id"].iloc[0]


RESAMPLE_SPAN = "Q"

# Matti and Tyler
PAID_DEVS = {"mattip", "tyler"}


dtypes = {"author_id": np.intp, "ticket_id": np.intp}

# Original code loading in tickets from Nelle's data:
tickets = pd.read_csv("for_numpy/issues.tsv", sep="\t", dtype=dtypes,
                      parse_dates=["created_at", "closed_at"])

resampled = {}

for event in ["created_at", "closed_at"]:
    for group, issues in tickets.groupby("type"):
        fmt = "o--" if event == "created_at" else "o-"
        color = "C0" if group == "issue" else "C1"

        label = "Issue" if group == "issue" else "PR"
        label += " "
        label += "opened" if event == "created_at" else "closed"

        if group == "pull_request":
            print("Filtering for master")
            filt = np.array(issues["ticket_id"].apply(utils.pr_is_master))

            print("    ", filt.sum(), "of ", len(filt))
            issues = issues.iloc[filt]

        # not actually issues:
        issues = issues.set_index(event)

        if True:
            # Just resample, otherwise try rolling window.
            issues = issues["ticket_id"].resample("Q").count()
        else:
            issues = issues["ticket_id"].resample("D").count()
            issues = issues.rolling("90D").mean()[:-90]

        issues = issues[datetime.datetime(2013, 3, 1):]
        # Had this in for the talk plot:
        # print("Warning, extrapolating the last data point with 3/2.")
        # issues.iloc[-1] = issues.iloc[-1]  * 3/2  # EXTRAPOLATED!

        resampled[event, group] = issues

        plt.plot(issues.index, issues.values, fmt, label=label,
                 alpha=0.6, color=color)

plt.ylabel("number opened or closed")
plt.legend()

plt.tight_layout()
plt.savefig("issues_prs_open_close.pdf")

plt.figure(figsize=(4, 4/3*2))
diff_issues = (resampled["created_at", "issue"] -
               resampled["closed_at", "issue"])
diff_prs = (resampled["created_at", "pull_request"] -
            resampled["closed_at", "pull_request"])

plt.plot(diff_issues.index, diff_issues.values, "o-", label=r"Issues")
plt.plot(diff_prs.index, diff_prs.values, "s-", label=r"Pull Requests")

for last_years in [0, 1, 2, 3]:
    months = last_years * 4
    trange = slice(-months - 4, None if last_years == 0 else -months)
    trange_ext = slice(-months - 5, None if last_years == 0 else -months + 1)
    deltas_issues = diff_issues.values[trange]
    deltas_prs = diff_prs.values[trange]

    if False:  # Do Piecewise linear fits... I do not think I like them
        p_issues = np.polyfit(np.arange(4), deltas_issues, 1)[::-1]
        p_prs = np.polyfit(np.arange(4), deltas_prs, 1)[::-1]

        fit_issues = p_issues[0] + p_issues[1] * np.arange(-1, 5 if last_years != 0 else 4)
        fit_prs= p_prs[0] + p_prs[1] * np.arange(-1, 5 if last_years != 0 else 4)

        months = diff_issues.index[trange_ext]

        plt.plot(months, fit_issues, "--", color="C0", alpha=0.5)
        plt.plot(months, fit_prs, "--", color="C1", alpha=0.5)

plt.ylim(-50, 120)
plt.axhline(0, color="k", ls="--", zorder=0)

plt.ylabel("Number opened $-$ closed")
plt.xlabel("Quarter")
plt.legend(loc="upper left")

plt.tight_layout()
plt.savefig("issues_prs_delta.pdf")

plt.show()
