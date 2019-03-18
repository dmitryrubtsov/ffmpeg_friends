from bs4 import BeautifulSoup
import requests
import re
import os
import subprocess


def dict_episode():
    ''' Функция для парсинга информации названий и описаний эпизодов c сайта.
        Функция возвращает dict = { [id episode]: (name, description)  } '''
    dict_episode = {}
    headers = {
        'User-Agent':
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36'
    }

    season = 1
    while season <= 10:
        url = 'https://www.imdb.com/title/tt0108778/episodes?season=' + \
            str(season)
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        episode_list = soup.find('div', {'class': 'list detail eplist'})
        items = episode_list.find_all(
            'div', {'class': ['list_item odd', 'list_item even']})

        for item in items:
            id_str = item.find('div', {
                'class': 'image'
            }).find('div').find('div').text
            id = "S" + "%02d" % int(re.search(r"(?<=S)\d+", id_str).group(0)) \
                + "E" + "%02d" % int(re.search(r"(?<=Ep)\d+", id_str).group(0))
            name = item.find('div', {'class': 'info'}).find('strong').text
            description = item.find('div', {'class': 'item_description'}).\
                text.strip("\n    ")
            dict_episode[id] = (name, description)
        season += 1
    return dict_episode


def return_maps_list(path):
    '''Функция возвращает maps. path(str) --> list'''
    out = subprocess.Popen(['ffmpeg', '-i', path],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    stdout, stderr = out.communicate()
    maps_dir = {}
    matches = re.finditer(r"(?<=Stream #)\d:\d\(\w+\): \w+", str(stdout),
                          re.MULTILINE)

    for matchNum, match in enumerate(matches):
        matchNum = matchNum + 1
        tracks = match.group()
        if tracks.endswith("Video"):
            maps_dir['video'] = tracks[0:3]
        if tracks.endswith("Audio"):
            track_lang = re.findall(r"(?<=\d:\d\()\w+", tracks)
            if track_lang[0] == "eng":
                maps_dir['audio_eng'] = tracks[0:3]
            if track_lang[0] == "rus":
                maps_dir['audio_rus'] = tracks[0:3]
        if tracks.endswith("Subtitle"):
            track_lang = re.findall(r"(?<=\d:\d\()\w+", tracks)
            if track_lang[0] == "eng":
                maps_dir['sub_eng'] = tracks[0:3]
    string_map = [
            "-map", maps_dir['video'],
            "-map", maps_dir['audio_eng'],
            "-map", maps_dir['audio_rus'],
            "-map", maps_dir['sub_eng']
            ]
    return string_map


def return_id_episode(path):
    '''Функция возвращает id episode. S01E01 --> str'''
    id_episode = re.findall(r"S\d{2}E\d{2}", path)
    return id_episode[0]


def return_metadata_list(id_episode):
    '''Функция возвращает metadata
    id_episode (str) --> list'''
    global dict_metadata
    metadata_list = []
    metadata_list.append("-metadata")
    metadata_list.append("title=" + dict_metadata[id_episode][0])
    metadata_list.append("-metadata")
    metadata_list.append("show=Friends")
    metadata_list.append("-metadata")
    metadata_list.append("season_number=" + id_episode[1:3])
    metadata_list.append("-metadata")
    metadata_list.append("episode_sort=" + id_episode[4:6])
    metadata_list.append("-metadata")
    metadata_list.append("description=" + dict_metadata[id_episode][1])
    return metadata_list


def ffmpeg(path):
    '''Функция конвертирует файл path набором библиотек ffmpeg.
    path(str) --> 1'''
    global OUTPATH

    id_episode = return_id_episode(path)
    numder_season = id_episode[1:3]

    file_dir = os.path.join(OUTPATH, "Season " + numder_season)
    file_path_out = os.path.join(
        file_dir, id_episode + " " + dict_metadata[id_episode][0] + ".m4v")

    if not os.path.exists(file_dir):
        os.makedirs(file_dir)

    ffmpeg_string = [
        "ffmpeg", "-i", path, "-c:v", "libx264", "-crf", "20", "-maxrate",
        "1M", "-bufsize", "2M", "-profile:v", "high", "-level", "4.2", "-c:a",
        "aac", "-q:a", "2", "-ac", "2", "-c:s", "mov_text"
        ]
    ffmpeg_string.extend(return_maps_list(path))
    ffmpeg_string.extend(return_metadata_list(id_episode))
    ffmpeg_string.append(file_path_out)

    subprocess.check_call(ffmpeg_string)
    return 1


def return_file_list(path, type_file):
    '''Функция возвращает лист файлов с расширением type_file из папки path.
    path(str), type_file(str) --> list'''
    file_list = []
    for root, dirs, files in os.walk(path):
        for _file in files:
            if _file.endswith(type_file):
                file_list.append(os.path.join(root, _file))
    return file_list


if __name__ == '__main__':
    root_dir = os.path.dirname(__file__)
    PATH = input('Input folder: ' + root_dir)
    OUTPATH = input('Destination folder: ' + root_dir + '/OUT/')

    if PATH == '':
        PATH = root_dir

    if OUTPATH == '':
        OUTPATH = os.path.join(root_dir, 'OUT')
        if not os.path.exists(OUTPATH):
            os.makedirs(OUTPATH)

    dict_metadata = dict_episode()
    file_list = return_file_list(PATH, ".mkv")

    for file_path in file_list:
        ffmpeg(file_path)
