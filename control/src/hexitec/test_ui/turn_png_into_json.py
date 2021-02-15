"""Support Hexitec integration tests; Turns a PNG file into equivalent json file.

Christian Angelsen, STFC Detector Systems Software Group
"""

try:
    import PyQt5
except ImportError:
    print("Script requires python package PyQt5 to be installed!")
    import sys
    sys.exit(1)

# importing pyplot and image from matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as img
import json
import sys


def turn_png_into_json(png_file, rows, columns):
    """Take file.png and writes its values (scaled up) into file.json."""
    # reading png image
    try:
        im = img.imread(png_file)
    except FileNotFoundError as e:
        print("File error: {}".format(e))
        return

    if (rows > im.shape[0]) or (columns > im.shape[1]):
        print(" Requested {} by {} but file dimensions: {} by {}. ".format(rows, columns, im.shape[0], im.shape[1]))
        print(" Abort..")
        return
    lum = im[:rows, :columns]

    # Characterise values in PNG file
    spread = []
    zeros = 0
    nonzeros = 0
    for row in range(rows):
        for column in range(columns):
            val = lum[row][column]
            if (val > 0) and (val not in spread):
                spread.append(val)
            if val == 0:
                zeros += 1
            else:
                nonzeros += 1

    print("The file: {}".format(png_file))
    print(" Zero values: {}".format(zeros))
    print(" non-zeros:   {}".format(nonzeros))
    print(" Total:       {}".format(zeros + nonzeros))
    print(" spread:      \n", spread)

    # Array of floats, either 0.0 or 0.4777065;
    # Scale by 25 before converting to integers, or array of zeros
    lum = lum * 25
    lum_ints = lum.astype(int)
    print("Array dims going into JSON file: {}".format(lum_ints.shape))
    # Create JSON file with same name as PNG file
    index = png_file.find(".")
    json_file = png_file[:index] + ".json"

    try:
        # Write to json file
        with open(json_file, "w+") as outfile:
            json.dump(lum_ints.tolist(), outfile)
        print("Wrote JSON file: ", json_file)
    except Exception as e:
        print("Error writing JSON file: {}".format(e))

    # setting colormap as hot
    plt.imshow(lum, cmap='hot')
    plt.colorbar()

    plt.show()


if __name__ == '__main__':
    # print("\ncommandline arguments: ", sys.argv)
    usage = "python turn_png_into_json.py /path/to/my.png <rows> <columns>"
    if (len(sys.argv) != 4):
        print("Wrong arguments supplied, should look like:")
        print(usage)
    else:
        try:
            rows, columns = int(sys.argv[2]), int(sys.argv[3])
            turn_png_into_json(sys.argv[1], rows, columns)
        except IndexError:
            print("\nUsage:")
            print(usage)
