from pytube import Playlist, YouTube, exceptions
import sys
import threading
from collections import deque
import pprint
import time
import os

########################################
### Producer/Consumer Design Pattern ###
########################################

V_MP4_1080P = 137
A_MP4_128KB = 140

VA_MP4_720P = 22

class ytDownloaderThread(threading.Thread):
    ## Consumer
    def __init__(self, yt_video_queue, init_num_videos, show_progress=False):
        super().__init__()
        self._yt_video_queue = yt_video_queue
        self.init_num_videos = init_num_videos
        self.show_progress = show_progress
        self.count = 1

    def run(self):
        while len(self._yt_video_queue) > 0:
            yt_video = self._yt_video_queue.popleft()
            yt_url = yt_video[0]
            pl_path = yt_video[1]
            self.check_path(pl_path)
            try:
                if self.show_progress:
                    yt = YouTube(yt_url, on_progress_callback=self.progress_function)
                else:
                    yt = YouTube(yt_url)
                # video = yt.streams.filter(subtype='mp4').all()
                # video = yt.streams.get_by_itag(V_MP4_1080P)
                # audio = yt.streams.get_by_itag(A_MP4_128KB)
                video = yt.streams.get_by_itag(VA_MP4_720P)
                start_time = time.time()
                print("[Main - {} - {}/{}] YouTube Video {} w/ {} Download Has Started ...\n".format(self.name, self.count, self.init_num_videos, yt_url, video.resolution))
                video.download(pl_path)
                end_time = time.time()
                diff_time = end_time - start_time
                print("[Main - {} - {}/{}] YouTube Video {} w/ {} Was Successfully Downloaded -- Took {:.2f}s!\n".format(self.name, self.count, self.init_num_videos, yt_url, video.resolution, diff_time))
                self.count += 1
            except exceptions.RegexMatchError:
                print("[Error - {} - {}/{}] YouTube Video {} Had a Problem Processing And Was Skipped!\n".format(self.name, self.count, self.init_num_videos, yt_url))
                self.count += 1
                continue
            

        print("[Main - {}] The Thread Has Finished Downloading All YouTube Videos {}!\nExiting Thread ... \n".format(self.name, yt_url))

    def progress_function(self, stream, chunk, file_handle, bytes_remaining):
        total_size = stream.filesize
        percent = 100.
        while percent <= 100.:
            if percent % 10. == 0.:
                print('[Downloading - {} - {}/{}] {:.2f}%\n'.format(self.name, self.count, self.init_num_videos, percent))
            percent = self.percent(bytes_remaining, total_size)

    def percent(self, bytes_remaining, total_size):
        percent = (float(bytes_remaining) / float(total_size)) * 100.
        return percent

    def check_path(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
            print("[Main - {}] The Missing Folder/Directory, {}, Has Been Created!\n".format(self.name, path))
            
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

def download_from_mapping_multithreaded(yt_urls, pl_paths, num_threads=5, show_progress=False):
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

    ## Start ytDownloaderThread workers.
    for mappings in mappings_by_threads:
        mappings = deque(mappings)
        num_mappings = len(mappings)
        yt_downloader = ytDownloaderThread(yt_video_queue=mappings, init_num_videos=num_mappings, show_progress=show_progress)

        yt_downloader.start()
        time.sleep(1)
        # yt_downloader.join()    ## Commented out to avoid waiting for current thread to finish processing (Used for debugging)

if __name__ == '__main__':  ## python youtube-downloader.py [num_threads] ([storage_directory] [youtube playlists]) ...
    if len(sys.argv) < 3:
        print("Please provide more than ONE Youtube Playlists. \n")
        exit()

    num_threads = int(sys.argv[1])
    pl_lst = list()
    path_lst = list()

    for i in range(2, len(sys.argv[2:]), 2):
        path_lst.append(sys.argv[i])
        pl_lst.append(sys.argv[i+1])

    pl_mappings = list(zip(pl_lst, path_lst))
    yt_urls, pl_paths = get_yt_urls_and_paths(pl_mappings)
    download_from_mapping_multithreaded(yt_urls=yt_urls, pl_paths=pl_paths, num_threads=num_threads, show_progress=False)