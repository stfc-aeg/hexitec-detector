import h5py
import numpy as np
import argparse

from nose.tools import assert_true, assert_equal


class DatasetChecker:

    def __init__(self, args):

        # open file
        # read datasets into a variable of some sort
        with h5py.File(args.filename, "r") as data_file:
            print("Keys: {}".format(data_file.keys()))

            self.data = np.array(data_file[args.dataset_name])
            self.raw = np.array(data_file["raw_frames"])

            self.spectra = np.array(data_file["summed_spectra"])

    def check_summed_spectra(self):

        expected_spectra = np.zeros(800, dtype=np.uint64)
        # These values are not calculated, simply hardcoded matching pixel spectra:
        # # 2x2:
        # expected_spectra[:5] = np.array([   0, 8960, 3680,    0,  320], dtype=np.uint64)
        # 2x6:
        expected_spectra[:19] = np.array([0,  0, 30, 130, 104, 131, 157, 105, 157, 208, 104, 52, 78, 52, 26, 52, 52, 26, 26], dtype=np.uint64)
        # The first three indexes are of the same (1490), the remaining 7 are empty
        # print("spectra:  ", self.spectra[0][:].sum())
        # print("spectra:  ", self.spectra[1][:].sum())
        # print("spectra:  ", self.spectra[2][:].sum())
        # print("expected: ", expected_spectra[0:24])
        # print(" sum spectra:  ", self.spectra[0].sum())
        # print(" sum exp_spec: ", expected_spectra.sum())
        assert_true(np.array_equal(self.spectra[0], expected_spectra))

    def check_addition_averages(self):

        processed_frame = self.data[0]
        raw_frame = self.raw[0]
        # go through raw_frame
        # if raw pixel = 0, processed should also be 0
        # if not 0, then need to check surrounding pixels for values
        #   if no surrouding values, processed = raw
        # suppose we could just generate what we think the processed frame should be then compare

        # pad with a single 0 on each axis, so that we can still look "around" every pixel
        expected_frame = np.pad(raw_frame, 1, mode='constant')  # frame now shaped (82, 82)
        cols = expected_frame.shape[1]
        rows = expected_frame.shape[0]
        for i in range(rows):
            for j in range(cols):
                pixel = expected_frame[i, j]
                if not pixel == 0:
                    # list the pixels neighbours
                    # this ends up being a 3 by 3 square array with the original pixel in the middle
                    # print("Pixel Position: {}".format((i, j)))
                    neighbours = expected_frame[i - 1:i + 2, j - 1:j + 2]
                    neighbour_sum = np.sum(neighbours)
                    max_pos = np.unravel_index(neighbours.argmax(), neighbours.shape)
                    max_pos = tuple(np.subtract(max_pos, (1, 1)))
                    actual_pos = tuple(np.add((i, j), max_pos))

                    # set all neighbours to 0
                    expected_frame[i - 1:i + 2, j - 1:j + 2] = 0
                    # set pixel @ max_pos to the sum
                    expected_frame[actual_pos[0], actual_pos[1]] = neighbour_sum
                    # print(expected_frame[i - 1:i + 2, j - 1:j + 2])

        # trim the padding back off now that processing is complete
        expected_frame = expected_frame[1:rows-1, 1:cols-1]
        # we now have what the processed frame SHOULD look like when using Addition Plugin
        assert_equal(processed_frame.shape, expected_frame.shape)
        # print("processed:", processed_frame.shape)
        # for i in range(4):
        #     print(processed_frame[i][:15], processed_frame[i][15:30])
        # print("expected:", expected_frame.shape)
        # for i in range(4):
        #     print(expected_frame[i][:15], expected_frame[i][15:30])
        # print("raw:", raw_frame.shape)
        # for i in range(4):
        #     print(raw_frame[i][:15], raw_frame[i][15:30])
        cols = expected_frame.shape[1]
        rows = expected_frame.shape[0]
        disagree = 0
        for i in range(rows):
            for j in range(cols):
                pf = processed_frame[i, j]
                ef = expected_frame[i, j]
                if pf != ef:
                    disagree += 1
                    if disagree < 12:
                        print(" frames differ@ ({}, {}) pf ({}) != ef ({})".format(i, j, pf, ef))
        if disagree > 0:
            print("Disagreed: {}".format(disagree))
        assert_true(np.array_equal(processed_frame, expected_frame))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", type=str, default='test_2_000001.h5', dest="filename",
                        help="Filename of the datatype to read in")
    parser.add_argument("--dataset", type=str, default="processed_frames", dest="dataset_name",
                        help="Name of the dataset required")
    args = parser.parse_args()

    checker = DatasetChecker(args)

    checker.check_addition_averages()
    checker.check_summed_spectra()
