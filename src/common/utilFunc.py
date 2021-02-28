def FormatNumber(value, format_str, heading="", trailing="", with_color=False):
    """
    Formating a number for printing friendly
    """
    if value < 0:
        return "-" + heading + format_str.format(abs(value)) + trailing
    else:
        return heading + format_str.format(value) + trailing

def isClose(value_a, value_b, delta = 1e-14):
    """
    Compare if two float values are within delta difference.
    """
    return abs(value_a - value_b) < delta
