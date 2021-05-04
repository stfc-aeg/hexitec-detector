"""
Characterise range of values within a coefficients file.

Christian Angelsen, STFC Detector Systems Software Group
"""
import sys
import numpy as np


def characterise_coefficients_file(fname, datatype):
    """Determine number of coefficients, minimum and maximum of the targeted file."""
    try:
        f = open(fname)
        vals_str = f.read()
        f.close()
    except IOError as e:
        print("Error: %s" % e)
        return

    n = np.fromstring(vals_str, dtype=datatype, sep=' ')

    items = len(n)
    minimum = n.min()
    maximum = n.max()

    print("Checking file %s\n   Items: %s\n   min: %s\n   max: %s" %
          (fname, items, minimum, maximum))


if __name__ == '__main__':
    # print(sys.argv[1])
    try:
        characterise_coefficients_file(sys.argv[1], sys.argv[2])
    except IndexError:
        print("\n")
        print("Data types for calib: float, thresh: int8")
        print("Usage: python characterise_coefficients_file.py <file> <datatype>")
        print("i.e.: python characterise_coefficients_file.py ~/tmp/m_coeffs.txt float")
