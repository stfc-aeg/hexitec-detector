import h5py
import glob
import sys

print(f"sys.argv: ", sys.argv)
prefix = sys.argv[1]
print(f"1.prefix: {prefix}")
files_found = glob.glob(f"/tmp/{prefix}_*.h5")
source_files = (sorted(files_found))
# prefix = "/tmp/08-11-001" #'25-08-005'
# print(f"2.prefix: {prefix}")
print(f"1.source_files: {source_files}")
# source_files2 = [f'{prefix}_{idx:06d}.h5' for idx in range(2)]   # range(4)]
# print(f"2.source_files: {source_files2}")
num_sources = len(source_files)
print(f"1.num_sources: {num_sources}")
dest_file = f'{prefix}.h5'
# sys.exit()
dataset_names = []
dtype = None
inshape = None

# Open first file to check how many datasets
with h5py.File(source_files[0]) as file:
    number_of_datasets = len(file.keys())
    for dataset in file:  # Each dataset in current file
        dataset_names.append(dataset)
print(f"first file contains: {dataset_names} dataset_names")

vsources = []

num_frames = [0 for idx in range(number_of_datasets)]
dtype = [0 for idx in range(number_of_datasets)]
inshape = [0 for idx in range(number_of_datasets)]
print(f"Number of files: {num_sources}")
print(f"source files: {source_files}")
print("+++++++ Loop over files, dsets..")
# Loop over all source files, datasets
for source in source_files: # Go through all .h5 files
    with h5py.File(source) as file: # Go through each file
        if number_of_datasets != len(file.keys()):
            e = f"Expected {number_of_datasets} but {source} contains {len(file.keys())} datasets!"
            print(e, "\nAborting..")
            sys.exit()

        index = 0
        for dataset in file:  # Each dataset in current file
            dset = file[dataset]
            
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

            print(f" {dataset}, shape={dset.shape}")
            vsources.append(h5py.VirtualSource(source, dataset, shape=dset.shape))
            index += 1

layout = []

dataset_index = [0 for idx in range(number_of_datasets)]
index = -1
print("--- Iterate through all datasets")
for dataset in dataset_names:  # Iterate through all datasets
    index += 1
    # if dataset == "pixel_spectra":
    #     print("skip'g ", dataset)
    #     continue
    # if dataset != "pixel_spectra":
    #     print("skip'g ", dataset)
    #     continue

    # print(f"dataset '{dataset}' index: {index} in {num_frames} shape: {len(inshape[index])}")

    # 
    if len(inshape[index]) == 2:
        n = 1;print("adjusting dimensions..")
    else:
        n = 0
    print(f"*** dataset: '{dataset}' Shape: {inshape[index]} n: {n}")
    if dataset == "spectra_bins":
        outshape = (inshape[index][1-n], inshape[index][2-n])
    elif dataset == "pixel_spectra":
        outshape = (num_frames[index], inshape[index][1],
                    inshape[index][2], inshape[index][3])
    else:
        outshape = (num_frames[index], inshape[index][1-n], inshape[index][2-n])
        # print(f" num_frames: {num_frames} index: {index}")
        # print(f" inshape: {inshape}")
    print(f" outshape = {outshape}")

    layout = h5py.VirtualLayout(shape=outshape, dtype=dtype[index])

    for (idx, vsource) in enumerate(vsources):
        current_index = idx % number_of_datasets
        if current_index == index:
            temp_idx = dataset_index[current_index]

            if dataset == "spectra_bins":
                print(f" spectra_bins, layout[, ] = layout[, ]")
                layout[:, :] = vsource
            elif dataset == "pixel_spectra":
                print(f" pixel_spectra; layout: [{temp_idx}:{num_frames[index]}:{num_sources}, :, :, :]")
                layout[temp_idx:num_frames[index]:num_sources, :, :, :] = vsource
            else:
                print(f" all other dsets, layout: [{temp_idx}:{num_frames[index]}:{num_sources}, :, :]")
                layout[temp_idx:num_frames[index]:num_sources, :, :] = vsource
                

            dataset_index[current_index] += 1

    with h5py.File(dest_file, 'a', libver='latest') as outfile:
        outfile.create_virtual_dataset(dataset_names[index], layout)
