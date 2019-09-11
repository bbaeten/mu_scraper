
##written in Python 3.7
##Uses BeautifulSoup and urllib


import requests
import urllib.request
from bs4 import BeautifulSoup
import pickle
import os.path



PICKLE_FILENAME = "MU_Episodes.p"
MU_EPISODE_PAGE = 'https://mysteriousuniverse.org/category/podcasts/'


class Episode:
    def __init__(self, season, number, tags, description, downloadLink):
        self.season = season
        self.number = number
        self.tags = tags
        self.description = description
        self.downloadLink = downloadLink

    def toString(self):
        return '{},{},"{}",{},{}\n'.format(
                self.season,
                self.number,
                self.description,
                ' '.join(self.tags),
                self.downloadLink)


def getEpisodeFromSoup(episodeSoup):    
    header = episodeSoup.find('h2', class_ = "entry-title")    
    epNumbers = header.find('a')['title'].split('.')
    tags = [c.replace('tag-', '') for c in episodeSoup['class'] if c.startswith('tag') ]
    
    if len(epNumbers) > 1:
        season = epNumbers[0]
        number = epNumbers[1][:2]
    else:
        season = ''
        number = header.find('a')['title']

    epdisodeResponse = requests.get(header.find('a')['href'])
    episodeSoup = BeautifulSoup(epdisodeResponse.content, "html.parser")
    description = episodeSoup.findAll('p', class_ = "")[0].text
    dlDiv = episodeSoup.find('div', class_ = "mejs-download")
    if dlDiv is not None:
        downloadLink = dlDiv.find('a')['href']
    else: downloadLink = ""

    return Episode(season, number, tags, description, downloadLink)

def buildEpisodeList():
    episodeList = []    
    response = requests.get(MU_EPISODE_PAGE)
    soup = BeautifulSoup(response.content, 'html.parser')
    nextButton = soup.find('a', class_ = "next page-numbers")
    while(nextButton is not None):
        response = requests.get(nextButton['href'])        
        nextButton = soup.find('a', class_ = "next page-numbers")
        soup = BeautifulSoup(response.content, 'html.parser')
        episodes = [x for x in soup.findAll('article')]
        for e in episodes:
            try:
                episodeList.append(getEpisodeFromSoup(e))
            except Exception as e:
                print(e)
                continue        

    pickle.dump(episodeList, open(PICKLE_FILENAME, 'wb'))

def main():    
    if os.path.exists(PICKLE_FILENAME):
        f = open('Episode_List.csv', 'w+')
        f.write("Season,Episode,Description,Tags,Link\n")
        episodes = pickle.load(open(PICKLE_FILENAME, 'rb'))
        for e in episodes:
            f.write(e.toString())
        f.close()

    buildEpisodeList()
    
if __name__ == '__main__':
    main()