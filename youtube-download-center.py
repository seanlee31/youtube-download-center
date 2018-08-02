from pytube import Playlist, YouTube, exceptions
import sys
import threading
from collections import deque
import pprint
import time
import os

from tkinter import filedialog
from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import re

########################################
### Producer/Consumer Design Pattern ###
########################################

V_MP4_1080P = 137
A_MP4_128KB = 140
A_OPUS_160KB = 251

VA_MP4_720P = 22

class ytDownloaderThread(threading.Thread):
    def __init__(self, yt_queue, init_quantity, show_progress=False):
        super().__init__()
        self._yt_queue = yt_queue
        self._init_quantity = init_quantity
        self._show_progress = show_progress
        self._count = 1

    def progress_function(self, stream, chunk, file_handle, bytes_remaining):
        total_size = stream.filesize
        percent = 100.
        while percent <= 100.:
            if percent % 10. == 0.:
                print('[Downloading - {} - {}/{}] {:.2f}%\n'.format(self.name, self._count, self._init_quantity, percent))
            percent = self.percent(bytes_remaining, total_size)

    def percent(self, bytes_remaining, total_size):
        percent = (float(bytes_remaining) / float(total_size)) * 100.
        return percent

    def check_path(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            print("[Main - {}] The Missing Folder/Directory, {}, Has Been Created!\n".format(self.name, path))

class videoDownloaderThread(ytDownloaderThread):
    ## Consumer
    def __init__(self, yt_video_queue, init_num_videos, show_progress=False):
        super().__init__(yt_video_queue, init_num_videos, show_progress)

    def run(self):
        while len(self._yt_queue) > 0:
            yt_video = self._yt_queue.popleft()
            yt_url = yt_video[0]
            pl_path = yt_video[1]
            self.check_path(pl_path)
            try:
                if self._show_progress:
                    yt = YouTube(yt_url, on_progress_callback=super.progress_function)
                else:
                    yt = YouTube(yt_url)
                # video = yt.streams.filter(subtype='mp4').all()
                # video = yt.streams.get_by_itag(V_MP4_1080P)
                # audio = yt.streams.get_by_itag(A_MP4_128KB)
                video = yt.streams.get_by_itag(VA_MP4_720P)
                start_time = time.time()
                print("[Main - {} - {}/{}] YouTube Video {} w/ {} Download Has Started ...\n".format(self.name, self._count, self._init_quantity, yt_url, video.resolution))
                video.download(pl_path)
                end_time = time.time()
                diff_time = end_time - start_time
                print("[Main - {} - {}/{}] YouTube Video {} w/ {} Was Successfully Downloaded -- Took {:.2f}s!\n".format(self.name, self._count, self._init_quantity, yt_url, video.resolution, diff_time))
                self._count += 1
            except exceptions.RegexMatchError:
                print("[Error (RegexMatchError) - {} - {}/{}] YouTube Video {} Had a Problem Processing And Was Skipped!\n".format(self.name, self._count, self._init_quantity, yt_url))
                self._count += 1
                continue
            except OSError as err:
                sys.stderr.write(err)
                print("[Error (OSError) - {} - {}/{}] YouTube Video {} Had a Problem Processing And Was Skipped!\n".format(self.name, self._count, self._init_quantity, yt_url))
                self._count += 1
                continue

        print("[Main - {}] The Thread Has Finished Downloading All YouTube Videos {}!\nExiting Thread ... \n".format(self.name, yt_url))

class audioDownloaderThread(ytDownloaderThread):
    ## Consumer
    def __init__(self, yt_audio_queue, init_num_audios, show_progress=False):
        super().__init__(yt_audio_queue, init_num_audios, show_progress)

    def run(self):
        while len(self._yt_queue) > 0:
            yt_audio = self._yt_queue.popleft()
            yt_url = yt_audio[0]
            pl_path = yt_audio[1]
            self.check_path(pl_path)
            try:
                if self._show_progress:
                    yt = YouTube(yt_url, on_progress_callback=super.progress_function)
                else:
                    yt = YouTube(yt_url)
                # audio = yt.streams.get_by_itag(A_MP4_128KB)
                audio = yt.streams.get_by_itag(A_OPUS_160KB)
 
                start_time = time.time()
                print("[Main - {} - {}/{}] YouTube Audio {} w/ {} Download Has Started ...\n".format(self.name, self._count, self._init_quantity, yt_url, audio.abr))
                audio.download(pl_path)
                end_time = time.time()
                diff_time = end_time - start_time
                print("[Main - {} - {}/{}] YouTube Audio {} w/ {} Was Successfully Downloaded -- Took {:.2f}s!\n".format(self.name, self._count, self._init_quantity, yt_url, audio.abr, diff_time))
                self._count += 1
            except exceptions.RegexMatchError:
                print("[Error - {} - {}/{}] YouTube Audio {} Had a Problem Processing And Was Skipped!\n".format(self.name, self._count, self._init_quantity, yt_url))
                self._count += 1
                continue

        print("[Main - {}] The Thread Has Finished Downloading All YouTube Videos {}!\nExiting Thread ... \n".format(self.name, yt_url))

            
def download_playlist_1080p(pl_url, pl_path, threads=5):
    # print("[Main] Started Downloading YouTube Playlist {}! \n".format(url))
    pl = Playlist(pl_url)
    pl.populate_video_urls()
    videos_len = len(pl.video_urls)
    print(videos_len)

    for yt_url in pl.video_urls:
        try:
            yt = YouTube(yt_url)
            video = yt.streams.filter(adaptive=True, subtype='mp4').all()[0]
            print("[Downloading] YouTube Video {} w/ {} ...\n".format(yt_url, video.resolution))
            video.download(pl_path)
            print("[Main] YouTube Video {} w/ {} Was Successfully Downloaded!\n".format(yt_url, video.resolution))
        except exceptions.RegexMatchError:
            continue

def get_yt_urls_and_paths(pl_urls_and_paths):
    yt_urls = list()
    pl_paths = list()

    for pl in pl_urls_and_paths:
        pl_url = pl[0]
        pl_path = pl[1]
        
        pl = Playlist(pl_url)
        pl.populate_video_urls()

        for yt_url in pl.video_urls:
            yt_urls.append(yt_url)
            pl_paths.append(pl_path)

    return yt_urls, pl_paths

def list_chunkify(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def download_from_mapping_multithreaded(yt_urls, pl_paths, mode, num_threads=5, show_progress=False):
    mappings = list(zip(yt_urls, pl_paths))
    num_mappings = len(mappings)
    num_videos_per_thread = num_mappings // num_threads
    num_videos_remainder = num_mappings % num_threads

    mappings_by_threads = list(list_chunkify(mappings, num_videos_per_thread))

    if num_videos_remainder > 0:
        remainder_idx = num_threads
        mappings_by_threads[remainder_idx-1].extend(mappings_by_threads[remainder_idx])

    ## Remove the remainder mappings that were added to the last complete mappings set.
    mappings_by_threads = mappings_by_threads[:-1]

    # yt_downloaders = list()
    ## Start videoDownloaderThread workers.
    for mappings in mappings_by_threads:
        mappings = deque(mappings)
        num_mappings = len(mappings)

        if mode == "AUDIO":
            yt_downloader = audioDownloaderThread(yt_audio_queue=mappings, init_num_audios=num_mappings, show_progress=show_progress)
        if mode == "VIDEO":
            yt_downloader = videoDownloaderThread(yt_video_queue=mappings, init_num_videos=num_mappings, show_progress=show_progress)

        yt_downloader.daemon = True
        yt_downloader.start()
        # yt_downloaders.append(yt_downloader)
        time.sleep(1)

    # for yt_downloader in yt_downloaders:
    #     yt_downloader.join()

def main():
    ## Disable buttons
    download_button['state'] = 'disabled'
    exit_button['state'] = 'disabled'

    p_url_and_path = r"(.*):(https?:.*)"
    pl_entries = text_pl_urls.get("1.0", 'end-1c')  ## 'end-1c' to remove 1 character, \n.
    pl_entries = pl_entries.splitlines()

    mode = cbox_mode.get()
    num_threads = int(cbox_thread.get())

    path_lst = list()
    pl_lst = list()

    for line in pl_entries:
        entry = re.findall(p_url_and_path, line)[0]
        path = entry[0]
        pl = entry[1]

        path_lst.append(path)
        pl_lst.append(pl)

    pl_mappings = list(zip(pl_lst, path_lst))
    yt_urls, pl_paths = get_yt_urls_and_paths(pl_mappings)

    if mode == "AUDIO":
        download_from_mapping_multithreaded(yt_urls=yt_urls, pl_paths=pl_paths, mode=mode, num_threads=num_threads, show_progress=False)
    if mode == "VIDEO":
        download_from_mapping_multithreaded(yt_urls=yt_urls, pl_paths=pl_paths, mode=mode, num_threads=num_threads, show_progress=False)

    ## Enable buttons
    download_button['state'] = 'normal'
    exit_button['state'] = 'normal'

if __name__ == '__main__':  ## python youtube-downloader.py [mode] [num_threads] ([storage_directory] [youtube playlists]) ...
    root = Tk()
    root.title("YouTube Download Center v1.1 - By Sean L.")
    label_pl_urls = Label(root, text='Input YouTube PlayLists Urls: ')
    label_pl_urls.grid(row=0, column=0, columnspan=2)

    text_pl_urls = ScrolledText(root)
    text_pl_urls.grid(row=1, column=0, columnspan=2)

    label_mode = Label(root, text='Input Mode (AUDIO/VIDEO): ')
    label_mode.grid(row=2, column=0)
    mode_options = ("AUDIO", "VIDEO")
    cbox_mode = ttk.Combobox(root, values=mode_options, width=40)
    cbox_mode.current(0)
    cbox_mode.grid(row=2, column=1)

    label_num_threads = Label(root, text='Input # of Thread Using: ')
    label_num_threads.grid(row=3, column=0)
    thread_options = tuple([str(i) for i in range(1, 10+1)])
    cbox_thread = ttk.Combobox(root, values=thread_options, width=40)
    cbox_thread.current(4)
    cbox_thread.grid(row=3, column=1)

    label_warning = Label(root, text='You will not be able to cancel downloading with the UI or Ctrl+C.')
    label_warning_2 = Label(root, text='Please close it manually or wait until process is finished.')
    label_warning.grid(row=5, column=0, columnspan=2)
    label_warning_2.grid(row=6, column=0, columnspan=2)

    download_button = Button(root, text="Start Download", command=main, width=50)
    download_button.grid(row=7, column=0, columnspan=2)

    ## Define Exit Button
    exit_button = Button(root, text="Exit", width=50, command=root.destroy)
    exit_button.grid(row=8, column=0, columnspan=2)

    
    root.mainloop()