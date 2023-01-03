import basket_case as bc


def enum_to_dict(enum, alpha=False):
    """Convert an enum to a dict of title-cased keys and the corresponding values, optionally alphabetizing."""
    out = {bc.title(e.name.lower().replace("_", " ")): e.value for e in enum}
    if alpha:
        out = {k: out[k] for k in sorted(out.keys())}
    return out
