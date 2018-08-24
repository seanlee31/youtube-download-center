########################################
###            LIBRARIES             ###
########################################
from pytube import Playlist, YouTube, exceptions
import sys
import threading
from collections import deque
import pprint
import time
import os, subprocess

from tkinter import filedialog
from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import re
########################################
###              CODES               ###
########################################

### Video ###
V_VP9_1080P = 248

### Audio ###
A_MP4_128KB = 140
A_OPUS_160KB = 251

### Video + Audio ###
VA_MP4_720P = 22

########################################
###  SIMPLE FACTORY DESIGN PATTERN   ###
########################################
class genericDownloaderThread(threading.Thread):
    def __init__(self, va_queue, init_quantity, show_progress=False):
        super().__init__()
        self._va_queue = va_queue
        self._init_quantity = init_quantity
        self._show_progress = show_progress
        self._count = 1

    def progress_function(self, stream, chunk, file_handle, bytes_remaining):
        total_size = stream.filesize
        percent = 100.
        while percent <= 100.:
            if percent % 10. == 0.:
                print('[DOWNLOADING - {} - {}/{}] {:.2f}%\n'.format(self.name, self._count, self._init_quantity, percent))
            percent = self.percent(bytes_remaining, total_size)

    def percent(self, bytes_remaining, total_size):
        percent = (float(bytes_remaining) / float(total_size)) * 100.
        return percent

    def check_path(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            print("[MAIN - {}] Missing Folder/Directory, {}, Has Been Created!\n".format(self.name, path))
    
class videoDownloaderThread(genericDownloaderThread):
    ## Concrete Product
    def __init__(self, yt_video_queue, init_num_videos, resolution, show_progress=False):
        super().__init__(yt_video_queue, init_num_videos, show_progress)
        self._resolution = resolution
    
    def run(self):
        if self._resolution == '1080P':
            self.download_1080P()
        elif self._resolution == '720P':
            self.download_720P()

    def download_720P(self):
        while len(self._va_queue) > 0:
            yt_video = self._va_queue.popleft()
            yt_url = yt_video[0]
            pl_path = yt_video[1]
            self.check_path(pl_path)
            try:
                if self._show_progress:
                    yt = YouTube(yt_url, on_progress_callback=self.progress_function)
                else:
                    yt = YouTube(yt_url)

                video = yt.streams.get_by_itag(VA_MP4_720P)
                
                start_time = time.time()
                print("[MAIN - {} - {}/{}] YouTube Video {} w/ {} Download Has Started ...".format(self.name, self._count, self._init_quantity, yt.title, video.resolution))
                print("[MAIN - {} - {}/{}] URL: {} \n".format(self.name, self._count, self._init_quantity, yt_url))
                video.download(pl_path)
                end_time = time.time()
                diff_time = end_time - start_time
                print("[MAIN - {} - {}/{}] YouTube Video {} w/ {} Was Successfully Downloaded -- Took {:.2f}s!".format(self.name, self._count, self._init_quantity, yt.title, video.resolution, diff_time))
                print("[MAIN - {} - {}/{}] URL: {} \n".format(self.name, self._count, self._init_quantity, yt_url))
                self._count += 1
            except exceptions.RegexMatchError:
                print("[Error (RegexMatchError) - {} - {}/{}] YouTube Video {} Had a Problem Processing And Was Skipped!\n".format(self.name, self._count, self._init_quantity, yt_url))
                self._count += 1
                continue
            except OSError:
                print("[Error (OSError) - {} - {}/{}] YouTube Video {} Had a Problem Processing And Was Skipped!\n".format(self.name, self._count, self._init_quantity, yt_url))
                self._count += 1
                continue

        print("[MAIN - {}] The Thread Has Finished Downloading All YouTube Videos Assigned!\nExiting Thread ... \n".format(self.name))

    def download_1080P(self):
        while len(self._va_queue) > 0:
            yt_video = self._va_queue.popleft()
            yt_url = yt_video[0]
            pl_path = yt_video[1]
            self.check_path(pl_path)
            try:
                if self._show_progress:
                    yt = YouTube(yt_url, on_progress_callback=self.progress_function)
                else:
                    yt = YouTube(yt_url)
                
                start_time = time.time()
                print("[MAIN - {} - {}/{}] YouTube Video {} w/ {} Download Has Started ...".format(self.name, self._count, self._init_quantity, yt.title, self._resolution))
                print("[MAIN - {} - {}/{}] URL: {} \n".format(self.name, self._count, self._init_quantity, yt_url))
                self.download_1080p_helper(yt=yt, video_path=pl_path)
                end_time = time.time()
                diff_time = end_time - start_time
                print("[MAIN - {} - {}/{}] YouTube Video {} w/ {} Was Successfully Downloaded -- Took {:.2f}s!".format(self.name, self._count, self._init_quantity, yt.title, self._resolution, diff_time))
                print("[MAIN - {} - {}/{}] URL: {} \n".format(self.name, self._count, self._init_quantity, yt_url))
                self._count += 1
            except exceptions.RegexMatchError:
                print("[ERROR (RegexMatchError) - {} - {}/{}] YouTube Video {} Had a Problem Processing And Was Skipped!\n".format(self.name, self._count, self._init_quantity, yt_url))
                self._count += 1
                continue
            except OSError:
                print("[ERROR (OSError) - {} - {}/{}] YouTube Video {} Had a Problem Processing And Was Skipped!\n".format(self.name, self._count, self._init_quantity, yt_url))
                self._count += 1
                continue

        print("[MAIN - {}] The Thread Has Finished Downloading All YouTube Videos Assigned!\nExiting Thread ... \n".format(self.name))
        
    def download_1080p_helper(self, yt, video_path):
        print("[HELPER - {} - {}/{}] Start Downloading YouTube 1080P Video: {} ! \n".format(self.name, self._count, self._init_quantity, yt.watch_url))
        itags = [V_VP9_1080P, A_OPUS_160KB]
        file_names = list()

        for itag in itags:      
            video = yt.streams.get_by_itag(itag)
            codec_type = (video.parse_codecs()[0] if video.parse_codecs()[0] is not None else video.parse_codecs()[1])
            title = video.default_filename[:-5]
            file_type = video.default_filename[-4:].upper()
            filename = title + codec_type
            file_names.append(filename)
            print("[HELPER - {} - {}/{}] Start Downloading: {} @ {}. \n".format(self.name, self._count, self._init_quantity, filename, video_path)) 
            video.download(output_path=video_path, filename=filename)
            print("[HELPER - {} - {}/{}] Finished Downloading: {} @ {}. \n".format(self.name, self._count, self._init_quantity, filename, video_path))
            
        print("[HELPER - {} - {}/{}] Start Merging Audio & Video using ffmpeg. \n".format(self.name, self._count, self._init_quantity))
        ## Check Operating System
        if sys.platform == 'win32':
            ffmpeg_path = os.path.join(sys.path[0], "ffmpeg", "win", "bin")
        elif sys.platform == 'darwin':
            ffmpeg_path = os.path.join(sys.path[0], "ffmpeg", "mac", "bin")
        elif sys.platform.startswith('linux'):
            ffmpeg_path = os.path.join(sys.path[0], "ffmpeg", "linux", "bin")
        
        os.chdir(video_path)
        input_files = ['{}.{}'.format(file_names[0], file_type), '{}.{}'.format(file_names[1], file_type)]
        subprocess.call([os.path.join(ffmpeg_path, "ffmpeg"), 
        '-i', input_files[0], 
        '-i', input_files[1], 
        '-c:v', 'copy',
        '-c:a', 'aac', 
        '-ac', '2',
        '-ar', '48000', 
        '-ab', '160k',
        '-f', 'matroska',
        '-y',  ## overwrite if the output video has already existed.
        '{}.mkv'.format(title)])

        for f in input_files:
            os.remove(f)
            print("Removed {}. \n".format(f))

        print("[HELPER - {} - {}/{}] Finished Downloading and Merging Audio & Video for 1080p YouTube Video: {}. \n".format(self.name, self._count, self._init_quantity, title))

class audioDownloaderThread(genericDownloaderThread):
    ## Concrete Product
    def __init__(self, yt_audio_queue, init_num_audios, show_progress=False):
        super().__init__(yt_audio_queue, init_num_audios, show_progress)

    def run(self):
        while len(self._va_queue) > 0:
            yt_audio = self._va_queue.popleft()
            yt_url = yt_audio[0]
            pl_path = yt_audio[1]
            self.check_path(pl_path)
            try:
                if self._show_progress:
                    yt = YouTube(yt_url, on_progress_callback=self.progress_function)
                else:
                    yt = YouTube(yt_url)

                audio = yt.streams.get_by_itag(A_OPUS_160KB)
 
                start_time = time.time()
                print("[MAIN - {} - {}/{}] YouTube Audio {} w/ {} Download Has Started ...".format(self.name, self._count, self._init_quantity, yt.title, audio.abr))
                print("[MAIN - {} - {}/{}] URL: {} \n".format(self.name, self._count, self._init_quantity, yt_url))
                audio.download(pl_path)
                end_time = time.time()
                diff_time = end_time - start_time
                print("[MAIN - {} - {}/{}] YouTube Audio {} w/ {} Was Successfully Downloaded -- Took {:.2f}s!".format(self.name, self._count, self._init_quantity, yt.title, audio.abr, diff_time))
                print("[MAIN - {} - {}/{}] URL: {} \n".format(self.name, self._count, self._init_quantity, yt_url))
                self._count += 1
            except exceptions.RegexMatchError:
                print("[ERROR - {} - {}/{}] YouTube Audio {} Had a Problem Processing And Was Skipped!\n".format(self.name, self._count, self._init_quantity, yt_url))
                self._count += 1
                continue

        print("[MAIN - {}] The Thread Has Finished Downloading All YouTube Videos Assigned!\nExiting Thread ... \n".format(self.name))

class YTDC_GUI():
    def __init__(self, current_version):
        self._version = current_version
        self.root = Tk()
        self.label_pl_urls = Label(self.root, text='Input YouTube PlayLists URLs: ', font='Helvetica 10 bold')
        self.text_pl_urls = ScrolledText(self.root)
        self.label_mode = Label(self.root, text='Select Mode (AUDIO/VIDEO): ', font='Helvetica 10 bold')

        mode_options = ("AUDIO", "VIDEO")
        self.cbox_mode = ttk.Combobox(self.root, values=mode_options, width=40, font='Helvetica 8 bold')
        self.label_num_threads = Label(self.root, text='Select # of Thread Using: ', font='Helvetica 10 bold')

        thread_options = tuple([str(i) for i in range(1, 10+1)])
        self.cbox_thread = ttk.Combobox(self.root, values=thread_options, width=40, font='Helvetica 8 bold')

        self.label_resolution = Label(self.root, text='Select Resolution (If VIDEO Mode): ', font='Helvetica 10 bold')

        resolution_options = ('1080P', '720P')
        self.cbox_resolution = ttk.Combobox(self.root, values=resolution_options, width=40, font='Helvetica 8 bold')

        self.label_warning = Label(self.root, text='You Will Be Able To Cancel The Downloading Process By Clicking "EXIT" Button.', font='Helvetica 10 bold', fg="red")

        ## Define DOWNLOAD Button
        self.download_button = Button(self.root, text="START DOWNLOAD", command=self.main, width=50, font='Helvetica 8 bold', cursor="hand2")
        
        ## Define EXIT Button
        self.exit_button = Button(self.root, text="EXIT", width=50, command=self.root.destroy, font='Helvetica 8 bold', cursor="hand2")

        ## Author Disclaimer
        self.label_author = Label(self.root, text='Developed By Sean Lee © 2018', font='Helvetica 8 bold')

        ## Github Links
        self.label_github = Label(self.root, text='[Github] https://github.com/seanlee31/youtube-download-center', font='Helvetica 8 bold', fg="blue", cursor="hand2")
        self.label_bug_report = Label(self.root, text='[BUG Report] https://github.com/seanlee31/youtube-download-center/issues', font='Helvetica 8 bold', fg="blue", cursor="hand2")

    def run(self):
        self.root.title("YouTube Download Center v{}".format(self._version))
        self.label_pl_urls.grid(row=0, column=0, columnspan=2, pady=(10, 10))

        self.text_pl_urls.grid(row=1, column=0, columnspan=2)

        self.label_mode.grid(row=2, column=0)
        
        self.cbox_mode.current(1)
        self.cbox_mode.grid(row=2, column=1)

        self.label_num_threads.grid(row=3, column=0)

        self.cbox_thread.current(4)
        self.cbox_thread.grid(row=3, column=1)

        self.label_resolution.grid(row=4, column=0)

        self.cbox_resolution.current(0)
        self.cbox_resolution.grid(row=4, column=1)

        self.label_warning.grid(row=5, column=0, columnspan=2, pady=(10, 10))

        self.download_button.grid(row=6, column=0, columnspan=2)

        self.exit_button.grid(row=7, column=0, columnspan=2)

        self.label_author.grid(row=8, column=0, columnspan=2, pady=(10, 0))

        self.label_github.grid(row=9, column=0, columnspan=2)
        self.label_bug_report.grid(row=10, column=0, columnspan=2)

        ## Start GUI
        self.root.mainloop()

    
    def get_yt_urls_and_paths(self, pl_urls_and_paths):
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

    def list_chunkify(self, lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i+n]

    def download_from_mapping_multithreaded(self, urls, paths, mode, num_threads=5, show_progress=False, resolution="1080P"):
        mappings = list(zip(urls, paths))
        num_mappings = len(mappings)
    
        num_videos_per_thread = num_mappings // num_threads
        num_videos_remainder = num_mappings % num_threads

        if num_mappings < num_threads:
            num_videos_per_thread = 1

        mappings_by_threads = list(self.list_chunkify(mappings, num_videos_per_thread))

        if num_videos_per_thread >= 1 and num_videos_remainder > 0:
            last_valid_idx = num_threads - 1
            num_mappings_per_thread = len(mappings_by_threads)
            diff = num_mappings_per_thread - num_threads

            while diff > 0:
                cur_last_idx = last_valid_idx + diff 
                mappings_by_threads[cur_last_idx - 1].extend(mappings_by_threads[cur_last_idx])

                ## Remove the remainder mappings that were added to the last complete mappings set.
                mappings_by_threads = mappings_by_threads[:-1]
                num_mappings_per_thread = len(mappings_by_threads)
                diff = num_mappings_per_thread - num_threads
        
        # yt_downloaders = list()
        ## Start DownloaderThread workers.
        for mappings in mappings_by_threads:
            mappings = deque(mappings)
            num_mappings = len(mappings)

            if mode == "AUDIO":
                downloader = audioDownloaderThread(yt_audio_queue=mappings, init_num_audios=num_mappings, show_progress=show_progress)
            if mode == "VIDEO":
                downloader = videoDownloaderThread(yt_video_queue=mappings, init_num_videos=num_mappings, show_progress=show_progress, resolution=resolution)

            downloader.daemon = True
            downloader.start()
            # yt_downloaders.append(yt_downloader)
            time.sleep(1)

        # for yt_downloader in yt_downloaders:
        #     yt_downloader.join()

    def button_monitor(self):
        while True:
            if threading.activeCount() >= 2:
                ## Disable buttons
                self.download_button['state'] = 'disabled'
                self.exit_button['state'] = 'disabled'
                time.sleep(5)
            else:           
                ## Enable buttons
                self.download_button['state'] = 'normal'
                self.exit_button['state'] = 'normal'

    def main(self):
        ## Disable buttons
        self.download_button['state'] = 'disabled'

        p_url_and_path = r"(.*):(https?:.*)"
        pl_entries = self.text_pl_urls.get("1.0", 'end-1c')  ## 'end-1c' to remove 1 character, \n.
        pl_entries = pl_entries.splitlines()

        mode = self.cbox_mode.get()
        num_threads = int(self.cbox_thread.get())
        resolution = self.cbox_resolution.get()

        path_lst = list()
        pl_lst = list()

        for line in pl_entries:
            entry = re.findall(p_url_and_path, line)[0]
            path = entry[0]
            pl = entry[1]

            path_lst.append(path)
            pl_lst.append(pl)

        pl_mappings = list(zip(pl_lst, path_lst))
        yt_urls, pl_paths = self.get_yt_urls_and_paths(pl_mappings)

        self.download_from_mapping_multithreaded(urls=yt_urls, paths=pl_paths, mode=mode, num_threads=num_threads, show_progress=False, resolution=resolution)
        
        # buttonMonitorThread = threading.Thread(target=button_monitor, name="buttonMonitor")
        # buttonMonitorThread.daemon = True
        # buttonMonitorThread.run()
        # print("[MAIN] All Threads Had Successfully Finished Downloading Quests! \n")

if __name__ == '__main__':
    current_version = "1.2.0"
    YTDC_GUI = YTDC_GUI(current_version=current_version)
    YTDC_GUI.run()