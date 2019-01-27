import struct
import bitstring

ID3V1_MAGIC = b'TAG'
ID3V2_MAGIC = b'ID3'


def decode_synchsafe(safe_size):
    return (((safe_size & 0x7f000000) >> 3)
            | ((safe_size & 0x007f0000) >> 2)
            | ((safe_size & 0x00007f00) >> 1)
            | (safe_size & 0x0000007f))


GENRES = [
    "Blues", "Classic Rock", "Country", "Dance", "Disco", "Funk", "Grunge",
    "Hip-Hop", "Jazz", "Metal", "New Age", "Oldies", "Other", "Pop", "R&B",
    "Rap", "Reggae", "Rock", "Techno", "Industrial", "Alternative", "Ska",
    "Death Metal", "Pranks", "Soundtrack", "Euro-Techno", "Ambient",
    "Trip-Hop", "Vocal", "Jazz+Funk", "Fusion", "Trance", "Classical",
    "Instrumental", "Acid", "House", "Game", "Sound Clip", "Gospel", "Noise",
    "AlternRock", "Bass", "Soul", "Punk", "Space", "Meditative",
    "Instrumental Pop", "Instrumental Rock", "Ethnic", "Gothic", "Darkwave",
    "Techno-Industrial", "Electronic", "Pop-Folk", "Eurodance", "Dream",
    "Southern Rock", "Comedy", "Cult", "Gangsta", "Top 40", "Christian Rap",
    "Pop/Funk", "Jungle", "Native American", "Cabaret", "New Wave",
    "Psychadelic", "Rave", "Showtunes", "Trailer", "Lo-Fi", "Tribal",
    "Acid Punk", "Acid Jazz", "Polka", "Retro", "Musical", "Rock & Roll",
    "Hard Rock", "Folk", "Folk-Rock", "National Folk", "Swing", "Fast Fusion",
    "Bebob", "Latin", "Revival", "Celtic", "Bluegrass", "Avantgarde",
    "Gothic Rock", "Progressive Rock", "Psychedelic Rock", "Symphonic Rock",
    "Slow Rock", "Big Band", "Chorus", "Easy Listening", "Acoustic", "Humour",
    "Speech", "Chanson", "Opera", "Chamber Music", "Sonata", "Symphony",
    "Booty Bass", "Primus", "Porn Groove", "Satire", "Slow Jam", "Club",
    "Tango", "Samba", "Folklore", "Ballad", "Power Ballad", "Rhythmic Soul",
    "Freestyle", "Duet", "Punk Rock", "Drum Solo", "A capella", "Euro-House",
    "Dance Hall",
]


class MetaID3V1:
    def __init__(self, title, artist, album, year, comment, genre):
        self.title = title.decode('ISO-8859-1').strip('\u0000')
        self.artist = artist.decode('ISO-8859-1').strip('\u0000')
        self.album = album.decode('ISO-8859-1').strip('\u0000')
        self.year = year
        self.comment = comment.decode('ISO-8859-1').strip('\u0000')
        self.genre = GENRES[genre] if genre < len(GENRES) else "Unknown"

    def print(self):
        print("MetaID3V1 Tag")
        print("Title:", self.title)
        print("Artist:", self.artist)
        print("Album:", self.album)
        print("Year:", self.year)
        print("Comment:", self.comment)
        print("Genre:", self.genre)


def parse_id3v1(header, stream):
    """header = 4 first bytes!!!"""
    data = header + stream.read(124)
    metadata = MetaID3V1(data[3:33], data[33:63], data[63:93],
                         data[93:97], data[97:127], data[127])
    return metadata


class MetaID3V2:
    def __init__(self, version, flags):
        self.version = version
        self.unsync = bool(flags & 0b1000_0000)
        self.extended_header = bool(flags & 0b0100_0000)
        self.experimental = bool(flags & 0b0010_0000)

        self.title = None
        self.compositor = None
        self.performer_1 = None
        self.year = None
        self.album = None
        self.track = None
        self.album_image_bytes: bytes = None
        self.encoder = None
        self.copyright = None

    def append_frame(self, tag, flags, data):
        if tag in frame_parsers:
            frame_parsers[tag](self, flags, data)

    def is_version_supported(self):
        return self.version == 0x0300 or self.version == 0x0400

    def print(self):
        print("MetaID3V2 version:", self.version)
        print("MetaID3V2 has album image:", self.album_image_bytes is None)
        print("MetaID3V2 extended header:", self.extended_header)
        print("MetaID3V2 unsynchronization:", self.unsync)
        print("MetaID3V2 experimental:", self.experimental)


ENCODINGS = [
    ('ISO-8859-1', 1), ('UTF-16', 2), ('UTF-16BE', 2), ('UTF-8', 1)
]


def parse_apic(meta: MetaID3V2, flags, data):
    stream = bitstring.BitStream(data)
    encoding = ENCODINGS[stream.read('int:8')]

    mime = b""
    while True:
        tmp = stream.read('bytes:1')
        if tmp != b"\x00":
            mime += tmp
        else:
            break

    pic_type = stream.read('bytes:1')

    description = b''
    while True:
        tmp = stream.read('bytes:' + str(encoding[1]))
        if tmp != b'\x00' * encoding[1]:
            description += tmp
        else:
            break

    meta.album_image_bytes = data[stream.bytepos:]


def parse_text_frame(data):
    stream = bitstring.BitStream(data)
    encoding = ENCODINGS[stream.read('int:8')]
    data = b''
    while stream.bytepos < stream.len // 8:
        tmp = stream.read('bytes:' + str(encoding[1]))
        if tmp != b'\x00' * encoding[1]:
            data += tmp
        else:
            break
    return data.decode(encoding[0])


def parse_tcom(meta: MetaID3V2, flags, data):
    meta.compositor = parse_text_frame(data)


def parse_talb(meta: MetaID3V2, flags, data):
    meta.album = parse_text_frame(data)


def parse_tit2(meta: MetaID3V2, flags, data):
    meta.title = parse_text_frame(data)


def parse_tpe1(meta: MetaID3V2, flags, data):
    meta.performer_1 = parse_text_frame(data)


def parse_tyer(meta: MetaID3V2, flags, data):
    meta.year = parse_text_frame(data)


def parse_tsse(meta: MetaID3V2, flags, data):
    meta.encoder = parse_text_frame(data)


def parse_trck(meta: MetaID3V2, flags, data):
    meta.track = parse_text_frame(data)


def parse_tcop(meta: MetaID3V2, flags, data):
    meta.copyright = parse_text_frame(data)


frame_parsers = {
    "APIC": parse_apic,
    "TCOM": parse_tcom,
    "TALB": parse_talb,
    "TIT2": parse_tit2,
    "TPE1": parse_tpe1,
    "TYER": parse_tyer,
    "TDRC": parse_tyer,
    "TSSE": parse_tsse,
    "TRCK": parse_trck,
    "TCOP": parse_tcop,
}


def parse_id3v2(header, stream):
    """header = 4 first bytes!!!"""
    header = header + stream.read(6)
    tag = header[0:3]
    version, flags, safe_size = struct.unpack('>HBI', header[3:])

    meta = MetaID3V2(version, flags)

    size = decode_synchsafe(safe_size)

    data = stream.read(size)
    # print(data)
    if not meta.is_version_supported():
        return meta

    parse_id3v2_frames(data, meta, size, version)

    return meta


def parse_id3v2_frames(data, meta, size, version):
    frame_stream = bitstring.BitStream(data)
    while frame_stream.bytepos <= size - 4:
        frame_id = frame_stream.read('bytes:4')
        if frame_id == b'\x00\x00\x00\x00':
            break
        frame_id = frame_id.decode()
        frame_size = frame_stream.read('uint:32')
        if version == 0x0400:
            frame_size = decode_synchsafe(frame_size)

        frame_flags = frame_stream.read('bytes:2')
        frame_data = frame_stream.read('bytes:' + str(frame_size))

        print(frame_id)

        meta.append_frame(frame_id, frame_flags, frame_data)
