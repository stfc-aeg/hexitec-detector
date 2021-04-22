
try:
    import PyQt5
except ImportError:
    print("Script requires python package PyQt5 to be installed!")
    import sys
    sys.exit(1)

import sys

#applying pseudocolor
# importing pyplot and image from matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as img  

def turn_png_into_json(png_file):

    #png_file = "/u/ckd27546/tmp/CSD_average.png"
    # reading png image
    im = img.imread(png_file)  
    # applying pseudocolor
    # default value of colormap is used.
    lum = im[:, :,]  
    # show image
    plt.imshow(lum)

    #colorbar
    # reading png image
    im = img.imread(png_file)
    lum = im[:, :, ]
    # setting colormap as hot
    plt.imshow(lum, cmap ='hot')
    plt.colorbar()

    plt.show()


if __name__ == '__main__':
    try:
        turn_png_into_json(sys.argv[1])
    except IndexError:
        print("Usage:")
        print("turn_png_into_json.py /path/to/my.png")
