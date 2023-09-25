from cmath import e
from datetime import datetime, timedelta
import os
import subprocess
import xml.etree.ElementTree as ET
import ffmpeg
import requests

MEDIA_STATIC_PATH = "app/static/media"

class PlexInfo:
    def __init__(self, username):
        self.plex_url = os.environ.get("PLEX_URL")
        self.plex_token = os.environ.get("PLEX_TOKEN")
        self.params = (("X-Plex-Token", {self.plex_token}),)
        self.sessions_xml = self._get_current_sessions_xml()
        self.username = username
        self.session_id = self._get_session_id(username)
        self.media_key = self._get_media_key()
        self.media_path_xml = self._get_media_path_xml()
        self.media_path = self._get_file_path()
        self.media_fps = self._get_media_fps()
        self.media_type = self._get_file_type()
        self.media_title = self._get_file_title()
        self.current_media_time_int = self._get_current_media_time()
        self.current_media_time_str = Utils(offset=self.current_media_time_int).offset_to_time

    def _get_media_fps(self):
        media_dict = list(list(list(list(list(self.media_path_xml)[0]))[0])[0])[0].attrib
        return float(media_dict["frameRate"])

    def _get_current_media_time(self):
        media_dict = list(list(self.sessions_xml))[self.session_id].attrib
        return int(media_dict["viewOffset"])

    def _get_current_sessions_xml(self):
        response = requests.get(f"{self.plex_url}/status/sessions", params=self.params)
        xml_content = ET.fromstring(response.content)
        return xml_content

    def _get_file_path(self):
        media_dict = list(list(list(list(self.media_path_xml)[0]))[0])[0].attrib
        return media_dict["file"]

    def _get_file_title(self):
        if self.media_type == "episode":
            video_dict = list(list(self.media_path_xml))[0].attrib
            title = video_dict["title"]
            show_name = video_dict["grandparentTitle"]
            return f"{show_name} - {title}"
        else:
            video_dict = list(list(self.media_path_xml))[0].attrib
            return video_dict["title"]

    def _get_file_type(self):
        video_dict = list(list(self.media_path_xml))[0].attrib
        return video_dict["type"]

    def _get_media_path_xml(self):
        response = requests.get(f"{self.plex_url}{self.media_key}", params=self.params)
        xml_content = ET.fromstring(response.content)
        return xml_content
        
    def _get_media_key(self):
        media_info = list(list(self.sessions_xml))[self.session_id].attrib
        return media_info["key"]

    def _get_session_id(self, username):
        for sessions in list(self.sessions_xml):
            for session in sessions:
                if session.tag == "User" and session.attrib["title"] == username:
                    return list(self.sessions_xml).index(sessions)
        raise Exception(f"No stream running for user {username}")

class Snapshot:
    def __init__(self, media_path: str, time: str, fps: float):
        self.media_path = media_path
        self.time = time
        self.fps = int(fps)

    def _download_frames(self):
        cmd = f"ffmpeg -ss {self.time} -i {self.media_path} -vframes {self.fps} -qscale:v 2 {MEDIA_STATIC_PATH}/images/{self.time.replace(':','_')}_%03d.jpg"
        a = subprocess.call(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

class Video:
    def convert_path_to_linux(self, path):
        # Convert drive letter to lowercase and replace backslashes with forward slashes
        linux_path = '/' + path[0].lower() + path[2:].replace('\\', '/')
        return linux_path
        
    def __init__(self, plex_data: PlexInfo, time: str, duration, file_name: str):
        self.media_path = plex_data.media_path
        self.time = time
        self.duration = duration
        self.file_name = file_name
        self.media_path_converted = self.convert_path_to_linux(self.media_path)
        print(f"Original Path: {self.media_path}")
        print(f"Converted Path: {self.media_path_converted}")

    def extract_video(self):
        (
            ffmpeg
            .input(self.media_path_converted, ss=self.time, t=self.duration)
            .output(f"{MEDIA_STATIC_PATH}/videos/{self.file_name}.mp4", 
                    map_metadata=-1, 
                    vcodec="libx264", 
                    acodec="libvorbis", 
                    pix_fmt="yuv420p", 
                    crf=18)
            .run(capture_stdout=True)
        )

class Utils:
    def __init__(self, offset: int=0):
        self.offset_to_time = self.milli_to_string(offset)

    def milli_to_string(self, millisec: int) -> str:
        time = str(timedelta(milliseconds=millisec))
        if len(time.split(":")[0]) < 2:
            time = f"0{time}"
        return time.split(".")[0]

    def add_time(self, current_time: str, time_to_add: int) -> str:
        time_obj = datetime.strptime(current_time, "%H:%M:%S")
        time_obj_with_time_added = time_obj + timedelta(seconds=time_to_add)
        return time_obj_with_time_added.strftime("%H:%M:%S")

    def _pad_time(self, time) -> str:
        if len(str(time)) < 2:
            time = f"0{time}"
        return time

    def calculate_clip_time(self, start, end) -> int:
        start = start.split(":")
        start_total_sec = (int(start[0])*3600) + (int(start[1])*60) + (int(start[2]))
        end = end.split(":")
        end_total_sec = (int(end[0])*3600) + (int(end[1])*60) + (int(end[2]))
        total_second = end_total_sec - start_total_sec
        return total_second

    def get_images_in_folder() -> list:
        folder = os.path.join(MEDIA_STATIC_PATH, "images")
        folder_list = []
        for a in os.listdir(folder):
            a = f"{folder}/{a}"
            folder_list.append(f"{a.split('/')[-4]}/{a.split('/')[-3]}/{a.split('/')[-2]}/{a.split('/')[-1]}")
        return sorted(folder_list)

    def get_videos_in_folder() -> list:
        folder = os.path.join(MEDIA_STATIC_PATH, "videos")
        folder_list = []
        for file in os.listdir(folder):
            file_dict = {}
            file = os.path.join(folder, file)
            metadata = ffmpeg.probe(file)["format"]["tags"]
            file_dict["file_path"] = "/".join(file.split("/")[1:])
            file_dict["title"] = metadata.get("title") or ""
            file_dict["original_start_time"] = metadata.get("comment") or ""
            file_dict["username"] = metadata.get("artist") or ""
            file_dict["show"] = metadata.get("show") or ""
            file_dict["season"] = metadata.get("season_number") or ""
            file_dict["episode"] = metadata.get("episode_id") or ""
            folder_list.append(file_dict)
        return sorted(folder_list, key=lambda x: x["original_start_time"], reverse=True)

    def get_videos_in_folder() -> list:
        folder = os.path.join(MEDIA_STATIC_PATH, "videos")
        folder_list = []
        for file in os.listdir(folder):
            file_dict = {}
            file = os.path.join(folder, file)
            metadata = ffmpeg.probe(file)["format"]["tags"]
            file_dict["file_path"] = "/".join(file.split("/")[1:])
            file_dict["title"] = metadata.get("title") or ""
            file_dict["original_start_time"] = metadata.get("comment") or ""
            file_dict["username"] = metadata.get("artist") or ""
            file_dict["show"] = metadata.get("show") or ""
            file_dict["episode_number"] = metadata.get("episode_id") or ""
            file_dict["season_number"] = metadata.get("season_number") or ""
            folder_list.append(file_dict)
        return folder_list

    def delete_file(self, file_path) -> bool:
        try:
            os.remove(f"./app/{file_path}")
            return True
        except:
            return False

    def streamable_upload(self, file_path) -> str:
        file_processed = {
            "file": (file_path.split("/")[-1], open(f"app/{file_path}", "rb")),
        }
        email = os.environ.get("STREAMABLE_LOGIN") or ""
        password = os.environ.get("STREAMABLE_PASSWORD") or ""
        try:
            response = requests.post("https://api.streamable.com/upload", auth=(email, password), files=file_processed).json()
            return response
        except Exception as e:
            raise Exception(f"Problem uploading to streamable: {e}")
