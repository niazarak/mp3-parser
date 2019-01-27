import struct

from . import sideinfo, consts

SYNC_WORD = b'\xff'

LAYER_1 = 3
LAYER_2 = 2
LAYER_3 = 1

#    V1,L1    V1,L2   V1,L3   V2,L1   V2, L2 & L3
bitrate_index = [
    ['free', 'free', 'free', 'free', 'free'],  # 0b0000
    [32, 32, 32, 32, 8],  # |                    0b0001
    [64, 48, 40, 48, 16],  # |                   0b0010
    [96, 56, 48, 56, 24],  # |                   0b0011
    [128, 64, 56, 64, 32],  # |                  0b0100
    [160, 80, 64, 80, 40],  # |                  0b0101
    [192, 96, 80, 96, 48],  # |                  0b0110
    [224, 112, 96, 112, 56],  # |                0b0111
    [256, 128, 112, 128, 64],  # |               0b1000
    [288, 160, 128, 144, 80],  # |               0b1001
    [320, 192, 160, 160, 96],  # |               0b1010
    [352, 224, 192, 176, 112],  # |              0b1011
    [384, 256, 224, 192, 128],  # |              0b1100
    [416, 320, 256, 224, 144],  # |              0b1101
    [448, 384, 320, 256, 160],  # |              0b1110
    ['bad', 'bad', 'bad', 'bad', 'bad'],  # |    0b1111
]

SAMPLE_COLUMN_MAP = {
    consts.Standards.MPEG_1: 0,
    consts.Standards.MPEG_2: 1,
    consts.Standards.MPEG_25: 2
}


class Header:
    def __init__(self, standart, layer, protection, bitrate, samplerate,
                 padding, private, channel_mode, extension, copyright,
                 is_original, emphasis):
        self.standart = consts.Standards(standart)
        self.layer = layer
        self.protection = not bool(protection)
        self.bitrate = bitrate
        self.samplerate = samplerate
        self.padding = padding
        self.private = private
        self.channel_mode = consts.ChannelMode(channel_mode)
        self.extension = extension
        self.copyright = copyright
        self.is_original = is_original
        self.emphasis = emphasis

        self.frame_size = self.calc_frame_size()
        self.frame_length = self.calc_frame_length()

    def print(self):
        print_standart(self.standart)
        print_layer(self.layer)
        print("Frame bitrate:", self.bitrate)
        print("Frame samplerate:", self.samplerate)
        print("Frame channel_mode:", self.channel_mode)
        print("Frame copyrighted:", self.copyright)
        print("Frame is original:", self.is_original)
        print("Frame size:", self.frame_size)
        print("Frame length:", self.frame_length)

    @property
    def data_length(self):
        return self.frame_length - 4

    def channels_count(self):
        return 1 if self.channel_mode == 3 else 2

    def use_middle_side_stereo(self):
        if self.channel_mode == consts.ChannelMode.JointStereo:
            return self.extension & 0x2 != 0
        else:
            return False

    def use_intensity_stereo(self):
        if self.channel_mode == consts.ChannelMode.JointStereo:
            return self.extension & 0x1 != 0
        else:
            return False

    def calc_sideinfo_size(self):
        if self.standart == consts.Standards.MPEG_1:
            if self.channel_mode == consts.ChannelMode.Mono:
                return 17
            else:
                return 32
        else:
            if self.channel_mode == consts.ChannelMode.Mono:
                return 8
            else:
                return 17

    def calc_frame_size(self) -> int:
        sample_col = consts.SAMPLE_INDEX[self.layer]
        return sample_col[SAMPLE_COLUMN_MAP[self.standart]]

    def calc_frame_length(self) -> int:
        if self.layer == LAYER_1:
            raw_len = 12 * self.bitrate * 1000 / self.samplerate
            return (raw_len + self.padding) * 4
        else:
            raw_len = self.frame_size * self.bitrate * 125 / self.samplerate
            return int(raw_len + self.padding)


class FirstFrameData:
    def __init__(self, tag, flags, frames_count, file_length):
        self.tag = tag
        self.flags = flags
        self.frames_count = struct.unpack('>L', frames_count)[0]
        self.file_length = struct.unpack('>L', file_length)[0]

    def print(self):
        print("Main bytes flags:", self.flags)
        print("Main bytes frames count:", self.frames_count)
        print("Main bytes file length:", self.file_length)


class FrameDecoder:
    def __init__(self):
        self.first_frame_data = None
        self.prev_frame_main_bytes = None

    def parse_frame(self, raw_header, file):
        header = header_from_bytes(raw_header)
        if header.protection:  # header HAS protection!!! todo: process crc
            print("Protection enabled!")

        data = file.read(header.data_length)
        si: sideinfo.Sideinfo = self.decode_sideinfo(header, data)
        frame_main_bytes = data[si.size:]
        if not self.first_frame_data:
            self.first_frame_data = \
                self.decode_first_frame_data(frame_main_bytes)
            self.prev_frame_main_bytes = frame_main_bytes
        # else:
        #     offset = si.main_data_start
        #     self.decode_data(header, si,
        #         self.prev_frame_main_bytes[-offset:] + frame_main_bytes)
        #     self.prev_frame_main_bytes = frame_main_bytes
        return Frame(header)

    def decode_first_frame_data(self, first_frame_data_bytes):
        xing_tag = len(b'Xing')
        return FirstFrameData(
            first_frame_data_bytes[:xing_tag],
            first_frame_data_bytes[xing_tag:xing_tag + 4],
            first_frame_data_bytes[xing_tag + 4:xing_tag + 8],
            first_frame_data_bytes[xing_tag + 8:xing_tag + 12]
        )

    def decode_sideinfo(self, header, data_bytes) -> sideinfo.Sideinfo:
        return sideinfo.decode_sideinfo(header, data_bytes)


def header_from_bytes(raw_header) -> Header:
    header = struct.unpack('>H2B', raw_header)
    sync_word = (header[0] & 0b1111_1111_1110_0000) >> 5

    standart = (header[0] & 0b0001_1000) >> 3
    layer = (header[0] & 0b0000_0110) >> 1
    protection = (header[0] & 0b0000_0001)

    raw_bitrate = (header[1] & 0b1111_0000) >> 4
    bitrate = calc_bitrate(standart, layer, raw_bitrate)

    raw_samplerate = (header[1] & 0b0000_1100) >> 2
    samplerate = calc_samplerate(standart, raw_samplerate)

    padding = (header[1] & 0b0000_0010) >> 1
    private = (header[1] & 0b0000_0001)

    channel_mode = (header[2] & 0b1100_0000) >> 6
    extension = (header[2] & 0b0011_0000) >> 4
    copyright = (header[2] & 0b0000_1000) >> 3
    is_original = (header[2] & 0b0000_0100) >> 2
    emphasis = (header[2] & 0b0000_0011)
    return Header(standart, layer, protection, bitrate, samplerate, padding,
                  private, channel_mode, extension, copyright, is_original,
                  emphasis)


def calc_bitrate(standart: int, layer_desc: int, bitrate_raw: int) -> int:
    if standart == consts.Standards.MPEG_1:
        if layer_desc == LAYER_1:
            col = 0
        elif layer_desc == LAYER_2:
            col = 1
        elif layer_desc == LAYER_3:
            col = 2
        else:
            raise BaseException
    elif standart == consts.Standards.MPEG_2 \
            or standart == consts.Standards.MPEG_25:
        if layer_desc == LAYER_1:
            col = 3
        elif layer_desc == LAYER_2 or layer_desc == LAYER_3:
            col = 4
        else:
            raise BaseException
    else:
        raise BaseException
    return bitrate_index[bitrate_raw][col]


def calc_samplerate(standart: int, samplerate_raw: int) -> int:
    sample_col = consts.SAMPLERATE_INDEX[samplerate_raw]
    return sample_col[SAMPLE_COLUMN_MAP[standart]]


def print_standart(standart):
    pretty_map = {3: 1, 2: 2, 0: 2.5}
    if standart in pretty_map.keys():
        print('Standart:', bin(standart), f'(MPEG {pretty_map[standart]})')
    else:
        raise BaseException


def print_layer(layer):
    pretty_map = {3: 1, 2: 2, 1: 3}
    if layer in pretty_map.keys():
        print('Layer:', bin(layer), f'(Layer {pretty_map[layer]})')
    else:
        raise BaseException


class Frame:
    def __init__(self, header: Header, data=None):
        self.header = header
        self.data = data
