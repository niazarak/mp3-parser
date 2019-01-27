from . import meta, frame


def decode(file):
    decoded_file = File()
    frame_decoder = frame.FrameDecoder()

    i = 0
    while True:
        header_bytes = file.read(4)

        if not header_bytes:
            break

        if header_bytes.startswith(meta.ID3V2_MAGIC):
            metadata = meta.parse_id3v2(header_bytes, file)
            decoded_file.meta_id3v2 = metadata
        elif header_bytes.startswith(frame.SYNC_WORD):
            framedata = frame_decoder.parse_frame(header_bytes, file)
            decoded_file.append_frame(framedata)
            if i == 2:
                break
            else:
                pass
                # i += 1
        elif header_bytes.startswith(meta.ID3V1_MAGIC):
            metadata = meta.parse_id3v1(header_bytes, file)
            decoded_file.meta_id3v1 = metadata
        else:
            raise BaseException('Unknown header bytes!', header_bytes)

    return decoded_file


class File:
    def __init__(self):
        self.frames: list = []
        self.meta_id3v1 = None
        self.meta_id3v2 = None

    def append_frame(self, framedata: frame.Frame):
        self.frames.append(framedata)
