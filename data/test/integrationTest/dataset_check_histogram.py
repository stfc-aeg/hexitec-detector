import h5py
import numpy as np
import argparse

from nose.tools import assert_equals, assert_true, assert_false,\
    assert_equal, assert_not_equal


class DatasetChecker:

    def __init__(self, args):

        # open file
        # read datasets into a variable of some sort
        with h5py.File(args.filename, "r") as data_file:
            print("Keys: {}".format(data_file.keys()))

            self.data = np.array(data_file["pixel_spectra"])

    def check_none_zero_values(self):
        """Look through pixel_spectra noting all non-zero values."""
        hits = -1
        if (len(self.data.shape) == 3):
            hits = 0
            frames = self.data.shape[0]
            pixels = self.data.shape[1]
            bins = self.data.shape[2]
            for i in range(frames):
                for j in range(pixels):
                    for k in range(bins):
                        value = self.data[i][j][k]
                        if value > 0:
                            hits += 1
                print("self.data[{}][{}][{}]; Sum so far = {}".format(i, j, k, hits))
        return hits



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", type=str, default='test_2_000001.h5', dest="filename",
                        help="Filename of whose pixel_spectra dataset will be examined")
    # parser.add_argument("--dataset", type=str, default="processed_frames", dest="dataset_name",
    #                     help="Name of the dataset required")
    args = parser.parse_args()

    checker = DatasetChecker(args)

    print(" File: {} Non-zero values: {}".format(args.filename, np.count_nonzero(checker.data)))
    hits = checker.check_none_zero_values()
    print(" File: {} Non-zero values: {}".format(args.filename, hits))
