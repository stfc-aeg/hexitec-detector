"""Test disk writing performance, a general inducation."""

import numpy
import time
import h5py
import sys


def test_disc_writing(x, y, images, file_name="testing.h5"):
    """Test disk writing speed(s).

    Create empty numpy array of dims (images, x, y), measuring time to
    write data to disk
    """
    image_array = numpy.zeros((images, x, y))
    for idx in range(images):
        image_array[idx] = numpy.random.uniform(low=1, high=15000, size=(x, y))
    # file_name = "testing.h5"
    theStart = time.time()
    h5f = h5py.File(file_name, 'w')
    h5f.create_dataset('dataset_1', data=image_array)
    h5f.close()
    theEnd = time.time()
    size_of_dataset = len(image_array.tobytes())
    duration = (theEnd - theStart)
    data_rate = size_of_dataset / duration
    print("     FILE WRITING took %s" % duration)
    print("     Data written: %s" % size_of_dataset)
    print("     Data rate: {0:.2f} B/s".format(data_rate))
    print("     Data rate: {0:.2f} MB/s".format(data_rate / 1000000))


if __name__ == '__main__':
    # print(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    try:
        test_disc_writing(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    except IndexError:
        print("Correct usages:")
        print("write_to_disc.py <x> <y> <images>")
        print("write_to_disc.py 160 160 20")
