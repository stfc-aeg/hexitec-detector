
import sys

HEX_ASCII_CODE = [0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
                0x41, 0x42, 0x43, 0x44, 0x45, 0x46]

DAC_SCALE_FACTOR = 0.732

def convert_aspect_exponent_to_dac_value(exponent):
    ''' 
    Converts aspect formats to fit dac format
    Aspect's exponent format looks like: 1,003000E+2
    Convert to float (eg: 100.3), rounding to nearest 
    int before scaling to fit DAC range
    '''
    number_string = str(exponent)
    number_string = number_string.replace(",", ".")
    number_float = float(number_string)
    number_int = int(round(number_float))
    number_scaled = int(number_int // DAC_SCALE_FACTOR)
    return number_scaled

def make_list_hexadecimal(value):
    value_hexadecimal = []
    for val in value:
        value_hexadecimal.append("0x%x" % val)
    return value_hexadecimal


def convert_to_aspect_format(value):
    '''  Converts integer to Aspect's hexadecimal notation
            e.g. 31 (0x1F) -> 0x31, 0x46
    '''
    hex_string  = "{:02x}".format(value)
    high_string = hex_string[0]
    low_string  = hex_string[1]
    high_int    = int(high_string, 16)
    low_int     = int(low_string, 16)
    high_encoded = HEX_ASCII_CODE[high_int]
    low_encoded = HEX_ASCII_CODE[low_int]
    return high_encoded, low_encoded


def t(umid_value):
    # Valid value, within range
    umid_high = (umid_value >> 8) & 0x0F
    umid_low = umid_value & 0xFF
    umid  = [0x30, 0x35, 0x35, 0x35]
    umid[0], umid[1] = convert_to_aspect_format(umid_high)
    umid[2], umid[3] = convert_to_aspect_format(umid_low)
    return umid


if __name__ == '__main__':
    # print(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    # calculate_frame_rate(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))

    idx='1,000000E+0'
    print(idx, " -> ", make_list_hexadecimal(t(convert_aspect_exponent_to_dac_value(idx))))
    idx='10,00000E+0'
    print(idx, " -> ", make_list_hexadecimal(t(convert_aspect_exponent_to_dac_value(idx))))
    idx='1,000000E+1'
    print(idx, " -> ", make_list_hexadecimal(t(convert_aspect_exponent_to_dac_value(idx))))
    idx='1,000000E+2'
    print(idx, " -> ", make_list_hexadecimal(t(convert_aspect_exponent_to_dac_value(idx))))
    idx='1,000000E+3'
    print(idx, " -> ", make_list_hexadecimal(t(convert_aspect_exponent_to_dac_value(idx))))
    idx='1000,000E+0'
    print(idx, " -> ", make_list_hexadecimal(t(convert_aspect_exponent_to_dac_value(idx))))
