#!/usr/bin/env python


try:
    import github
    g = github.Github()  # Can add token/password, may make things faster.
    numpy = g.get_repo('numpy/numpy')

except:
    numpy = None


cache = {}
try:
    with open(__file__ + "_cache.txt", "r") as cf:
        for line in cf:
            line = line.strip()
            ticket_id, is_master = line.split("\t")
            cache[int(ticket_id)] = (is_master == "True")
except IOError:
    print("Cache file not yet created.")


def pr_is_master(ticket_id):
    if ticket_id in cache:
        return cache[ticket_id]

    if numpy is None:
        raise ValueError("Must install github, or can only use cache.")

    pr = numpy.get_pull(ticket_id)
    is_master = pr.base.label == "numpy:master"
    # Could fetch `pr.merged_by.id` or `.login`

    cache[ticket_id] = is_master
    with open(__file__ + "_cache.txt", "a+") as cf:
        cf.write(f"{ticket_id}\t{is_master}\n")

    print(f"Fetched: {ticket_id}\tis master: {is_master}")
    return is_master
    
