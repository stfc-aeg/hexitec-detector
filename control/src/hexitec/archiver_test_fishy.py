"""Test script for debugging archiving HDF5 files

Christian Angelsen, STFC Application Engineering
"""
import logging
import sys
from datetime import datetime
import numpy as np
import h5py
import glob
import os


def map_virtual_datasets(filename):
    """Map real datasets into set of virtual datasets."""
    local_dir = "/tmp/"
    logging.debug( "INFO: map_virtual_datasets()")
    logging.debug(f"      Called with file {filename}")
    logging.debug(f"      Local dir is {local_dir}\n")
    # Strip (incoming) path from filename
    file_without_path = os.path.basename(filename)
    # Prepend local path to filename
    filename = os.path.join(local_dir, file_without_path)
    # Determine all files with same prefix
    file_tokenised = filename.split(".h5")
    file_without_extension = file_tokenised[0]
    data_files = f"{file_without_extension}_*.h5"
    files_found = glob.glob(data_files)
    source_files = (sorted(files_found))
    num_sources = len(source_files)
    logging.debug(f"VDS found {num_sources} file(s), namely: {source_files}")
    if num_sources == 0:
        logging.error("Received meta data but no files containing real data")
        return -1
    dest_file = f'{filename}'
    dataset_names = []
    # dtype = None
    # inshape = None
    ps_dset = None
    si_dset = None

    # Open first file to check how many datasets
    try:
        with h5py.File(source_files[0]) as file:
            num_datasets = len(file.keys())
            for dataset in file:  # Each dataset in current file
                # print(f" Found dataset: '{dataset}'")
                dataset_names.append(dataset)
                if dataset == "pixel_spectra":
                    ps_dset = file[dataset]
                    ps_inshape = ps_dset.shape
                    ps_dtype = ps_dset.dtype
                if dataset == "summed_images":
                    si_dset = file[dataset]
                    si_inshape = si_dset.shape
                    si_dtype = si_dset.dtype
    except OSError as e:
        logging.error(f"Error opening data file {source_files[0]}: {e}")
        return -1
    # print(f"first file contains: {dataset_names} dataset_names")

    # Determine 'pixel_spectra' dimensions
    if ps_dset is None:
        logging.error("Couldn't find 'pixel_spectra' dataset in first data file")
        return -1
    pixel_spectra_summed = np.zeros((ps_dset.shape[1], ps_dset.shape[2], ps_dset.shape[3]), dtype=ps_dset.dtype)

    # Determine 'summed_images' dimensions
    if si_dset is None:
        logging.error("Couldn't find 'summed_images' dataset in first data file")
        return -1
    summed_images_summed = np.zeros((si_dset.shape[1], si_dset.shape[2]), dtype=si_dset.dtype)

    vsources = []
    num_frames = [0 for idx in range(num_datasets)]
    dtype = [0 for idx in range(num_datasets)]
    inshape = [0 for idx in range(num_datasets)]
    # pixel_spectra_summed = []
    # print(f"Number of files: {num_sources}, source files: {source_files}")
    # Loop over all source files, datasets
    for source in source_files:     # Go through all .h5 files
        with h5py.File(source) as file:     # Go through each file
            if num_datasets != len(file.keys()):
                e = f"Expected {num_datasets} but {source} has {len(file.keys())} datasets"
                logging.error(e)
                return -2

            index = 0
            for dataset in file:  # Each dataset in current file
                dset = file[dataset]

                if dataset == "pixel_spectra":
                    # print(f"    (vsrc -> {dataset}, shape={dset.shape})")
                    # print(f"dset.shape = {dset.shape}")
                    # print(f"dset.dtype = {dset.dtype}")
                    # print(f"1.ps type: {type(pixel_spectra_summed)} dset type: {type(dset)} shape: {pixel_spectra_summed.shape}")
                    pixel_spectra_summed = np.sum([pixel_spectra_summed, dset[0]], axis=0)
                    # print(f"2.ps type: {type(pixel_spectra_summed)} dset type: {type(dset)} shape: {pixel_spectra_summed.shape}")
                    # print(" Skipping adding to VDS for 'pixel_spectra'")
                    # continue
                if dataset == "summed_images":
                    summed_images_summed = np.sum([summed_images_summed, dset[0]], axis=0)

                # 'spectra_bins' identical across files, need only one instance
                if dataset == "spectra_bins":
                    num_frames[index] = 1
                else:
                    num_frames[index] += dset.shape[0]

                if not inshape[index]:
                    inshape[index] = dset.shape
                if not dtype[index]:
                    dtype[index] = dset.dtype
                else:
                    assert dset.dtype == dtype[index]

                # print(f" *** Adding vsrc -> vsource = '{source}' ds = '{dataset}', shape={dset.shape}")
                vsources.append(h5py.VirtualSource(source, dataset, shape=dset.shape))
                index += 1
    layout = []
    dataset_index = [0 for idx in range(num_datasets)]
    index = -1
    print(f"Dataset names: {dataset_names}")
    print(f"Number of datasets: {num_datasets}")
    print(f"num_frames: {num_frames}")
    print(f"inshape: {inshape}\n")

    print("Determine virtual dataset dimensions and map sources into layout")
    for dataset in dataset_names:  # Iterate through all datasets
        try:
            index += 1

            if len(inshape[index]) == 2:
                n = 1
            else:
                n = 0
            print(f"*idx={index}* dataset: '{dataset}' n_frames: {num_frames[index]} Shape: {inshape[index]} n: {n}")
            if dataset == "spectra_bins":
                outshape = (inshape[index][1-n], inshape[index][2-n])
            elif dataset == "pixel_spectra":
                # print(" pixel_spectra dataset summed, not mapped as VDS - Skipping")
                # continue
                print(f" dataset: 'pixel_spectra' num_frames = {num_frames[index]}")
                print(f" num_frames = {num_frames[index]}")
                print(f" inshape = {inshape[index]}")
                outshape = (num_frames[index], inshape[index][1],
                            inshape[index][2], inshape[index][3])
            else:
                outshape = (num_frames[index], inshape[index][1-n], inshape[index][2-n])
            print(f" DS: {dataset}, outshape = {outshape}")

            # In case user tries to add datasets that already exist in destination file
            d = datetime.now()
            optional_dataset_prefix = f"{d.hour:02}" + ":" + f"{d.minute:02}" + ":" + f"{d.second:02}" + "/"

            layout = h5py.VirtualLayout(shape=outshape, dtype=dtype[index])
        except IndexError as e:
            logging.error(f"Couldn't create virtual layout for dataset '{dataset}': {e}")
            return -2
        # Map sources into layout
        try:
            for (idx, vsource) in enumerate(vsources):
                current_index = idx % num_datasets
                if current_index == index:
                    temp_idx = dataset_index[current_index]

                    if dataset == "spectra_bins":
                        # print(f" spectra_bins, layout[, ] = layout[, ]")
                        layout[:, :] = vsource
                    elif dataset == "pixel_spectra":
                        # print(f" l'out: [{temp_idx}:{num_frames[index]}:{num_sources}, :, :, :]")
                        layout[temp_idx:num_frames[index]:num_sources, :, :, :] = vsource
                    else:
                        # print(f" '{dataset}' l'out: [{temp_idx}:{num_frames[index]}:{num_sources}, :, :] = vsource")
                        layout[temp_idx:num_frames[index]:num_sources, :, :] = vsource
                    dataset_index[current_index] += 1
            with h5py.File(dest_file, 'a', libver='latest') as outfile:
                if dataset_names[index] in outfile.keys():
                    amended_dataset_name = optional_dataset_prefix + dataset_names[index]
                    msg = f"Dataset: '{dataset_names[index]}' already exist in HDF5 file"
                    logging.warning(f"{msg};Amending dataset to '{amended_dataset_name}'")
                    outfile.create_virtual_dataset(amended_dataset_name, layout)
                else:
                    print(f" Creating VDS for dataset: '{dataset_names[index]}' index: {index}")
                    outfile.create_virtual_dataset(dataset_names[index], layout)
                if dataset == "pixel_spectra":
                    print(" *** PS *** Deleting summed 'pixel_spectra' dataset from file")
                    del outfile["pixel_spectra"]
                    print(" Writing summed 'pixel_spectra' dataset into file")
                    # Write summed pixel_spectra as real dataset
                    outfile.create_dataset("pixel_spectra", data=pixel_spectra_summed)
                if dataset == "summed_images":
                    print(" *** SI *** Final check of datasets in file:")
                    num_datasets = len(outfile.keys())
                    print(f" 0.Final file contains {num_datasets} datasets:")
                    for dataset in outfile:  # Each dataset in current file
                        print(f" Found dataset: '{dataset}'")

                    # print(" Deleting summed 'summed_images' dataset from file")
                    del outfile["summed_images"]
                    print(" Writing summed 'summed_images' dataset into file")
                    # Write summed summed_images as real dataset
                    outfile.create_dataset("summed_images", data=summed_images_summed)
        except IndexError as e:
            logging.error(f"Couldn't map virtual dataset ({dataset}) into {dest_file}: {e}")
            return -3
        except BlockingIOError as e:
            logging.error(f"File {dest_file} is locked, couldn't write VDS: {e}")
            return -4
    logging.debug(f"VDS finished mapping virtual datasets into file {dest_file}")
    return 0


if __name__ == '__main__':
    if 1:
        map_virtual_datasets(sys.argv[1])
    # try:
    # except IndexError:
    #     print("Usage:")
    #     print("archiver_test.py <path_and_file.h5>")
