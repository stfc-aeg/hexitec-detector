"""Convert a comma-separated file containing integer values into a numpy array

Christian Angelsen, STFC Detector Systems Software Group
"""

try:
    import PyQt5
except ImportError:
    print("Script requires python package PyQt5 to be installed!")
    import sys
    sys.exit(1)

import numpy as np
import matplotlib.pyplot as plt

def read_file_into_numpy_array(filename):
  frame = np.loadtxt(filename, delimiter=',', dtype=int)
  print("{}\thas dimensions: {} shape: {} size: {} mean: {}".format(filename, frame.ndim, frame.shape, frame.size, frame.mean()))
  return frame

if __name__ == '__main__':
  filename1 = "TestFrame1and0_80x80.txt"
  filename2 = "TestFrame1and0_80x80_B.txt"
  filename3 = "TestFrame1and0_80x80_C.txt"
  filename4 = "TestFrame1and0_80x80_D.txt"

  # Read each file into a numpy array
  test_frame1 = read_file_into_numpy_array(filename1)
  test_frame2 = read_file_into_numpy_array(filename2)
  test_frame3 = read_file_into_numpy_array(filename3)
  test_frame4 = read_file_into_numpy_array(filename4)

  # "extra credit", visualise the four different frames:
  fig1, ax1 = plt.subplots()
  plt.title('TestFrame1and0_80x80.txt')
  plt.imshow( test_frame1, cmap = 'rainbow' , interpolation = 'bilinear')

  fig2, ax2 = plt.subplots()
  plt.title('TestFrame1and0_80x80_B.txt')
  plt.imshow( test_frame2, cmap = 'rainbow' , interpolation = 'bilinear')

  fig3, ax3 = plt.subplots()
  plt.title('TestFrame1and0_80x80_C.txt')
  plt.imshow( test_frame3, cmap = 'rainbow' , interpolation = 'bilinear')

  fig4, ax4 = plt.subplots()
  plt.title('TestFrame1and0_80x80_D.txt')
  plt.imshow( test_frame4, cmap = 'rainbow' , interpolation = 'bilinear')
  plt.show()
