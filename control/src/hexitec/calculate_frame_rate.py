
import sys

def calculate_frame_rate(row_s1, s1_sph, sph_s2):
    """
    Calculate variables to determine frame rate 
    (as defined by spreadsheet ASICTimingRateDefault.xlsx)
    """
    # Calculate RowReadClks
    ADC_Clk     = 21250000      # B2
    ASIC_Clk1   = ADC_Clk * 2.0   # B3 = B2 * 2
    ASIC_Clk2   = 1 / ASIC_Clk1 # B4 = 1 / B3
    # print(ASIC_Clk1)
    # print(ASIC_Clk2)
    Rows        = 80            # B6; Hard coded yes?
    Columns     = 20            # B7; Hard coded too?
    WaitCol     = 1             # B9; Hard coded too?
    WaitRow     = 8             # B10
    # row_s1      = 5             # B12 from hexitecVSR file
    # s1_sph      = 1             # B13 from file
    # sph_s2      = 5             # B14 from file
    
    RowReadClks     = ((Columns + WaitCol + row_s1 + s1_sph + sph_s2) \
                                                        * 2) + 10   # B16 = ((B7 + B9 + B12 + B13 + B14) * 2) + 10
    frameReadClks   = (Rows * RowReadClks) + 4 + (WaitRow * 2)      # B18 = B6 * B16 + 4 + (B10 * 2)

    frame_time      = ((frameReadClks * 3) + 2) * (ASIC_Clk2 / 3)   # B20 = (B18 * 3) + 2) * (B4 / 3)
    frame_rate      = 1 / frame_time                                # B21 = 1 / B20
    
    print(" frame_rate: %s " % frame_rate)
    data_rate_b = 160*160*2 * frame_rate
    data_rate_m = data_rate_b / 1000000
    print(" data rate: {:.2f}".format(data_rate_m))

    ###

if __name__ == '__main__':
    print(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    calculate_frame_rate(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
