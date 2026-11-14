ORDER = {"valid": 0, "degraded": 1, "unverified": 2}


def worst(*values):
    """A line is only as trustworthy as its weakest input."""
    return max(values, key=lambda v: ORDER[v])
