tag_template = '''
def {name}(*args: TagChildArg, children: Optional[list[TagChildArg]] = None, **kwargs: TagAttrArg) -> Tag:
    """
    Create a <{name}> tag.

    {desc}

    Parameters
    ----------
    *args
        Child elements to this tag.
    children
        Child elements to this tag.
    **kwargs
        Attributes to this tag.

    Returns
    -------
    Tag
    """

    return Tag("{name}", *args, children=children, **kwargs)
'''
