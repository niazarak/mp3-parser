import sys
import os
import unittest

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             os.path.pardir))

from decoder import decoder, consts


class TestDecoder(unittest.TestCase):
    def setUp(self):
        pass

    def test_decode(self):
        with open('tests/files/cool_music_v1.mp3', 'rb') as file:
            decoder.decode(file)

    def test_meta(self):
        meta = decoder.meta.MetaID3V2(0x0300, 0xF)

        test_string = b'\x00\x00\x00\x17\x00\x00\x01\xff\xfe' \
                      b't\x00e\x00s\x00t\x00s\x00t\x00r\x00i\x00n\x00g\x00'
        data = b''.join((map(lambda x: x + test_string, [
            b'TCOM',
            b'TALB',
            b'TIT2',
            b'TPE1',
            b'TYER',
            b'TDRC',
            b'TSSE',
            b'TRCK',
            b'TCOP',
        ])))

        print(data)
        decoder.meta.parse_id3v2_frames(data, meta, len(data), 0x0300)
        self.assertEqual(meta.title, "teststring")
        self.assertEqual(meta.compositor, "teststring")
        self.assertEqual(meta.performer_1, "teststring")
        self.assertEqual(meta.year, "teststring")
        self.assertEqual(meta.album, "teststring")
        self.assertEqual(meta.track, "teststring")
        self.assertEqual(meta.encoder, "teststring")
        self.assertEqual(meta.copyright, "teststring")

    def test_calc_bitrate(self):
        self.assertEqual(decoder.frame.calc_bitrate(
            consts.Standards.MPEG_1, decoder.frame.LAYER_1, 0b1110),
            448,
        )
        self.assertEqual(decoder.frame.calc_bitrate(
            consts.Standards.MPEG_1, decoder.frame.LAYER_2, 0b1110),
            384,
        )
        self.assertEqual(decoder.frame.calc_bitrate(
            consts.Standards.MPEG_1, decoder.frame.LAYER_3, 0b1110),
            320,
        )
        self.assertEqual(decoder.frame.calc_bitrate(
            consts.Standards.MPEG_2, decoder.frame.LAYER_1, 0b1110),
            256,
        )
        self.assertEqual(decoder.frame.calc_bitrate(
            consts.Standards.MPEG_2, decoder.frame.LAYER_2, 0b1110),
            160,
        )


if __name__ == '__main__':
    unittest.main()
