"""plot_OneDim.py.

Plot A one-dimensional dataset.

Created on 11th July 2022

:author: Christian Angelsen, STFC Application Engineering Gruop
"""

import io
import h5py
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime


if __name__ == "__main__":

    hdf_file_location = "/u/ckd27546/tmp/100_xtek_000001.h5"
    hdf_file = h5py.File(hdf_file_location, 'r')
    # hdf_file 
    #<HDF5 file "13June1122_000001.h5" (mode r)>

    # print("Keys: {}".format(hdf_file.keys()))
    #Keys: <KeysViewHDF5 ['pixel_spectra', 'raw_frames', 'spectra_bins', 'summed_images', 'summed_spectra']>

    summed_spectra = np.array(hdf_file["summed_spectra"])
    summed_spectra.ndim
    summed_spectra.shape

    bins = 8000//10
    ypoints = summed_spectra[0]
    xpoints = np.array(range(0, bins))

    fig, ax = plt.subplots()

    plt.plot(xpoints, ypoints)
    ax.set_xlabel('Number of bins')
    ax.set_ylabel('Hits')
    timestamp = '%s' % (datetime.now().strftime('%Y%m%d_%H%M%S.%f'))
    ax.set_title(r'Summed_spectra ({})'.format(timestamp))
    # Enforcing plot limits redundant?
    plt.xlim(0, bins)
    ymin = summed_spectra[0].min()
    max = summed_spectra[0].max()
    ymax = max + round(max * 0.1)
    plt.ylim(ymin, ymax)
    # b = io.BytesIO()
    # plt.savefig(b, format='png')
    # plt.close()

    # b.seek(0)
    # with open("frommem.png", "wb") as f:
    #   f.write(b.read())

    plt.show()

