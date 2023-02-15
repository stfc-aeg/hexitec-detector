"""
Generate a pattern of rows by columns.

Christian Angelsen, STFC Detector Systems Software Group
"""


def generate_pattern():
    """Generate a pattern in the form of a list of lists.

    Generate 2x6 json pattern replacement to be utilized by the integration test.
    """
    cleared = 0
    edged = 7
    idx = 0
    lone = 9
    rows = 160
    columns = 480
    pattern = []
    inner = []
    for i in range(rows):
        for j in range(columns):
            if (i == 0) or (i == rows-1) or (j == 0) or (j == columns-1):
                inner.append(cleared)
            elif ((i < 3) or (i > (rows-4))) and ((j < 3) or (j > (columns-4))):
                inner.append(edged)
            elif ((i < 4) or (i > (rows-5))) or ((j < 4) or (j > (columns-5))):
                inner.append(cleared)
            elif (((i+idx) % 6) == 1) or (((j+idx) % 7) == 0):
                # print("{} {}".format(i, j))
                idx += 1
                inner.append(lone)
            else:
                inner.append(cleared)
        pattern.append(inner)
        inner = []
    with open("2x6_pattern.json", "w") as f:
        f.write("{\n")
        f.write("    \"img\": {}\n".format(pattern))
        f.write("}")
    return pattern


if __name__ == '__main__':
    try:
        pattern = generate_pattern()
        # print(pattern)
    except IndexError:
        print("Bang!")

# Copy generated pattern and use by integration test:
#cp /u/ckd27546/tmp/2x6_pattern.json /<snip>/hexitec/install/test_config/patterns/CSD_2x6_average.json