# -*- coding: utf-8 -*-
# Copyright(c) 2023 UNITED KINGDOM RESEARCH AND INNOVATION
# Electronic System Design Group, Technology Department,
# Science and Technology Facilities Council
# Licensed under the BSD 3-Clause license. See LICENSE file in the project root for details.
"""Helper functions for operating on auto-generated :obj:`dict` imported from :mod:`rdma_control.RDMA_REGISTERS`.

.. important::

   Usually these helper functions will only be wrapped in class methods and functions. General end-users are not
   expected to operate on registers at this lower level.
"""
def calc_shiftr(mask):
    """Calculates the number of bits to shift right to give actual value from a given mask.

    Operates on 32 bit registers.

    Args:
        mask (:obj:`int`): The bit mask, usually returned from :mod:`rdma_control.RDMA_REGISTERS` register/field
            descriptions.

    Returns:
        :obj:`int`: The number of bits required to shift right to get the real value of the masked register/field.
    """
    shift = 0
    temp_mask = mask
    for x in range(0, 32):
        if not (mask >> x) % 2:
            temp_mask = mask >> x
        else:
            shift = x
            break
    return shift


def get_mmap_info(mmap_dict, extended=False):
    """Prints memory-map information, extracted from :obj:`dict` declared in :mod:`rdma_control.RDMA_REGISTERS`.

    Args:
        mmap_dict (:obj:`dict`): declared in :mod:`rdma_control.RDMA_REGISTERS`.
        extended (:obj:`bool`, optional): Included description in returned info. Default: `False`.

    Returns:
        Nothing.
    """
    fields = [ f['name'] for f in mmap_dict['fields'] ]
    addr = f"0x{mmap_dict['addr']:08X}"
    print(f"[{mmap_dict['name']}]: Address: {addr} | Fields: {fields} | Reset: {mmap_dict['reset_value']}")
    if extended:
        print(f"     Description: <{mmap_dict['description']}>")


def get_mmap_field_info(mmap_dict, extended=False):
    """Prints memory-map field information, extracted from :obj:`dict` declared in :mod:`rdma_control.RDMA_REGISTERS`.

    Returns information on all found fields.

    Args:
        mmap_dict (:obj:`dict`): declared in :mod:`rdma_control.RDMA_REGISTERS`.
        extended (:obj:`bool`, optional): Included description in returned info. Default: `False`.

    Returns:
        Nothing.

    """
    if mmap_dict['fields']:
        print(f"[{mmap_dict['name']}]:")
        for f in mmap_dict['fields']:
            mask = f"0x{f['mask']:08X}"
            print(f"    [{f['name']}]: Mask: {mask} <{f['shiftr']}> | Size (bits): {f['nof_bits']} | Reset: {f['reset_value']}")
            if extended:
                print(f"     Description: <{f['description']}>")
    else:
        print(f"[{mmap_dict['name']}]: <no fields>")


def get_field(mmap_dict, name):
    """Returns the :obj:`dict` for the given field :obj:`name` in :obj:`mmap_dict` declared in :mod:`rdma_control.RDMA_REGISTERS`.

    Args:
        mmap_dict (:obj:`dict`): declared in :mod:`rdma_control.RDMA_REGISTERS`.
        name (:obj:`str`): Name of field to fetch.

    Returns:
        :obj:`dict`: field if found, otherwise :obj:`None`.

    """
    field = None
    for f in mmap_dict['fields']:
        if f['name'].upper() == name.upper():
            field = f
    return field


def decode_field(mmap_dict, field, d):
    """Decodes a data word, usually returned from a register read operation, and returns value of the given field.

    The data word will be ANDed with the :obj:`dict` `mask` key/value pair and shifted right by the
    :obj:`dict` `shiftr` key/value pair.

    Args:
        mmap_dict (:obj:`dict`): declared in :mod:`rdma_control.RDMA_REGISTERS`.
        field (:obj:`str`): name of register field to decode.
        d (:obj:`int`): data word to extract and decode field value from.

    Returns:
        :obj:`int`: decoded value if :attr:`field` exists, otherwise: `None`

    """
    f = get_field(mmap_dict, field)
    if f is not None:
        return (d & f['mask']) >> f['shiftr']
    else:
        return None


def encode_field(mmap_dict, field, v):
    """Encodes a value by positioning the value into the correct mask position for a given field.

    Args:
        mmap_dict (:obj:`dict`): declared in :mod:`rdma_control.RDMA_REGISTERS`.
        field (:obj:`str`): name of register field to decode.
        v (:obj:`int`): value to encode into the correct mask position.

    Returns:
        :obj:`int`: encoded value if :attr:`field` exists, otherwise: `None`

    """
    f = get_field(mmap_dict, field)
    if f is not None:
        return f['mask'] & (v << f['shiftr'])
    else:
        return None


def set_field(mmap_dict, field, d, v):
    """Sets a field value into the correct mask position within a given data word, usually returned from a register read operation.

    Args:
        mmap_dict (:obj:`dict`): declared in :mod:`rdma_control.RDMA_REGISTERS`.
        field (:obj:`str`): name of register field to decode.
        d (:obj:`int`): data word to modify.
        v (:obj:`int`): value to encode into the correct mask position.

    Returns:
        :obj:`int`: modified value of :attr:`d` if :attr:`field` exists, otherwise: `None`

    """
    return encode_field(mmap_dict, field, v) | clr_field(mmap_dict, field, d)


def clr_field(mmap_dict, field, d):
    """Clears a field value within a given data word, usually returned from a register read operation.

    Args:
        mmap_dict (:obj:`dict`): declared in :mod:`rdma_control.RDMA_REGISTERS`.
        field (:obj:`str`): name of register field to decode.
        d (:obj:`int`): data word to modify.

    Returns:
        :obj:`int`: modified value of :attr:`d` if :attr:`field` exists, otherwise: `None`

    """
    return  d & ~encode_field(mmap_dict, field, 0xFFFFFFFF)
