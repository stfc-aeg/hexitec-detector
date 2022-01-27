"""Characterise all datasets (except processed_frames).

Christian Angelsen, STFC Detector Systems Software Group
"""

import h5py
import numpy as np
import argparse

class DatasetChecker:
    """Summarises all datasets info, except processed_frames."""

    def check_if_empty(self):
        """Check whether 'pixel_spectra' empty - superseded."""
        print("Pixel_spectra has dimensions: {}".format(self.pixel_spectra.shape))
        (dim_a, dim_b, dim_c) = self.pixel_spectra.shape
        completely_empty = True
        for loop in range(dim_a):
            summed = self.pixel_spectra[loop].sum()
            if summed > 0:
                print("Pixel_spectra, image{}: {} > 0.0".format(loop, summed))
                completely_empty = False
        if completely_empty:
            print("Pixel_spectra completely empty!")

    def check_empty_frames(self, dataset_name):
        """Check whether dataset_name is empty."""
        with h5py.File(args.filename, "r") as data_file:
            # print("Keys: {}".format(data_file.keys()))
            try:
                self.data = np.array(data_file[dataset_name])
            except KeyError as e:
                print(" *** Couldn't access '{}': {}".format(dataset_name, e))
                return

        dims = self.data.ndim

        if dims == 3:
            print("dataset: '{}' has dimensions: {}".format(dataset_name, self.data.shape))
            (dim_a, dim_b, dim_c) = self.data.shape
            completely_empty = True
            nonzero_count = 0

            for loop in range(dim_a):
                summed = self.data[loop].sum()
                if summed > 0:
                    nonzero_count += 1
                    completely_empty = False

            if completely_empty:
                print(" It's completely empty!")
            else:
                if (nonzero_count != dim_a):
                    print("Expected {} populated frames but only {} contained hit(s)!".format(dim_a, nonzero_count))
                else:
                    print("All image(s) populated as expected")
            print("___________________")
        else:
            if dims == 2:
                print("dataset: '{}' has dimensions: {}".format(dataset_name, self.data.shape))
                (dim_a, dim_b) = self.data.shape
                completely_empty = True

                for loop in range(dim_a):
                    summed = self.data[loop].sum()
                    if summed > 0:
                        print(" image{}: {} > 0.0".format(loop, summed))
                        completely_empty = False

                if completely_empty:
                    print(" It's completely empty!")
                print("___________________")
            else:
                print("Unexpected dataset: '{}' dimensions: {} shape: {}".format(dataset_name, dims, self.data.shape))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", type=str, default='test_2_000001.h5', dest="filename",
                        help="Filename of the datatype to read in")
    args = parser.parse_args()

    checker = DatasetChecker()

    datasets = ['pixel_spectra', 'raw_frames', 'spectra_bins', 'summed_spectra']
    for dataset_name in datasets:
        checker.check_empty_frames(dataset_name)
    # checker.check_if_empty()

# with h5py.File(filename, "r") as data_file:
#     print("Keys: {} ({})".format(data_file.keys(), type(data_file.keys())))
# Keys: <KeysViewHDF5 ['pixel_spectra', 'processed_frames', 'raw_frames', 'spectra_bins', 'summed_spectra']> (<class 'h5py._hl.base.KeysViewHDF5'>)
