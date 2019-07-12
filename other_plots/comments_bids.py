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


RESAMPLE_SPAN = "M"


dtypes = {"author_id": np.intp, "ticket_id": np.intp}

issues = pd.read_csv("for_numpy/issues.tsv", sep="\t", dtype=dtypes,
                     parse_dates=["created_at", "updated_at", "closed_at"])
c = pd.read_csv("for_numpy/comments.tsv", sep="\t", dtype=dtypes,
                parse_dates=["created_at", "updated_at"])

issues = issues.set_index("ticket_id")

def is_pr(row):
    ticket_id = row["ticket_id"]
    try:
        return issues["type"].loc[ticket_id] == "pull_request"
    except KeyError as e:
        #print(row)
        print(e)
        return False

print()
print()

c = c.iloc[np.array(c.apply(is_pr, axis=1))]

c = c.set_index("created_at")

def fix_author_association(row):
    if row["author_association"] == "NONE":
        return "NONE"
    if row["author_name"] == "mattip" and row.name > datetime.datetime(2018, 3, 11):
        return "BIDS"
    if row["author_name"] == "tylerjereddy" and row.name > datetime.datetime(2018, 6, 8):
        return "BIDS"
    if row["author_name"] == "seberg" and row.name > datetime.datetime(2019, 4, 24):
        return "BIDS"

    return row["author_association"]

c["author_association"] = c.apply(fix_author_association, axis=1)


stacked = {}
for ass, comments in c.groupby("author_association"):
    res = comments["id"].resample(RESAMPLE_SPAN).count()
    stacked[ass] = res

stack = []
for ass in ["NONE", "CONTRIBUTOR", "MEMBER", "BIDS"]:
    res = stacked[ass]
    if len(stack) > 0:
        res += stack[-1]
    stack.append(res)

    plt.plot(res.index, res.values, label=ass)

plt.xlabel("number of PR comments")
plt.ylim(0, None)
plt.xlim(datetime.datetime(2013, 1, 1), datetime.datetime(2019, 6, 1))

plt.legend()

plt.savefig("pr_comments_bids.pdf")
plt.show()


