"""
temp_file.py - Testing creating a temporary file to replace 12 Configuration files
"""

import tempfile

def main():

    # The execute_config file is used to wipe any existing config, then load user config
    execute_config = '''
[
    {
        "plugin": 
        {
            "disconnect": "all"
        }
    },
    {
        "execute": 
        {
            "index": "config"
        }
    }
]'''

    print("Creating execute config sequence, temporary file...")

    execute_temp = tempfile.NamedTemporaryFile(mode='w+t')
    execute_temp.delete = False


    # Put together the execute sequence file 
    try:
        print("Execute config file:", execute_temp)
        print("Name of the file is:", execute_temp.name)
        execute_temp.writelines(execute_config)
    finally:
        print("Closing execute's temp file")
        execute_temp.close()


    # ---------------- Section for the store sequence ---------------- #

    store_sequence_preamble = '''
[
    {
        "store": 
        {
            "index": "temp", 
            "value":
            [
                {
                    "fr_setup": {
                        "fr_ready_cnxn": "tcp://127.0.0.1:5001",
                        "fr_release_cnxn": "tcp://127.0.0.1:5002"
                    }
                },'''

    plugin_template = '''
    '''

    a = '''
                {
                    "plugin": {
                        "load": {
                            "index": "hdf",
                            "name": "FileWriterPlugin",
                            "library": "/u/ckd27546/develop/projects/odin-demo/install/lib/libHdf5Plugin.so"
                        }
                    }
                },
                {
                    "plugin": {
                        "connect": {
                            "index": "reorder",
                            "connection": "frame_receiver"
                        }
                    }
                },'''

    b = '''
                {
                    "reorder": {
                        "raw_data": false,
            			"sensors_layout": "2x2"
                    }
                },'''


    store_preamble = '''
[
    {
        "store":
    	{
            "index": "temp", 
            "value":
            [
                {
                    "fr_setup": {
                        "fr_ready_cnxn": "tcp://127.0.0.1:5001",
                        "fr_release_cnxn": "tcp://127.0.0.1:5002"
                    }
                }
            ]
        }
    }
]'''

    store_temp = tempfile.NamedTemporaryFile(mode='w+t')
    store_temp.delete = False

    # Put together the store sequence file
    try:
        print("Created file is:", store_temp)
        print("Name of the file is:", store_temp.name)
        store_temp.writelines("[\n")
        store_temp.writelines("   Hello?\n")
        store_temp.writelines("]\n")



        store_temp.writelines(store_preamble)
    finally:
        print("Closing store's temp file")
        store_temp.close()

if __name__ == '__main__':
    main()
