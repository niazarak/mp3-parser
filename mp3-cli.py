#!/usr/bin/env python3

import argparse

from decoder import decoder

parser = argparse.ArgumentParser()

parser.add_argument('file', type=argparse.FileType('rb'))

args = parser.parse_args()

data = decoder.decode(args.file)

for frame in data.frames[:10]:
    frame.header.print()
    print()

if len(data.frames) > 10:
    print("... (Output truncated to first 10 frames)")
    print()

if data.meta_id3v1:
    data.meta_id3v1.print()
else:
    print("No ID3v1 tag")

print()

if data.meta_id3v2:
    data.meta_id3v2.print()
else:
    print("No ID3v1 tag")

print()

print("Total", len(data.frames), "frames")
