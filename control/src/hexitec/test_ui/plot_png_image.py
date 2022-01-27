"""Read PNG file and plot."""
try:
    import PyQt5
    # Avoid depreciation warning with: from matplotlib.backends.backend_qt5agg import ...
except ImportError:
    print("Script requires python package PyQt5 to be installed!")
    import sys
    sys.exit(1)

import matplotlib.pyplot as plt
import matplotlib.image as img
import sys


def plot_png_image(png_file):
    """Plot PNG image."""
    # Read png image
    im = img.imread(png_file)
    lum = im[:, :, ]
    # Set colormap as hot
    plt.imshow(lum, cmap='hot')
    plt.colorbar()
    plt.show()


if __name__ == '__main__':
    try:
        plot_png_image(sys.argv[1])
    except IndexError:
        print("Usage:")
        print("plot_png_image.py /path/to/my.png")
