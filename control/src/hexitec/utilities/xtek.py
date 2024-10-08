# -*- coding: utf-8 -*-
"""
Created on Fri Feb 11 15:29:46 2022

@author: mbbxfnw2, ckd27546
"""

import numpy as np
from ast import literal_eval
from requests.exceptions import ConnectionError

import os
import json
import h5py
import requests
import argparse


def _arg_parser(doc=True):
    """ Arg parser for command line arguments.
    """
    parser = argparse.ArgumentParser(prog='xtek.py')
    parser.add_argument('folder', help='Nikon output data folder')
    parser.add_argument('target', help='IP address of Odin server')
    return parser.parse_args()


def xml_to_dict(file):
    """ Convert .xml file to Python dictionary.
    """
    import xmltodict
    with open(file, 'r') as myfile:
        obj = xmltodict.parse(myfile.read())
    return obj


def xtekct_to_dict(file):
    """ Convert .xtekct file to Python dictionary
    """
    mydict = {}
    with open(file, 'r') as myfile:
        for line in myfile:
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                key = line[1:-1]
                mydict[key] = {}
                current_dict = mydict[key]
            else:
                key, value = line.split('=', maxsplit=1)
                current_dict[key] = value
    return mydict


def ang_to_dict(file):
    """ Convert angles to a dictionary entry.
    """
    mydict = {'rotation_angle': []}
    with open(file, 'r') as myfile:
        # skip header line
        next(myfile)
        for line in myfile:
            angle = ' '.join(line.split(":")[-1].split())
            mydict['rotation_angle'].append(angle)
    return mydict


def _convert_values(value):
    """ Convert values to correct Python types
    """
    if isinstance(value, list):
        value = [_convert_values(v) for v in value]
    elif isinstance(value, dict):
        for key, entry in value.items():
            value[key] = _convert_values(entry)
    try:
        val = literal_eval(value)
    except Exception:
        val = value
    return str(val) if isinstance(val, type(None)) else val


def get_files(path):
    """ Find all files in (sub)folder(s) of .xml, .xtekct or .ang format
    """
    xml = []
    xtekct = []
    ang = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if (file.endswith(".xml")):
                xml.append(os.path.join(root, file))
            elif (file.endswith(".xtekct")):
                xtekct.append(os.path.join(root, file))
            elif (file.endswith(".ang")):
                ang.append(os.path.join(root, file))
    return xml, xtekct, ang


def get_meta_data(path):
    """ Return the complete meta data dictionary
    """
    meta_data = {}
    xml, xtekct, ang = get_files(path)

    for file in xml:
        meta_data.update(xml_to_dict(file))

    for file in xtekct:
        meta_data.update(xtekct_to_dict(file))

    for file in ang:
        meta_data.update(ang_to_dict(file))

    return meta_data


def save_dict_to_hdf5(mydict, path):
    filename = os.path.join(path, "meta_full.h5")

    with h5py.File(filename, 'w') as h5file:
        save_dict_contents_to_group(h5file, '/', mydict)


def put_data(target, data):
    try:
        url = f"http://{target}:8888/api/0.1/hexitec/xtek_meta"
        headers = {'Content-type': 'application/json'}
        resp = requests.put(url, headers=headers, data=json.dumps(data))
        if resp.status_code != 200:
            print("PUT Error, returned: {}".format(resp.status_code))
        else:
            print("Success")
    except ConnectionError as e:
        print(f"PUT Exception: {e}")


def save_dict_contents_to_group(h5file, path, dic):
    for key, item in dic.items():
        item = _convert_values(item)
        if isinstance(item, list):
            if isinstance(item[0], dict):
                newdict = {}
                for i in range(len(item)):
                    newdict[key + str(i)] = item[i]
                item = newdict
                save_dict_contents_to_group(h5file, path, {})
            else:
                item = np.array(item)
        if isinstance(item, dict):
            save_dict_contents_to_group(h5file, path + key + '/', item)
        else:
            if "AxisPosition" in key:
                print("AccessPosition!")
            else:
                h5file[path + key] = item


if __name__ == "__main__":
    args = _arg_parser()
    path = raw_string = r"{}".format(args.folder)
    target = r"{}".format(args.target)
    if os.path.isdir(path) is False:
        raise Exception("The folder path %s is invalid." % path)
    meta_data = get_meta_data(path)
    put_data(target, meta_data)
