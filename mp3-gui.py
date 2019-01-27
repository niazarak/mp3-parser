#!/usr/bin/env python3

import tkinter
from tkinter import messagebox, filedialog, ttk
import traceback
import functools
import threading
import pyaudio
import pydub
import audioop
from enum import Enum
from pydub import utils
from queue import Queue
from PIL import Image, ImageTk
from io import BytesIO
from zlib import decompress
from base64 import b85decode

from decoder import decoder


def handle_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwds):
        try:
            return func(*args, **kwds)
        except Exception as e:
            tkinter.messagebox.showerror('Error',
                                         f'{e}\n\n{traceback.format_exc()}')
            print(f'{e}\n\n{traceback.format_exc()}')

    return wrapper


class PlayerState:
    def __init__(self, player_queue):
        self.player_queue: Queue = player_queue
        self.p = pyaudio.PyAudio()

        self.is_playing = False
        self.segment = None
        self.chunks = []
        self.stream = None
        self.i = 0

        self._volume: float = 1.0

    def set(self, name):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        self.segment = pydub.AudioSegment.from_mp3(name)
        self.stream = self.p.open(
            format=self.p.get_format_from_width(self.segment.sample_width),
            channels=self.segment.channels,
            rate=self.segment.frame_rate,
            output=True
        )
        self.chunks = utils.make_chunks(self.segment, 50)

    def play(self):
        if self.segment and self.stream:
            self.is_playing = True

    def pause(self):
        self.is_playing = False

    def update(self):
        if self.is_playing:
            if self.i > len(self.chunks) - 1:
                self.is_playing = False
                self.i = 0
                self.player_queue.put(Mp3ThreadEvent.Finished)
            else:
                data = self.chunks[self.i]
                if self._volume < 1:
                    data = data._spawn(data=audioop.mul(
                        data._data, data.sample_width, self._volume
                    ))
                self.stream.write(data._data)
                self.i += 1

    @property
    def volume(self) -> float:
        """Returns value from 0.0 to 1.0"""
        return self._volume

    @volume.setter
    def volume(self, val):
        self._volume = val


class Mp3ThreadCommand(Enum):
    Play = 0
    Pause = 1
    Set = 2
    Volume = 3


class Mp3ThreadEvent(Enum):
    Finished = 0


class Mp3Thread(threading.Thread):
    def __init__(self, gui_queue, player_queue):
        super(Mp3Thread, self).__init__()
        self.gui_queue = gui_queue
        self.player = PlayerState(player_queue)

    def run(self):
        while True:
            if self.gui_queue.qsize():
                command, args = self.gui_queue.get_nowait()
                print('Mp3Thread loop command:', command, args)
                if command == Mp3ThreadCommand.Set:
                    self.player.set(args)
                elif command == Mp3ThreadCommand.Play:
                    self.player.play()
                elif command == Mp3ThreadCommand.Pause:
                    self.player.pause()
                elif command == Mp3ThreadCommand.Volume:
                    self.player.volume = args
                else:
                    break
            self.player.update()


class Mp3FileGuiState:
    def __init__(self):
        self.filename = None
        self.hist = None
        self.album = None
        self.data = None
        self.is_playing = False


class MetaInfoFrame(tkinter.Frame):
    def __init__(self, master):
        tkinter.Frame.__init__(self, master)
        self.text = tkinter.Text(self, width=40, height=10)
        self.label = tkinter.Label(self, text=type(self).__name__)

    def init(self):
        self.label.grid(in_=self, column=0, row=0)
        self.text.grid(in_=self, column=0, row=1)
        self['borderwidth'] = 2
        self.set_text("No file selected")

    def set_text(self, text):
        self.text.configure(state='normal')
        self.text.delete(1.0, 'end')
        self.text.insert('end', text)
        self.text.configure(state='disabled')


class ID3v1TagFrame(MetaInfoFrame):
    def set_tag(self, idv1_tag):
        if idv1_tag:
            s = (f"Title: {idv1_tag.title}\n"
                 f"Artist: {idv1_tag.artist}\n"
                 f"Album: {idv1_tag.album}\n"
                 f"Year: {idv1_tag.year}\n"
                 f"Comment: {idv1_tag.comment}\n"
                 f"Genre: {idv1_tag.genre}")
            self.set_text(s)
        else:
            self.set_text("File does not have ID3v1 tag")


class ID3v2TagFrame(MetaInfoFrame):
    def set_tag(self, idv2_tag):
        print(idv2_tag)
        if idv2_tag:
            s = f"Version: {idv2_tag.version}"
            if not idv2_tag.is_version_supported():
                s += " (not supported)"
            else:
                if idv2_tag.version == 0x0300:
                    s += " (ID3v2.3)\n"
                else:
                    s += " (ID3v2.4)\n"

                s += (
                    f'Title: {idv2_tag.title}\n'
                    f'Compositor: {idv2_tag.compositor}\n'
                    f'Lead performer: {idv2_tag.performer_1}\n'
                    f'Album: {idv2_tag.album}\n'
                    f'Year: {idv2_tag.year}\n'
                    f'Track: {idv2_tag.track}\n'
                    f'Encoder: {idv2_tag.encoder}\n'
                    f'Copyright: {idv2_tag.copyright}\n'
                )
            self.set_text(s)
        else:
            self.set_text("File does not have ID3v2 tag")


GRID = 'c%17D@N?(olHy`uVBq!ia0y~yV4MKLOw2%$zZdVt11X*WpAgrZH*X#}a^yc4d' \
       '`MaL1Srl}666=m;PC858jy3-)5S5QV$R#M3wap~c~}lk_>%tV@Agk$7U&+$Ik' \
       'Uz#^IYfd_&Y%j4hjMsEKH4XYVHL8r*9H5go9PyKg-cX7oFgDVtLUw0}Nr!N#(' \
       '`cM9@S9Jk*~ATUJY;3!e}<x!W?D3r&<`iSVbDb8LCgg;ONz)bD<hFnADW0rVt' \
       ';r>mdKI;Vst0JvvgF#'

GRID = Image.open(BytesIO(decompress(b85decode(GRID)))).convert('RGBA')


class Mp3Gui:
    HIST_SIZE = 250
    ALBUM_COVER_SIZE = 200

    def __init__(self, gui_queue, player_queue):
        self.root = tkinter.Tk()

        self.gui_queue: Queue = gui_queue
        self.player_queue: Queue = player_queue
        self.state = Mp3FileGuiState()

        self.menu = tkinter.Menu(self.root)
        self.sub_menu = tkinter.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Menu", menu=self.sub_menu)

        self.main_frame = tkinter.Frame(self.root)
        self.play_button = tkinter.Button(self.main_frame,
                                          text='Play',
                                          command=self.on_play_button_pressed)
        self.volume_slider = tkinter.Scale(self.main_frame,
                                           orient="horizontal",
                                           resolution=10,
                                           command=self.on_volume_changed)

        self.hist = tkinter.Canvas(self.main_frame,
                                   width=Mp3Gui.HIST_SIZE,
                                   height=Mp3Gui.HIST_SIZE)
        self.hist_image = None

        self.frames_list = tkinter.Listbox(self.root, width=10)
        self.frames_list.bind("<<ListboxSelect>>", self.on_frame_selected)
        self.frame_text = tkinter.Text(self.root, width=40, height=15)

        self.id3v1_frame = ID3v1TagFrame(self.root)
        self.id3v2_frame = ID3v2TagFrame(self.root)
        self.album_cover = tkinter.Canvas(self.root,
                                          width=Mp3Gui.ALBUM_COVER_SIZE,
                                          height=Mp3Gui.ALBUM_COVER_SIZE)
        self.album_cover_image = None

    def init(self):
        self.root.config(menu=self.menu)
        self.root.wm_resizable(width=False, height=False)
        # self.root.wm_geometry('320x420')
        self.root.wm_title("Mp3 Player")
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.destroy())
        self.sub_menu.add_command(label='Open mp3 file',
                                  command=self.on_open_file)

        self.main_frame['borderwidth'] = 2
        self.main_frame['relief'] = 'sunken'
        self.main_frame.grid(row=0, column=0, rowspan=2, sticky="N")
        self.play_button.grid(column=0, row=0)
        self.volume_slider.set(100)
        self.volume_slider.grid(column=1, row=0)
        self.hist.grid(column=0, row=1, columnspan=2)

        self.frames_list.grid(column=1, row=0, rowspan=2)
        self.frame_text.grid(column=2, row=0, rowspan=2)
        self.frame_text.configure(state='disabled')

        self.id3v1_frame.grid(row=2, column=0)
        self.id3v1_frame.init()
        self.id3v2_frame.grid(row=2, column=1)
        self.id3v2_frame.init()
        self.album_cover.grid(row=2, column=2)

        self.setup_watchdog()

    @handle_error
    def on_open_file(self):
        name = tkinter.filedialog.askopenfilename(
            filetypes=[('MP3 files', '*.mp3')])
        if name:
            self.process_file(name)

    def process_file(self, name):
        self.clear_frames_list()

        with open(name, 'rb') as file:
            data = decoder.decode(file)
            self.state.data = data
            self.fill_frames_list(len(self.state.data.frames))

        self.id3v1_frame.set_tag(self.state.data.meta_id3v1)
        self.id3v2_frame.set_tag(self.state.data.meta_id3v2)
        if self.state.data.meta_id3v2 \
                and self.state.data.meta_id3v2.album_image_bytes:
            self.set_album_cover(self.state.data.meta_id3v2.album_image_bytes)
        else:
            self.set_default_album_cover()
        self.set_audio(name)

        segment = pydub.AudioSegment.from_mp3(name).set_channels(1)
        self.state.hist = segment.get_array_of_samples()
        self.fill_hist(segment.get_array_of_samples(),
                       int(segment.max_possible_amplitude))

    def pause_audio(self):
        self.state.is_playing = False
        self.gui_queue.put((Mp3ThreadCommand.Pause, None))

    def play_audio(self):
        self.state.is_playing = True
        self.gui_queue.put((Mp3ThreadCommand.Play, None))

    def set_audio(self, name):
        self.state.filename = name
        self.gui_queue.put((Mp3ThreadCommand.Set, name))

    def destroy(self):
        self.gui_queue.put((None, None))
        self.root.destroy()

    def setup_watchdog(self):
        def result_watchdog():
            if player_queue.qsize():
                command = player_queue.get_nowait()
                if command == Mp3ThreadEvent.Finished:
                    self.on_playback_finished()

            self.root.after(50, func=result_watchdog)

        self.root.after(50, func=result_watchdog)

    @handle_error
    def on_play_button_pressed(self):
        if self.state.filename:
            if self.state.is_playing:
                self.pause_audio()
            else:
                self.play_audio()

    def on_volume_changed(self, volume):
        self.gui_queue.put((Mp3ThreadCommand.Volume, int(volume) / 100))

    def on_playback_finished(self):
        self.state.is_playing = False

    def run(self):
        self.root.mainloop()

    def fill_hist(self, samples, sample_max_val):
        data = ("{black}")
        channel_height = Mp3Gui.HIST_SIZE
        step = len(samples) // Mp3Gui.HIST_SIZE
        self.hist_image = tkinter.PhotoImage(width=Mp3Gui.HIST_SIZE,
                                             height=Mp3Gui.HIST_SIZE)
        for x in range(0, Mp3Gui.HIST_SIZE):
            sample = samples[min(x * step, len(samples))]
            scaled_sample = int(channel_height // 2 * sample / sample_max_val)

            if scaled_sample > 0:
                y0 = channel_height // 2 - scaled_sample
                y1 = channel_height // 2
                self.hist_image.put(data, to=(x, y0, x + 1, y1))
            elif scaled_sample < 0:
                y0 = channel_height // 2
                y1 = channel_height // 2 - scaled_sample
                self.hist_image.put(data, to=(x, y0, x + 1, y1))

        self.hist.create_image((Mp3Gui.HIST_SIZE // 2, Mp3Gui.HIST_SIZE // 2),
                               image=self.hist_image)

    def set_default_album_cover(self):
        bg = GRID.resize((Mp3Gui.ALBUM_COVER_SIZE, Mp3Gui.ALBUM_COVER_SIZE),
                         Image.ANTIALIAS)
        self.album_cover_image = ImageTk.PhotoImage(image=bg)
        self.album_cover.create_image(
            (Mp3Gui.ALBUM_COVER_SIZE // 2, Mp3Gui.ALBUM_COVER_SIZE // 2),
            image=self.album_cover_image)

    def set_album_cover(self, data: bytes):
        resized_image = Image.open(BytesIO(data)).resize(
            (Mp3Gui.ALBUM_COVER_SIZE, Mp3Gui.ALBUM_COVER_SIZE),
            Image.ANTIALIAS
        )
        self.album_cover_image = ImageTk.PhotoImage(resized_image, size=(
            Mp3Gui.ALBUM_COVER_SIZE, Mp3Gui.ALBUM_COVER_SIZE
        ))
        self.album_cover.create_image(
            (Mp3Gui.ALBUM_COVER_SIZE // 2, Mp3Gui.ALBUM_COVER_SIZE // 2),
            image=self.album_cover_image
        )

    def clear_frames_list(self):
        self.frames_list.delete(0, 'end')
        self.frame_text.configure(state='normal')
        self.frame_text.delete(1.0, 'end')
        self.frame_text.configure(state='disabled')

    def fill_frames_list(self, frames_count):
        self.frames_list.insert('end', *range(frames_count))

    def on_frame_selected(self, event):
        selection = event.widget.curselection()
        print("Frame selected:", selection)
        if not selection:
            return
        frame_header = self.state.data.frames[selection[0]].header

        header_description = (
            f"Standart: {frame_header.standart.name}\n"
            f"Layer: {frame_header.layer}\n"
            f"Bitrate: {frame_header.bitrate}\n"
            f"Samplerate: {frame_header.samplerate}\n"
            f"Channels: {frame_header.channel_mode.name}\n"
            f"Is original: {bool(frame_header.is_original)}\n"
            f"Copyrighted: {bool(frame_header.copyright)}\n"
            f"CRC protection: {frame_header.protection}\n"
            f"Samples count: {frame_header.frame_size}\n"
            f"Frame length: {frame_header.frame_length} bytes\n")

        self.frame_text.configure(state='normal')
        self.frame_text.delete(1.0, 'end')
        self.frame_text.insert('end', header_description)
        self.frame_text.configure(state='disabled')


if __name__ == '__main__':
    gui_queue = Queue()
    player_queue = Queue()

    bg_thread = Mp3Thread(gui_queue, player_queue)
    bg_thread.start()

    gui = Mp3Gui(gui_queue, player_queue)
    gui.init()
    gui.run()
