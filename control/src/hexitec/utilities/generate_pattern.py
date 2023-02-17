"""
Generate a pattern of rows by columns.

Christian Angelsen, STFC Detector Systems Software Group
"""

import sys


def generate_pattern(miniature_visual):
    """Generate a pattern in the form of a list of lists.

    Generate 2x6 json pattern replacement to be utilized by the integration test.
    """
    cleared = 0
    edged = 9
    miniature_visual = bool(miniature_visual)
    if miniature_visual:
        rows = 12
        columns = 18
    else:
        rows = 160
        columns = 480
    pattern = []
    inner = []
    for i in range(rows):
        for j in range(columns):
            if ((i != 0) and (i % rows == 2)) and ((j != 0) and (j % columns == 2)):
                # 2 pixels away from top left
                inner.append(edged)
            elif ((i != 0) and (i % rows == 3)) and ((j != 0) and (j % columns == 2)):
                # 3 pixels away from top
                inner.append(8)
            elif ((i != 0) and (i % rows == 2)) and ((j != 0) and (j % columns == 3)):
                # 3 pixels away from left
                inner.append(6)
            elif ((i != 0) and (i % rows == 3)) and ((j != 0) and (j % columns == 3)):
                # 3 pixels away from top left
                inner.append(2)
            elif ((i != 0) and (i % rows == 2)) and ((j != 0) and (j % columns == columns-3)):
                # 2 pixels away from top right
                inner.append(edged)
            elif ((i != 0) and (i % rows == rows-3)) and (j % columns == 2):
                # bottom left
                inner.append(9)
            elif ((i != 0) and (i % rows == rows-3)) and (j % columns == columns-3):
                # bottom right
                inner.append(9)
            else:
                inner.append(cleared)

        pattern.append(inner)
        inner = []
    # Add L-shapes, 2x1, 1x2 etc shapes into finished 2D array
    offsetVal = 0
    for offsetRow in range(0, rows-12, 12):
        for offsetCol in range(0, columns-18, 18):
            iRow = 1
            iCol = 7
            insert_l_shapes(pattern, iRow, iCol, offsetRow, offsetCol, offsetVal)
            iRow = 0
            iCol = 12
            insert_pairs(pattern, iRow, iCol, offsetRow, offsetCol, offsetVal)
        offsetVal += 1

    # Mark four corners with pairs
    pattern[0][0] = 1
    pattern[1][0] = 7
    pattern[0][-1] = 10
    pattern[0][-2] = 7
    pattern[-1][0] = 11
    pattern[-2][0] = 12
    pattern[-1][-1] = 13
    pattern[-1][-2] = 14

    if miniature_visual:
        print(pattern)
    else:
        with open("2x6_pattern.json", "w") as f:
            f.write("{\n")
            f.write("    \"img\": {}\n".format(pattern))
            f.write("}")
    return pattern


def insert_l_shapes(pattern, iRow, iCol, offsetRow, offsetCol, offsetVal):
    # 1st L-shape:
    pattern[iRow+offsetRow][iCol+offsetCol] = offsetVal+1
    pattern[iRow+offsetRow][iCol+offsetCol+1] = offsetVal+2
    pattern[iRow+offsetRow][iCol+offsetCol+2] = offsetVal+3
    pattern[iRow+offsetRow+1][iCol+offsetCol] = offsetVal+2
    # 2nd L-shape:
    iRow += 3
    pattern[iRow+offsetRow][iCol+offsetCol] = offsetVal+2
    pattern[iRow+offsetRow+1][iCol+offsetCol] = offsetVal+5
    pattern[iRow+offsetRow+2][iCol+offsetCol] = offsetVal+4
    pattern[iRow+offsetRow+2][iCol+offsetCol+1] = offsetVal+3
    iRow += 1
    iCol -= 3
    # 3rd L-shape:
    pattern[iRow+offsetRow][iCol+offsetCol] = offsetVal+6
    pattern[iRow+offsetRow+1][iCol+offsetCol] = offsetVal+5
    pattern[iRow+offsetRow+2][iCol+offsetCol] = offsetVal+8
    pattern[iRow+offsetRow+2][iCol+offsetCol+1] = offsetVal+3


def insert_pairs(pattern, iRow, iCol, offsetRow, offsetCol, offsetVal):
    pattern[iRow][iCol+offsetCol] = offsetVal+9
    pattern[iRow][iCol+offsetCol+1] = offsetVal+8
    iCol += 1
    iRow += 2
    pattern[iRow][iCol+offsetCol] = offsetVal+3
    pattern[iRow+1][iCol+offsetCol] = offsetVal+2
    iRow += 2
    iCol -= 3
    pattern[iRow][iCol+offsetCol] = offsetVal+2
    pattern[iRow+1][iCol+offsetCol] = offsetVal+5
    iRow += 3
    pattern[iRow+1][iCol+offsetCol] = offsetVal+4
    pattern[iRow][iCol+offsetCol+1] = offsetVal+3
    iRow += 1
    iCol -= 3
    pattern[iRow+1][iCol+offsetCol] = offsetVal+4
    pattern[iRow][iCol+offsetCol+1] = offsetVal+9


if __name__ == '__main__':
    try:
        pattern = generate_pattern(int(sys.argv[1]))
    except IndexError:
        print("Usage:\npython generate_pattern <val>")
        print(" where <val> is 0 (print pattern to .json) or 1 (display mini version)")

# Copy generated pattern and use by integration test:
# cp ~/tmp/2x6_pattern.json /<snip>/hexitec/install/test_config/patterns/CSD_2x6_average.json
