##written in Python 3.7
##Uses BeautifulSoup and urllib


from operator import concat
from pydoc import classname, plain
from turtle import title
from click import style
import requests
import urllib.request
import argparse
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
MISC_VALS = ['Weight', 'Damage Type','Weapon Art', 'Passive']

TOP_HEADERS = {"Weapon" : 1, "Upgrade Level": 1,
 #"Requirements" : 5, 
 "Attack Power": 6, "Attribute Scaling" : 5, "Passive" : 1, "Guard Stats": 7, "Misc" : 4}
BOTTOM_HEADERS = ['']*2 +  ATTACK_POWER + WEAPON_SCALING  + ["Passive"] + GUARD_STATS + MISC_VALS

class Weapon:
    def __init__(self, name, weapon_type, damage_type, weapon_art, weight, passive, stats):
        self.name = name
        self.weapon_type = weapon_type
        self.damage_type = damage_type
        self.weapon_art = weapon_art
        self.weight = weight
        self.passive = passive
        if stats is None: 
            stats = []
        self.stats = stats

    def ToString(self):
        rows = []
        for stat in self.stats:
            r = []
            r += [self.name, stat.upgrade_type]
            r += list(stat.attack_power.values())
            r += list(stat.damage_scaling.values())
            if stat.passive is None or stat.passive == '-':
                r += [self.passive]
            else:
                r += [stat.passive]
            r += list(stat.guard_stats.values())
            r += [self.weight, self.damage_type, self. weapon_art, self.passive]
            rows.append(r)

        return '\n'.join([','.join(r) for r in rows]) + '\n'

class WeaponStat:
    def __init__(self):

        self.required_stats = {
            'Str': None,
            'Dex': None,
            'Fai': None,
            'Fnt': None,
            'Arc': None
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
            'Str': None,
            'Dex': None,
            'Fai': None,
            'Fnt': None,
            'Arc': None
        }

        self.guard_stats = {
            'Phy': None,
            'Mag': None,
            'Fire': None,
            'Ligt': None,
            'Holy': None,
            'Boost': None,
        }

        self.upgrade_type = None
        self.damage_type = None
        self.weapon_skill = None
        self.passive = None
        self.weight = 0

class WeaponScraper:
    def __init__(self):


        chrome_options = webdriver.ChromeOptions()
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(chrome_options=chrome_options)

    def ScrapeWeapons(self, verbose=False):
        response = requests.get(WEAPONS_PAGE)
        soup = BeautifulSoup(response.content, 'html.parser')
        weapon_icons = soup.findAll('a', class_ = 'wiki_link wiki_tooltip', href=True)

        weapons_list = []

        if verbose:
            print("%d Weapons found", len(weapon_icons) - 1)

        #Replace 2 for full test
        for element in weapon_icons[1:]:
            
            weaponSoup =  self.GetWeaponPageSoup(BASE_PAGE + element['href'])
            try:          
                name = weaponSoup.find('a', id='page-title').text.split('|')[0].strip()
                if verbose:
                    print("Weapon stats for %s", name)

                infobox = weaponSoup.find('div', id='infobox')
                if infobox is not None:
                    infobox_rows = infobox.findAll('tr')
                    weapon_type = infobox_rows[4].findAll('a')[0].text.strip()
                    try:
                        damage_type = ''.join([e.text for e in infobox_rows[4].findAll()[1:]])
                    except Exception as e:
                        damage_type = '-'
                    weapon_art = infobox_rows[5].findAll('a')[0].text.strip()
                    weapon_weight = infobox_rows[6].findAll('a')[0].findParent().text.strip()
                    weapon_passive = infobox_rows[6].findAll('a')[1].findParent().text.strip()

                    if verbose:
                        print("type\tdamage type\tweapon art\tweight\tpassive")
                        print('%s\t%s\t\t%s\t\t%s\t%s', (weapon_type, damage_type, weapon_art, weapon_weight, weapon_passive))

                stat_list = []
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
                            stat.passive = rowVals[11]
                            stat_list.append(stat)

                else:
                    standard_upgrade_table = weaponSoup.find('span', text = 'Attack Power').find_parent('table', class_ = 'wiki_table')             
                    header_rows = standard_upgrade_table.findAll('th', style='text-align: center;')

                    headers = [r.find('strong').text.strip() for r in header_rows if r.find('strong') is not None]

                    table_rows = standard_upgrade_table.find('tbody').findAll('tr')[2:]

                    for row in table_rows:
                        stat = WeaponStat()
                        rowVals = [e.text.strip() for e in row.findAll('td')]

                        stat.upgrade_type = row.find('th').text.strip()
                        stat.attack_power = dict(zip(ATTACK_POWER, rowVals[:6]))
                        stat.damage_scaling = dict(zip(WEAPON_SCALING, rowVals[6: 11]))
                        stat.guard_stats = dict(zip(GUARD_STATS, rowVals[-7:]))
                        stat_list.append(stat)

                weapon = Weapon(name, weapon_type, damage_type, weapon_art, weapon_weight, weapon_passive, stat_list)
                weapons_list.append(weapon)
            except Exception as e:
                print("Failed to load weapon from %s", element['href'])
                print(e)
                continue

        return weapons_list               

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
    
    def PickleWeapons(self, weapons_list):
        pickle.dump(weapons_list, open(PICKLE_FILENAME, 'wb'))

def main(verbose, repickle, generate):  

    weapons = []

    if os.path.exists(PICKLE_FILENAME) and not repickle:
        weapons = pickle.load(open(PICKLE_FILENAME, 'rb'))                    

    else:
        scraper = WeaponScraper()
        weapons =  scraper.ScrapeWeapons(verbose)
        scraper.PickleWeapons(weapons)

    if generate:
        f = open('weapon_data.csv', 'w+')
        for k, v in TOP_HEADERS.items():
            f.write(k)
            f.write(','*v)
        f.write('\n')
        f.write(','.join(BOTTOM_HEADERS) + '\n')
        for weapon in weapons:
            f.write(weapon.ToString())
        f.close()
        


    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Print extra debug info')
    parser.add_argument('-r', '--repickle', action='store_true', help='Overwrtie any existing pickle file')
    parser.add_argument('-g', action='store_true', help='generate spreadsheet file')

    args = parser.parse_args()

    main(args.verbose, args.repickle, args.g)