##written in Python 3.7
##Uses BeautifulSoup and urllib


from cgitb import text
from operator import concat
from pydoc import classname, plain
from turtle import title
from click import style
from pyparsing import Regex
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

    def __init__(self):

        self.damage_type = None
        self.weapon_skill = None
        self.passive = None
        self.weight = 0
        self.stats = []

        self.required_stats = {
            'Str': None,
            'Dex': None,
            'Fai': None,
            'Fnt': None,
            'Arc': None
        }

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
    
        for element in weapon_icons[1:]:
            weapon = Weapon()
            weaponSoup =  self.GetWeaponPageSoup(BASE_PAGE + element['href'])
            try:          
                weapon.name = weaponSoup.find('a', id='page-title').text.split('|')[0].strip()
                if verbose:
                    print("Weapon stats for %s", (weapon.name))

                infobox = weaponSoup.find('div', id='infobox')
                if infobox is not None:
                    infoTable = infobox.find('table')
                    if infoTable is not None:
                        self.PopulateWeaponStats(infoTable, weapon)

                stat_list = []
                max_upgrade_table = weaponSoup.find('h3', string=re.compile('Max'))
                if max_upgrade_table is not None:
                    max_upgrade_table = max_upgrade_table.find_parent().find('table')

                    self.PopulateWeaponAttributesFromTable(max_upgrade_table, weapon)

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

                weapons_list.append(weapon)
            except Exception as e:
                print("Failed to load weapon from %s", element['href'])
                print(e)
                continue

        return weapons_list 

    def PopulateWeaponStats(self, table, weapon):
        tableRows = table.findAll('tr')
        reqImg = table.find('img', title='Attributes Requirement')
        if reqImg is not None:
            requirementsRow  = reqImg.find_parent('td')

        for k in WEAPON_SCALING:
            if requirementsRow.find('a', string=re.compile(k)) is not None:
                weapon.required_stats[k] =  re.sub('[^0-9]', '', requirementsRow.find('a', text=re.compile(k)).next_sibling.text)

        


    def PopulateWeaponAttributesFromTable(self, table, weapon):
        header_rows = table.find('tr').findAll('th')
        headerDict = {h.find('span').text.strip() : 1 if h.get('colspan') is None else int(h['colspan']) for h in header_rows}
        headerIndexArray = []
        for x in headerDict :
            headerIndexArray.extend([x]*headerDict[x]) 

        data_rows = table.findAll('tr')[2:]

        for row in data_rows:
            stat = WeaponStat()
            upgrade_type = row.find('th')
            if upgrade_type is not None:
                stat.upgrade_type = upgrade_type.text
            row_values = [x.text.strip() for x in row.findAll('td')]
            stat.attack_power = dict(zip(ATTACK_POWER, [row_values[i] for (i, x) in enumerate(headerIndexArray) if x == 'Attack Power' ]))
            stat.damage_scaling = dict(zip(WEAPON_SCALING, [row_values[i] for (i, x) in enumerate(headerIndexArray) if x == 'Stat Scaling' ]))            
            passiveCell = row.findAll('td')[headerIndexArray.index("Passive Effects")]
            if passiveCell.find('a') is not None:
                stat.passive = passiveCell.find('a').get('href')[1:] + ' ' + passiveCell.find('a').text
            else:
                stat.passive = passiveCell.text
            stat.guard_stats = dict(zip(GUARD_STATS, [row_values[i] for (i, x) in enumerate(headerIndexArray) if x == 'Damage Reduction (%)' ]))
            
            weapon.stats.append(stat)

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
    parser.add_argument('-r', '--repickle', action='store_true', default=True, help='Overwrite any existing pickle file')
    parser.add_argument('-g', action='store_true', help='generate spreadsheet file')

    args = parser.parse_args()

    main(args.verbose, args.repickle, args.g)