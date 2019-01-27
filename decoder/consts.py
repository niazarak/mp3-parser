import enum


class Standards(enum.IntEnum):
    MPEG_1 = 3
    MPEG_2 = 2
    MPEG_25 = 0


class ChannelMode(enum.IntEnum):
    Stereo = 0
    JointStereo = 1
    Dual = 2
    Mono = 3


class WindowType:
    Forbidden = 0
    Start = 1
    Short = 2
    End = 3


class ScaleFactorStep:
    Size2 = 0
    SizeV2 = 1


#   MPEG1 	MPEG2 	MPEG2.5
SAMPLERATE_INDEX = [
    [44100, 22050, 11025],  # | 00
    [48000, 24000, 12000],  # | 01
    [32000, 16000, 8000],  # |  10
    ['r', 'r', 'r'],  # |       11
]

#   MPEG1 	MPEG2 	MPEG2.5
SAMPLE_INDEX = [
    ['r', 'r', 'r'],
    [1152, 576, 576],
    [1152, 1152, 1152],
    [384, 384, 384],
]

SCALE_FACTOR_INDICES = {
    44100: (
        [0, 4, 8, 12, 16, 20, 24, 30, 36, 44, 52, 62, 74, 90,
         110, 134, 162, 196, 238, 288, 342, 418, 576],
        [0, 4, 8, 12, 16, 22, 30, 40, 52, 66, 84, 106, 136, 192]
    ),
    48000: (
        [0, 4, 8, 12, 16, 20, 24, 30, 36, 42, 50, 60, 72, 88,
         106, 128, 156, 190, 230, 276, 330, 384, 576],
        [0, 4, 8, 12, 16, 22, 28, 38, 50, 64, 80, 100, 126, 192]
    ),
    32000: (
        [0, 4, 8, 12, 16, 20, 24, 30, 36, 44, 54, 66, 82, 102,
         126, 156, 194, 240, 296, 364, 448, 550, 576],
        [0, 4, 8, 12, 16, 22, 30, 42, 58, 78, 104, 138, 180, 192]
    ),
}
