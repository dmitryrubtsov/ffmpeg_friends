from bs4 import BeautifulSoup
import requests
import re


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


if __name__ == '__main__':
    dict_metadata = dict_episode()
