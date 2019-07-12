#!/usr/bin/env python3

import numpy as np
from matplotlib import pyplot as plt
import pandas as pd

import datetime

import utils

# from caostk import plotting

# plt.style.use("sebastian-thesis")

def get_author_id(name):
    # ugly hack, but I do not care right now:
    names = issues[np.array(issues["author_name"] == "tylerjereddy")]
    return names["author_id"].iloc[0]


RESAMPLE_SPAN = "Q"
IGNORE_MONTHS = 3
# Matti and Tyler
PAID_DEVS = {"mattip", "tyler"}


dtypes = {"author_id": np.intp, "ticket_id": np.intp}

issues = pd.read_csv("for_numpy/issues.tsv", sep="\t", dtype=dtypes,
                     parse_dates=["created_at", "updated_at", "closed_at"])
c = pd.read_csv("for_numpy/comments.tsv", sep="\t", dtype=dtypes,
                parse_dates=["created_at", "updated_at"])


issues = issues.iloc[np.array(issues["created_at"] > datetime.datetime(2013, 1, 1))]
c = c.iloc[np.array(c["created_at"] > datetime.datetime(2013, 1, 1))]
c.copy()

PAID_DEVS = {get_author_id(n) for n in PAID_DEVS}

# Both Issues and PRs:
issues = issues.set_index("ticket_id")

by_id = c.groupby("ticket_id")

issues["first_reaction_time"] = np.nan
issues_unpaid = issues.copy()

count = 0

print("Info on paid developer being first to comment:")
for num, comments in by_id:
    try:
        creator = issues.loc[num, "author_id"]
    except:
        # Issue is out of range for time of interest.
        continue
    # For now also be OK with othe rpeople commenting, as long as it is not
    # the original author:
    comments = comments.iloc[np.array(comments["author_id"] != creator)]

    if len(comments) == 0:
        continue

    comments = comments.sort_values("created_at")
    first_reaction = comments["created_at"].min()

    issue_created_at = issues.loc[num, "created_at"]
    # could also count
    reaction_time = (first_reaction - issue_created_at)

    if IGNORE_MONTHS:
        if reaction_time > datetime.timedelta(days=IGNORE_MONTHS*30):
            continue

    seconds = reaction_time.total_seconds()
    issues.loc[num, "first_reaction_time"] = seconds

    assert comments.iloc[0]["created_at"] == first_reaction
    if comments.iloc[0]["author_id"] not in PAID_DEVS:
        issues_unpaid.loc[num, "first_reaction_time"] = seconds
    else:
        print("   ", issues_unpaid.loc[num, "created_at"], num, first_reaction - issue_created_at)
        count += 1

print("Number of issues first comment is paid:", count)
print()
del count

# Ignore issues created by Members (not pull requests though)
# TODO: Clean this up maybe...
tickets = issues[
        ~(np.asarray(issues["author_association"] == "MEMBER") &
          np.asarray(issues["type"] == "issue"))]
tickets_unpaid = issues_unpaid[
        ~(np.asarray(issues_unpaid["author_association"] == "MEMBER") &
          np.asarray(issues_unpaid["type"] == "issue"))]
del issues, issues_unpaid


for issue_kind in ["both", "pull_request"]:
    if issue_kind == "both":
        issue_str = ""
    elif issue_kind == "issue":
        issue_str = "Issue"
    elif issue_kind == "pull_request":
        issue_str = "PR"
    else:
        raise ValueError("jarharharhar")

    if issue_kind != "both":
        issues = tickets.iloc[np.asarray(tickets["type"] == issue_kind)]
        issues_unpaid = tickets_unpaid.iloc[np.asarray(tickets_unpaid["type"] == issue_kind)]
        issues = issues.copy()
        issues_unpaid = issues_unpaid.copy()

        if issue_kind == "pull_request":
            print("Filtering for master branch")
            print("    before:", len(issues))
            issues = issues.iloc[
                    np.array([utils.pr_is_master(pr) for pr in issues.index])]
            issues = issues.copy()
            issues_unpaid = issues_unpaid.iloc[
                    np.array([utils.pr_is_master(pr) for pr in issues_unpaid.index])]
            print("    after:", len(issues))
            issues_unpaid = issues_unpaid.copy()

    else:
        issues = tickets.copy()
        issues_unpaid = tickets_unpaid.copy()

    issues["closed_time"] = np.nan
    closed_time = (issues["closed_at"] - issues["created_at"]).dt
    if IGNORE_MONTHS:
        filt = closed_time.to_pytimedelta() > datetime.timedelta(IGNORE_MONTHS * 30)
        closed_time = closed_time.total_seconds().copy()
        closed_time.iloc[np.array(filt)] = np.nan
    else:
        closed_time = closed_time.total_seconds().copy()
    issues["closed_time"] = closed_time
    del closed_time

    times = issues[["created_at", "author_id", "first_reaction_time", "closed_time"]]
    times_unpaid = issues_unpaid[["created_at", "author_id", "first_reaction_time"]]

    times = times.set_index("created_at")
    times_unpaid = times_unpaid.set_index("created_at")

    #################################################################
    fig = plt.figure(figsize=(6, 4))
    ax = plt.gca()
    twin_ax = ax  # plt.twinx()
    plt.title(f"{issue_str} time until first comment".rstrip())

    for fmt, alpha, remove_paid in [("o-", 1, False)]: # , ("o--", 0.5, True)
        if remove_paid:
            reaction_t = times_unpaid["first_reaction_time"]
            reaction_t = reaction_t.iloc[np.asarray(reaction_t == reaction_t)]
        else:
            reaction_t = times["first_reaction_time"]
            reaction_t = reaction_t.iloc[np.asarray(reaction_t == reaction_t)]

        # Drop NaN:
        reaction_t = reaction_t.iloc[~np.asarray(np.isnan(reaction_t))]

        resampled = reaction_t.resample(RESAMPLE_SPAN)

        comment_mean = resampled.mean() / 3600 / 24
        ax.plot(comment_mean.index.values, comment_mean.values,
                fmt, alpha=alpha, label="mean", color="C0")

        comment_median = resampled.median() / 3600 / 24
        twin_ax.plot(comment_median.index.values, comment_median.values,
                     fmt, alpha=alpha, label="median", color="C1")

        # ax.legend(loc="best")

    ax.set_ylabel("days")  #, color="C0")
    ax.set_ylim(0, None)
    # twin_ax.set_ylabel("median in days", color="C1")
    #twin_ax.set_ylim(0, None)
    plt.legend()

    plt.tight_layout()
    plt.savefig(f"time_commented_{issue_kind}.pdf")

    #################################################################

    fig = plt.figure(figsize=(6, 4))
    ax = plt.gca()
    twin_ax = ax # plt.twinx()
    plt.title(f"{issue_str} time until closed".lstrip())

    fmt, alpha = "o-", 1

    closed_time = times["closed_time"].copy()
    closed_time = closed_time.iloc[~np.asarray(np.isnan(closed_time))]
    resampled_closed = times["closed_time"].resample(RESAMPLE_SPAN)

    closed_mean = resampled_closed.mean() / 3600 / 24
    ax.plot(closed_mean.index.values, closed_mean.values,
            fmt, alpha=alpha, label="mean", color="C0")

    closed_median = resampled_closed.median() / 3600 / 24
    twin_ax.plot(closed_median.index.values, closed_median.values,
                 fmt, alpha=alpha, label="median", color="C1")

    ax.set_ylabel("days")  # , color="C0")
    ax.set_ylim(0, None)
    # twin_ax.set_ylabel("median in days", color="C1")
    #twin_ax.set_ylim(0, 15)
    plt.legend()

    plt.tight_layout()
    plt.savefig(f"time_closed_{issue_kind}.pdf")


#################################################################

fig = plt.figure(figsize=(6, 4))
ax = plt.gca()

RESAMPLE_SPAN = "Q"

if RESAMPLE_SPAN == "2Q":
    plt.title("Comments per half year")
elif RESAMPLE_SPAN == "Q":
    plt.title("Comments per quarter")
elif RESAMPLE_SPAN == "M":
    plt.title("Comments per month")
else:
    plt.title(f"Comments per {RESAMPLE_SPAN}")

cn = c[["created_at", "author_id"]]
ct = cn.set_index("created_at")

resampled_c = ct.resample(RESAMPLE_SPAN)

print()
unique = resampled_c.nunique()
number = resampled_c.count()
# Remove last one, it does not make sense, since it is not complete:
unique = unique.iloc[:-1]
if RESAMPLE_SPAN == "Q":
    print("Warning extrapolating last quarter")
    number.iloc[-1] = number.iloc[-1] * 3/2

ax.plot(unique.index.values, unique.values, "o-")

ax.set_ylim(0, None)
ax.set_ylabel("number of unique commentators", color="C0")

ax = plt.twinx()
ax.plot(number.index.values, number.values, "s-", color="C1")

ax.set_ylim(0, None)
ax.set_ylabel("number of comments", color="C1")

plt.tight_layout()
plt.savefig("unique_commentators.pdf")

#####################################################

if False:
    # Was just trying around with seeing what happend 2019 that the
    # number of unique people went up so much, but no idea...
    cn = c[["created_at", "ticket_id", "author_id"]]
    ct = cn.set_index("created_at")

    resampled_c = ct.resample(RESAMPLE_SPAN)
    resampled_c.indices  # triggers some internal stuff?

    plt.figure()

    for t, o in resampled_c:
        if t < datetime.datetime(2019, 1, 1):
            continue
        unique = o.groupby("ticket_id")["author_id"].nunique()
        plt.hist(unique, bins=10, histtype="step", label=str(t))

    plt.semilogy()
    plt.legend()


plt.close()



plt.figure()

for issue_type, t in tickets.groupby("type"):
    for year in [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020][:-2:-1]:
        min_year = year - 8
        max_year = year
        filt = t["created_at"] > datetime.datetime(year-2, 1, 1)
        filt &= t["created_at"] < datetime.datetime(year, 1, 1)
        yt = t[filt]
        bins = np.logspace(1, 7, 20)
        vals, _, __ = plt.hist(yt["first_reaction_time"].dropna(), bins=bins,
                           density=True, histtype="step",
                           label=f"{issue_type} {min_year}–{max_year}")
        xvals = 0.5 * (bins[:-1] + bins[1:])
        filt = vals > 0
        filt &= xvals > 10**3
        p = np.polyfit(np.log10(xvals[filt]), np.log10(vals[filt]), deg=1)[::-1]
        plt.plot(xvals, 10**(p[0] + np.log10(xvals) * p[1]), "k-", alpha=0.5)
        print(f"Slope {issue_type}, {min_year}–{max_year}:", p[1])
plt.loglog()
plt.xlabel("time in seconds")
plt.ylabel("relative probability")
plt.legend()
plt.show()
