##written in Python 3.7
##Uses BeautifulSoup and urllib


from pydoc import classname, plain
from turtle import title
from click import style
import requests
import urllib.request
from bs4 import BeautifulSoup
import pickle
import os.path
import time
import re
from selenium import webdriver


PICKLE_FILENAME = "weaponStats.p"
WEAPONS_PAGE = 'https://eldenring.wiki.fextralife.com/Weapons'
BASE_PAGE = 'https://eldenring.wiki.fextralife.com'

ATTACK_POWER = ['Phy', 'Mag', 'Fire', 'Ligt', 'Holy', 'Sta']
WEAPON_SCALING = ['Str', 'Dex', 'Int', 'Fai', 'Arc']
GUARD_STATS = ['Phy', 'Mag', 'Fir', 'Lit', 'Hol', 'Bst', 'Rst']

class WeaponStat:
    def __init__(self):

        self.name= ''        
        self.upgrade_type = ''


        self.required_stats = {
            'str': None,
            'dex': None,
            'fai': None,
            'int': None,
            'arc': None
        }

        self.attack_power = {
            'Phy' : None,
            'Mag' : None,
            'Fire' : None,
            'Ligt' : None,
            'Holy' : None,
            'Stam' : None,    
        }

        self.damage_scaling = {
            'str': None,
            'dex': None,
            'fai': None,
            'int': None,
            'arc': None
        }

        self.guard_stats = {
            'Phy': None,
            'Mag': None,
            'Fire': None,
            'Ligt': None,
            'Holy': None,
            'Boost': None,
        }

        self.damage_type = None
        self.weapon_skill = None
        self.passive = None
        self.weight = 0

class WeaponScraper:
    def __init__(self):
        self.driver = webdriver.Chrome()

    def scrapeTest(self):
        response = requests.get(WEAPONS_PAGE)
        soup = BeautifulSoup(response.content, 'html.parser')
        weapon_icons = soup.findAll('a', class_ = 'wiki_link wiki_tooltip', href=True)

        #Replace 2 for full test
        for element in weapon_icons[1:10]:
            weaponSoup =  self.GetWeaponPageSoup(BASE_PAGE + element['href'])

            ##weapon = Weapon()

            max_upgrade_table = weaponSoup.find('h3', string=re.compile('Max'))
            if max_upgrade_table is not None:
                max_upgrade_table = max_upgrade_table.find_parent().find('table')
                if max_upgrade_table is not None:

                    header_rows = max_upgrade_table.findAll('th', style='text-align: center;')

                    headers = [r.find('strong').text.strip() for r in header_rows if r.find('strong') is not None]
                    table_rows = max_upgrade_table.find('tbody').findAll('tr')[2:]

                    for row in table_rows:
                        stat = WeaponStat()
                        rowVals = [e.text.strip() for e in row.findAll('td')]

                        stat.upgrade_type = row.find('th').text.strip()
                        stat.attack_power = dict(zip(ATTACK_POWER, rowVals[:6]))
                        stat.damage_scaling = dict(zip(WEAPON_SCALING, rowVals[6: 11]))
                        stat.guard_stats = dict(zip(GUARD_STATS, rowVals[-7:]))

            else:
                standard_upgrade_table = weaponSoup.find('span', text = 'Attack Power').find_parent('table', class_ = 'wiki_table')             
                header_rows = standard_upgrade_table.findAll('th', style='text-align: center;')

                headers = [r.find('strong').text.strip() for r in header_rows if r.find('strong') is not None]
                print(headers)

                table_rows = standard_upgrade_table.find('tbody').findAll('tr')[2:]

                for row in table_rows:
                    stat = WeaponStat()
                    rowVals = [e.text.strip() for e in row.findAll('td')]

                    stat.upgrade_type = row.find('th').text.strip()
                    print(stat.upgrade_type)
                    stat.attack_power = dict(zip(ATTACK_POWER, rowVals[:6]))
                    stat.damage_scaling = dict(zip(WEAPON_SCALING, rowVals[6: 11]))
                    stat.guard_stats = dict(zip(GUARD_STATS, rowVals[-7:]))

                    print(stat.attack_power)
                    print(stat.damage_scaling)
                    print(stat.guard_stats)   
               
    def GetWeaponPageSoup(self, href):
        self.driver.get(href)
        lastHeight = self.driver.execute_script("return document.body.scrollHeight")
        count = 1
        while count > 100:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            newHeight = self.driver.execute_script("return document.body.scrollHeight")
            if newHeight == lastHeight:
                break
            lastHeight = newHeight
            count += 1

        html = self.driver.page_source
        return BeautifulSoup(html, "html.parser")

    def getEpisodeFromSoup(self, episodeSoup):    
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
    

        # pickle.dump(episodeList, open(PICKLE_FILENAME, 'wb'))

def main():    
    # if os.path.exists(PICKLE_FILENAME):
    #     f = open('weapon_data.csv', 'w+')
    #     f.write("Season,Episode,Description,Tags,Link\n")
    #     episodes = pickle.load(open(PICKLE_FILENAME, 'rb'))
    #     for e in episodes:
    #         f.write(e.toString())
    #     f.close()
    scraper = WeaponScraper()
    scraper.scrapeTest()

    
if __name__ == '__main__':
    main()