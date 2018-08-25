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
import pprint
import itertools
########################################
###              CODES               ###
########################################

### Video ###
V_VP9_1080P = 248
V_MP4_1080P = 137

### Audio ###
A_OPUS_160KB = 251
A_MP4_128KB = 140

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
    ## Concrete Product (VIDEO)
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
            # except OSError:
            #     print("[ERROR (OSError) - {} - {}/{}] YouTube Video {} Had a Problem Processing And Was Skipped!\n".format(self.name, self._count, self._init_quantity, yt_url))
            #     self._count += 1
            #     continue

        print("[MAIN - {}] The Thread Has Finished Downloading All YouTube Videos Assigned!\nExiting Thread ... \n".format(self.name))

    def get_ffmpeg_path(self):
        if getattr(sys, 'frozen', False):
            ## Running in a Pyinstaller Executable.
            base_path = sys.executable
            base_path = os.path.dirname(base_path)
        else:
            ## Running in a Normal Python Environment.
            base_path = sys.path[0]

        ## Check Operating System
        if sys.platform == 'win32':
            ffmpeg_path = os.path.join(base_path, "lib", "ffmpeg", "win")
        elif sys.platform == 'darwin':
            ffmpeg_path = os.path.join(base_path, "lib", "ffmpeg", "mac")
        elif sys.platform.startswith('linux'):
            ffmpeg_path = os.path.join(base_path, "lib", "ffmpeg", "linux")
        
        ffmpeg_path = os.path.join(ffmpeg_path, "bin", "ffmpeg")

        return ffmpeg_path

    def get_available_1080p_codecs(self, yt):
        def remove_none_combinations_filter(comb):
            if comb is None:
                return False
            else:
                return True

        def check_combinations_filter(comb):
            if (yt.streams.get_by_itag(comb[0]) is not None) and (yt.streams.get_by_itag(comb[1]) is not None):
                return comb
            else:
                return None

        def get_available_1080p_codecs_helper(combination):
            return list(map(check_combinations_filter, combination))

        video_codec_tags = [V_VP9_1080P, V_MP4_1080P]
        audio_codec_tags = [A_OPUS_160KB, A_MP4_128KB]
        
        combinations = list(itertools.product(video_codec_tags, audio_codec_tags))
        opus_audio_combinations = list()
        mp4_audio_combinations = list()

        for comb in combinations:
            if A_OPUS_160KB in comb:
                opus_audio_combinations.append(comb)
            elif A_MP4_128KB in comb:
                mp4_audio_combinations.append(comb)
        
        available_combinations = list()
        ## Check Availabilities
        opus_audio_combinations = get_available_1080p_codecs_helper(opus_audio_combinations)
        mp4_audio_combinations = get_available_1080p_codecs_helper(mp4_audio_combinations)

        ### Push in all combinations, including the None ones resulted from get_available_1080p_codecs_helper().
        available_combinations.extend(opus_audio_combinations)
        available_combinations.extend(mp4_audio_combinations)

        ### Filter out the None objects
        available_combinations = list(filter(remove_none_combinations_filter, available_combinations))
        
        return available_combinations

    def get_title_and_file_ext(self, filename):
        if filename.endswith('.webm'):
            title = filename[:-5]
            file_ext = filename[-4:].upper()
        elif filename.endswith('.mp4'):
            title = filename[:-4]
            file_ext =  filename[-3:].upper()
        return title, file_ext

    def download_1080p_helper(self, yt, video_path):
        available_combinations = self.get_available_1080p_codecs(yt)
        ## Select the first/best quality combination.
        file_names = list()
        video_itag = available_combinations[0][0]
        audio_itag = available_combinations[0][1]

        ## Start Downloads
        ### Download Video Part
        video = yt.streams.get_by_itag(video_itag)
        codec_type = "VIDEO"
        title, video_file_ext = self.get_title_and_file_ext(video.default_filename)
        filename = title + codec_type
        file_names.append(filename)
        print("[HELPER - {} - {}/{}] Start Downloading YouTube 1080P - Video: {} ! \n".format(self.name, self._count, self._init_quantity, yt.watch_url))
        video.download(output_path=video_path, filename=filename)

        print("[HELPER - {} - {}/{}] Finished Downloading YouTube 1080P - Video: {} ! ".format(self.name, self._count, self._init_quantity, filename))
        print("[HELPER - {} - {}/{}] Saved Directory: {}. \n".format(self.name, self._count, self._init_quantity, video_path))

        ### Download Audio Part
        audio = yt.streams.get_by_itag(audio_itag)
        codec_type = "AUDIO"
        title, audio_file_ext = self.get_title_and_file_ext(audio.default_filename)
        filename = title + codec_type
        file_names.append(filename)
        print("[HELPER - {} - {}/{}] Start Downloading YouTube 1080P - Audio: {} ! \n".format(self.name, self._count, self._init_quantity, yt.watch_url))
        audio.download(output_path=video_path, filename=filename)

        print("[HELPER - {} - {}/{}] Finished Downloading YouTube 1080P - Audio: {} ! ".format(self.name, self._count, self._init_quantity, filename))
        print("[HELPER - {} - {}/{}] Saved Directory: {}. \n".format(self.name, self._count, self._init_quantity, video_path))

        ## Start Merging Audio & Video
        print("[HELPER - {} - {}/{}] Start Merging Audio & Video Using FFMPEG: {} ! \n".format(self.name, self._count, self._init_quantity, title))
        os.chdir(video_path)
        input_files = ['{}.{}'.format(file_names[0], video_file_ext), '{}.{}'.format(file_names[1], audio_file_ext)]
        ffmpeg_path = self.get_ffmpeg_path()
        print(ffmpeg_path)
        try:
            subprocess.call([ffmpeg_path, 
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

        except FileNotFoundError:
            print("[ERROR (FileNotFoundError) - {} - {}/{}] FFMPEG Library Is Missing. \n".format(self.name, self._count, self._init_quantity))
            pass

        print("[HELPER - {} - {}/{}] Finished Downloading and Merging Audio & Video for 1080p YouTube Video: {}. \n".format(self.name, self._count, self._init_quantity, title))

class audioDownloaderThread(genericDownloaderThread):
    ## Concrete Product (AUDIO)
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
    ## YouTube Download Center GUI
    def __init__(self, current_version):
        self._version = current_version
        self.root = Tk()

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
        ## Start DownloaderThread Workers.
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

    def download(self, download_button, text_pl_urls, cbox_mode, cbox_thread, cbox_resolution):
        ## Disable buttons
        download_button['state'] = 'disabled'

        p_url_and_path = r"(.*):(https?:.*)"
        pl_entries = text_pl_urls.get("1.0", 'end-1c')  ## 'end-1c' to remove 1 character, \n.

        if pl_entries == "":
            print("[ERROR] Please Enter At Least One Entry! \n")
            for i in range(5, 0, -1):
                print("[MAIN] Exiting In {} Seconds ... \n".format(str(i)))
                time.sleep(1)

            exit()

        pl_entries = pl_entries.splitlines()

        mode = cbox_mode.get()
        num_threads = int(cbox_thread.get())
        resolution = cbox_resolution.get()

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

    def run(self):
        # dynamic_entries = {}
        # def create_dynamic_entries(dynamic_entries, frame):
        #     num_entries = int(cbox_number_options.get())
        #     num_entries = tuple([str(i) for i in range(1, num_entries + 1)])

        #     url_label = Label(frame, text="URL", font='Helvetica 10 bold')
        #     url_label.grid(row=1, column=1, columnspan=2)
        #     path_label = Label(frame, text="PATH", font='Helvetica 10 bold')
        #     path_label.grid(row=1, column=3, columnspan=2)

        #     i = 2
        #     for number in num_entries:
        #         entry_label = Label(frame, text="Playlist {}: ".format(number), font='Helvetica 10 bold')
        #         entry_label.grid(row=i, column=0, columnspan=1)

        #         url_entry = Entry(frame)
        #         url_entry.grid(row=i, column=1, columnspan=2)

        #         path_entry = Entry(frame)
        #         path_entry.grid(row=i, column=3, columnspan=2)

        #         dynamic_entries[number] = [url_entry, path_entry]
        #         i += 1
        
        # def get_entry_values(dynamic_entries):
        #     for key, value in dynamic_entries.items():
        #         print(value[0].get())
        #         print(value[1].get())

        ## Setup TKinter Objects
        bulk_playlists_frame = Frame(self.root)
        bulk_playlists_frame.grid(row=1, column=0, columnspan=2)       

        label_pl_urls = Label(bulk_playlists_frame, text='Input YouTube PlayLists URLs: ', font='Helvetica 10 bold')
        text_pl_urls = ScrolledText(bulk_playlists_frame)
        label_mode = Label(bulk_playlists_frame, text='Select Mode (AUDIO/VIDEO): ', font='Helvetica 10 bold')

        mode_options = ("AUDIO", "VIDEO")
        cbox_mode = ttk.Combobox(bulk_playlists_frame, justify='center',values=mode_options, width=40, font='Helvetica 8 bold')
        label_num_threads = Label(bulk_playlists_frame, text='Select # of Thread Using: ', font='Helvetica 10 bold')

        thread_options = tuple([str(i) for i in range(1, 10+1)])
        cbox_thread = ttk.Combobox(bulk_playlists_frame, justify='center', values=thread_options, width=40, font='Helvetica 8 bold')

        label_resolution = Label(bulk_playlists_frame, text='Select Resolution (If VIDEO Mode): ', font='Helvetica 10 bold')

        resolution_options = ('1080P', '720P')
        cbox_resolution = ttk.Combobox(bulk_playlists_frame, justify='center', values=resolution_options, width=40, font='Helvetica 8 bold')

        label_warning = Label(bulk_playlists_frame, text='You Will Be Able To Cancel The Downloading Process By Clicking "EXIT" Button.', font='Helvetica 10 bold', fg="red")

        ### Define DOWNLOAD Button
        download_button = Button(bulk_playlists_frame, text="START DOWNLOAD", command=lambda: self.download(download_button, text_pl_urls, cbox_mode, cbox_thread, cbox_resolution), width=50, font='Helvetica 8 bold', cursor="hand2")
        
        ### Define EXIT Button
        exit_button = Button(bulk_playlists_frame, text="EXIT", width=50, command=self.root.destroy, font='Helvetica 8 bold', cursor="hand2")

        ### Author Disclaimer
        label_author = Label(bulk_playlists_frame, text='Developed By Sean Lee \u00A9 2018', font='Helvetica 8 bold')

        ### Github Links
        label_github = Label(bulk_playlists_frame, text='[Github] https://github.com/seanlee31/youtube-download-center', font='Helvetica 8 bold', fg="blue", cursor="hand2")
        label_bug_report = Label(bulk_playlists_frame, text='[BUG Report] https://github.com/seanlee31/youtube-download-center/issues', font='Helvetica 8 bold', fg="blue", cursor="hand2")

        ## Configure TKinter Objects
        self.root.title("YouTube Download Center v{}".format(self._version))
        label_pl_urls.grid(row=0, column=0, columnspan=2, pady=(10, 10))

        text_pl_urls.grid(row=1, column=0, columnspan=2)

        label_mode.grid(row=2, column=0)
        
        cbox_mode.current(1)
        cbox_mode.grid(row=2, column=1)

        label_num_threads.grid(row=3, column=0)

        cbox_thread.current(4)
        cbox_thread.grid(row=3, column=1)

        label_resolution.grid(row=4, column=0)

        cbox_resolution.current(0)
        cbox_resolution.grid(row=4, column=1)

        label_warning.grid(row=5, column=0, columnspan=2, pady=(10, 10))

        download_button.grid(row=6, column=0, columnspan=2)

        exit_button.grid(row=7, column=0, columnspan=2)

        label_author.grid(row=8, column=0, columnspan=2, pady=(10, 0))

        label_github.grid(row=9, column=0, columnspan=2)
        label_bug_report.grid(row=10, column=0, columnspan=2)
        
        # ## [Work IPR] Dynamic Entries
        # dynamic_entries_frame = Frame(self.root)
        # dynamic_entries_frame.grid(row=1, column=2, columnspan=2)

        # label_number_entry = Label(dynamic_entries_frame, text="Input # of Entries: ", font='Helvetica 10 bold')
        # label_number_entry.grid(row=22, column=0, columnspan=2)  ## Maximum 18 Entries

        # number_options = tuple([str(i) for i in range(1, 20+1)])
        # cbox_number_options = ttk.Combobox(dynamic_entries_frame, justify='center', values=number_options, width=40, font='Helvetica 8 bold')
        # cbox_number_options.grid(row=22, column=2, columnspan=2)
        # cbox_number_options.current(4)
        # ### Define Dynamic Entries Button
        # create_entries_button = Button(dynamic_entries_frame, text="CREATE EMPTY ENTRIES", command=lambda: create_dynamic_entries(dynamic_entries, dynamic_entries_frame), width=50, font='Helvetica 8 bold', cursor="hand2")
        # create_entries_button.grid(row=23, column=1, columnspan=2)
        # ### Define Get Entry Values Button
        # get_entry_values_button = Button(dynamic_entries_frame, text="Get Entries Values", command=lambda: get_entry_values(dynamic_entries), width=50, font='Helvetica 8 bold', cursor="hand2")
        # get_entry_values_button.grid(row=24, column=1, columnspan=2)

        ## Start GUI
        self.root.mainloop()


if __name__ == '__main__':
    current_version = "1.2.2"
    YTDC_GUI = YTDC_GUI(current_version=current_version)
    YTDC_GUI.run()