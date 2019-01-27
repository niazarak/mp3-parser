import bitstring
from . import consts


class Sideinfo:
    def __init__(self, size):
        self.size = size
        self.main_data_start = 0
        self.priv_bits = ''
        self.scale_factor_selection = [[0, 0, 0, 0], [0, 0, 0, 0]]
        self.part_23_length = [[0, 0], [0, 0]]
        self.big_values = [[0, 0], [0, 0]]
        self.global_gain = [[0, 0], [0, 0]]
        self.scalefac_compress = [[0, 0], [0, 0]]
        self.win_switch_flag = [[0, 0], [0, 0]]

        self.block_type = [[0, 0], [0, 0]]
        self.mixed_block_flag = [[0, 0], [0, 0]]
        self.table_select = [[[0, 0, 0], [0, 0, 0]], [[0, 0, 0], [0, 0, 0]]]
        self.subblock_gain = [[[0, 0, 0], [0, 0, 0]], [[0, 0, 0], [0, 0, 0]]]

        self.region0_count = [[0, 0], [0, 0]]
        self.region1_count = [[0, 0], [0, 0]]

        self.preflag = [[0, 0], [0, 0]]
        self.scalefac_scale = [[0, 0], [0, 0]]
        self.count1_table_select = [[0, 0], [0, 0]]
        self.count1 = [[0, 0], [0, 0]]


def decode_sideinfo(header, data_bytes):
    sideinfo_size = header.calc_sideinfo_size()
    sideinfo_bytes = data_bytes[:sideinfo_size]
    # print("Sideinfo:", sideinfo_bytes)

    sideinfo = Sideinfo(sideinfo_size)

    buf = bitstring.BitStream(bytes=sideinfo_bytes)

    def read_bits(count: int):
        return buf.read('uint:' + str(count))

    sideinfo.main_data_start = read_bits(9)
    # print("Sideinfo main data start:", sideinfo.main_data_start)

    if header.channel_mode == consts.ChannelMode.Mono:
        sideinfo.priv_bits = buf.read('bin:5')
    else:
        sideinfo.priv_bits = buf.read('bin:3')
    # print("Sideinfo priv bits:", sideinfo.priv_bits)

    for ch in range(0, header.channels_count()):
        for band in range(0, 4):
            sideinfo.scale_factor_selection[ch][band] = read_bits(1)
    # print('Sideinfo scfsi:', sideinfo.scale_factor_selection)

    # for gr in range(0, 2):
    #     for ch in range(0, header.channels_count()):
    #         sideinfo.part_23_length[gr][ch] = read_bits(12)
    #         sideinfo.big_values[gr][ch] = read_bits(9)
    #         sideinfo.global_gain[gr][ch] = read_bits(8)
    #         sideinfo.scalefac_compress[gr][ch] = read_bits(4)
    #         sideinfo.win_switch_flag[gr][ch] = read_bits(1)
    #         if sideinfo.win_switch_flag[gr][ch] == 1:
    #             sideinfo.block_type[gr][ch] = read_bits(2)
    #             sideinfo.mixed_block_flag[gr][ch] = read_bits(1)
    #             for region in range(0, 2):
    #                 sideinfo.table_select[gr][ch][region] = read_bits(5)
    #             for window in range(0, 3):
    #                 sideinfo.subblock_gain[gr][ch][window] = read_bits(3)
    #             if sideinfo.block_type[gr][ch] == consts.WindowType.Short \
    #                     and sideinfo.mixed_block_flag[gr][ch] == 0:
    #                 sideinfo.region0_count[gr][ch] = 8
    #             else:
    #                 sideinfo.region0_count[gr][ch] = 7
    #             sideinfo.region1_count[gr][ch] = \
    #                 20 - sideinfo.region0_count[gr][ch]
    #         else:
    #             for region in range(0, 3):
    #                 sideinfo.table_select[gr][ch][region] = read_bits(5)
    #             sideinfo.region0_count[gr][ch] = read_bits(4)
    #             sideinfo.region1_count[gr][ch] = read_bits(3)
    #             sideinfo.block_type[gr][ch] = consts.WindowType.Forbidden
    #         sideinfo.preflag[gr][ch] = read_bits(1)
    #         sideinfo.scalefac_scale[gr][ch] = read_bits(1)
    #         sideinfo.count1_table_select[gr][ch] = read_bits(1)
    return sideinfo
