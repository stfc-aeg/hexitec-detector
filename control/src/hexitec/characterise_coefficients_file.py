
import sys
import numpy as np

def characterise_coefficients_file(fname, datatype):
    """
    Determines number of coefficients, minimum and maximum of the targeted file
    """

    # fname = "/u/ckd27546/develop/projects/odin-demo/hexitec-detector/data/frameProcessor/m_2018_01_001_400V_20C.txt"
    f = open(fname)
    vals_str = f.read()
    f.close()

    n = np.fromstring(vals_str, dtype=datatype, sep=' ')

    items = len(n)
    minimum = n.min()
    maximum = n.max()

    print("Checking file %s\n   Items: %s\n   min: %s\n   max: %s" % (fname, items, minimum, maximum))

    ###

if __name__ == '__main__':
    # print(sys.argv[1])
    print("\n")
    print("Data types for calib: float, thresh: int8")
    print("Usage: python characterise_coefficients_file.py <file> <datatype>")
    print("Example: python characterise_coefficients_file.py /u/ckd27546/develop/projects/odin-demo/hexitec-detector/data/frameProcessor/m_2018_01_001_400V_20C.txt float")

    characterise_coefficients_file(sys.argv[1], sys.argv[2])
