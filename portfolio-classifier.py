import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
import uuid
import argparse
import re
from jsonpath_ng.ext import parse
from typing import NamedTuple
from itertools import cycle
from collections import defaultdict
from jinja2 import Environment, BaseLoader
import requests
import requests_cache
from bs4 import BeautifulSoup 
import os
import json


requests_cache.install_cache(expire_after=60) #cache downloaded files for 1 minute
requests_cache.remove_expired_responses()


COLORS = [
  "#C0B0A0",
  "#CD9575",
  "#FDD9B5",
  "#78DBE2",
  "#87A96B",
  "#FFA474",
  "#FAE7B5",
  "#9F8170",
  "#FD7C6E",
  "#000000",
  "#ACE5EE",
  "#1F75FE",
  "#A2A2D0",
  "#6699CC",
  "#0D98BA",
  "#7366BD",
  "#DE5D83",
  "#CB4154",
  "#B4674D",
  "#FF7F49",
  "#EA7E5D",
  "#B0B7C6",
  "#FFFF99",
  "#1CD3A2",
  "#FFAACC",
  "#DD4492",
  "#1DACD6",
  "#BC5D58",
  "#DD9475",
  "#9ACEEB",
  "#FFBCD9",
  "#FDDB6D",
  "#2B6CC4",
  "#EFCDB8",
  "#6E5160",
  "#CEFF1D",
  "#71BC78",
  "#6DAE81",
  "#C364C5",
  "#CC6666",
  "#E7C697",
  "#FCD975",
  "#A8E4A0",
  "#95918C",
  "#1CAC78",
  "#1164B4",
  "#F0E891",
  "#FF1DCE",
  "#B2EC5D",
  "#5D76CB",
  "#CA3767",
  "#3BB08F",
  "#FEFE22",
  "#FCB4D5",
  "#FFF44F",
  "#FFBD88",
  "#F664AF",
  "#AAF0D1",
  "#CD4A4C",
  "#EDD19C",
  "#979AAA",
  "#FF8243",
  "#C8385A",
  "#EF98AA",
  "#FDBCB4",
  "#1A4876",
  "#30BA8F",
  "#C54B8C",
  "#1974D2",
  "#FFA343",
  "#BAB86C",
  "#FF7538",
  "#FF2B2B",
  "#F8D568",
  "#E6A8D7",
  "#414A4C",
  "#FF6E4A",
  "#1CA9C9",
  "#FFCFAB",
  "#C5D0E6",
  "#FDDDE6",
  "#158078",
  "#FC74FD",
  "#F78FA7",
  "#8E4585",
  "#7442C8",
  "#9D81BA",
  "#FE4EDA",
  "#FF496C",
  "#D68A59",
  "#714B23",
  "#FF48D0",
  "#E3256B",
  "#EE204D",
  "#FF5349",
  "#C0448F",
  "#1FCECB",
  "#7851A9",
  "#FF9BAA",
  "#FC2847",
  "#76FF7A",
  "#9FE2BF",
  "#A5694F",
  "#8A795D",
  "#45CEA2",
  "#FB7EFD",
  "#CDC5C2",
  "#80DAEB",
  "#ECEABE",
  "#FFCF48",
  "#FD5E53",
  "#FAA76C",
  "#18A7B5",
  "#EBC7DF",
  "#FC89AC",
  "#DBD7D2",
  "#17806D",
  "#DEAA88",
  "#77DDE7",
  "#FFFF66",
  "#926EAE",
  "#324AB2",
  "#F75394",
  "#FFA089",
  "#8F509D",
  "#FFFFFF",
  "#A2ADD0",
  "#FF43A4",
  "#FC6C85",
  "#CDA4DE",
  "#FCE883",
  "#C5E384",
  "#FFAE42"
]


taxonomies = {'Asset-Type': {'url': 'https://www.emea-api.morningstar.com/sal/sal-service/fund/process/asset/v2/{secid}/data',
                             'component': 'sal-components-mip-asset-allocation',
                             'jsonpath': '$.allocationMap',                                              
                             'category': '',                                                
                             'percent': 'netAllocation',
                             'url2': 'https://www.emea-api.morningstar.com/sal/sal-service/stock/equityOverview/{secid}/data',
                             'component2': 'sal-eqsv-overview',
                             'jsonpath2': '$.securityName',                                              
                             'map':{"AssetAllocNonUSEquity":"Stocks", 
                                    "CANAssetAllocCanEquity" : "Stocks", 
                                    "CANAssetAllocUSEquity" : "Stocks",
                                    "CANAssetAllocInternationalEquity": "Stocks",
                                    "AssetAllocUSEquity":"Stocks",
                                    "AssetAllocCash":"Cash",
                                    "CANAssetAllocCash": "Stocks",
                                    "AssetAllocBond":"Bonds", 
                                    "CANAssetAllocFixedIncome": "Bonds",
                                    "UK bond":"Bonds",
                                    "AssetAllocNotClassified":"Other",
                                    "AssetAllocOther":"Other",
                                    "CANAssetAllocOther": "Other"
                                    }
                             },
              'Stock-style': {'url': 'https://www.emea-api.morningstar.com/sal/sal-service/fund/process/weighting/{secid}/data',
                            'component': 'sal-components-mip-style-weight',
                            'jsonpath': '$',
                            'category': '',
                            'percent': '',
                            'url2': 'https://www.emea-api.morningstar.com/sal/sal-service/stock/equityOverview/{secid}/data',
                            'component2': 'sal-eqsv-overview',
                            'jsonpath2': '$.investmentStyle',
                            'map':{ "largeValue":"Large Value",
                                    "largeBlend":"Large Blend", 
                                    "largeGrowth":"Large Growth",
                                    "middleValue":"Mid-Cap Value",
                                    "middleBlend":"Mid-Cap Blend", 
                                    "middleGrowth":"Mid-Cap Growth",
                                    "smallValue":"Small Value",
                                    "smallBlend":"Small Blend",
                                    "smallGrowth":"Small Growth",
                                    },
                            'map2':{"1":"Large Value",
                                    "2":"Large Blend", 
                                    "3":"Large Growth",
                                    "4":"Mid-Cap Value",
                                    "5":"Mid-Cap Blend", 
                                    "6":"Mid-Cap Growth",
                                    "7":"Small Value",
                                    "8":"Small Blend",
                                    "9":"Small Growth",
                                    }   
                            },                            

              'Sector': {'url': 'https://www.emea-api.morningstar.com/sal/sal-service/fund/portfolio/v2/sector/{secid}/data',
                         'component': 'sal-components-mip-sector-exposure',
                         'jsonpath': '$.EQUITY.fundPortfolio',
                         'category': '',
                         'percent': '',
                         'url2': 'https://www.emea-api.morningstar.com/sal/sal-service/stock/equityOverview/{secid}/data',
                         'component2': 'sal-eqsv-overview',
                         'jsonpath2': '$.sector',
                         'map':{"basicMaterials":"Basic Materials", 
                                "communicationServices":"Communication Services",
                                "consumerCyclical":"Consumer Cyclical",
                                "consumerDefensive":"Consumer Defensive", 
                                "energy":"Energy",
                                "financialServices":"Financial Services",
                                "healthcare":"Healthcare",
                                "industrials":"Industrials",
                                "realEstate":"Real Estate",
                                "technology":"Technology",
                                "utilities":"Utilities",
                                }
                         },   
              'Holding': {'url':'https://www.emea-api.morningstar.com/sal/sal-service/fund/portfolio/holding/v2/{secid}/data',
                          'component': 'sal-components-mip-holdings',
                          'jsonpath': '$.equityHoldingPage.holdingList[*]',
                          'category': 'securityName',
                          'percent': 'weighting',
                          'url2': 'https://www.emea-api.morningstar.com/sal/sal-service/stock/equityOverview/{secid}/data',
                          'component2': 'sal-eqsv-overview',
                          'jsonpath2': '$.securityName',     
                         },  
              'Region': { 'url': 'https://www.emea-api.morningstar.com/sal/sal-service/fund/portfolio/regionalSector/{secid}/data',
                         'component': 'sal-components-mip-region-exposure',
                         'jsonpath': '$.fundPortfolio',
                         'category': '',
                         'percent': '',
                         'url2': 'https://www.emea-api.morningstar.com/sal/sal-service/stock/companyProfile/{secid}',
                         'component2': '',
                         'jsonpath2': '$..contact.country',
                         'map':{"northAmerica":"North America", 
                                "europeDeveloped":"Europe Developed",
                                "asiaDeveloped":"Asia Developed",
                                "asiaEmerging":"Asia Emerging", 
                                "australasia":"Australasia",
                                "europeDeveloped":"Europe Developed",
                                "europeEmerging":"Europe Emerging",
                                "japan":"Japan",
                                "latinAmerica":"Central & Latin America",
                                "unitedKingdom":"United Kingdom",
                                "africaMiddleEast":"Middle East / Africa",
                                },
                         'map2':{ "Aruba": "Central & Latin America",
                                  "Afghanistan": "Asia Emerging",
                                  "Angola": "Middle East / Africa",
                                  "Anguilla": "Central & Latin America",
                                  "Albania": "Europe Emerging",
                                  "Andorra": "Europe Developed",
                                  "UnitedArabEmirates": "Middle East / Africa",
                                  "Argentina": "Central & Latin America",
                                  "Armenia": "Asia Emerging",
                                  "AmericanSamoa": "Asia Emerging",
                                  "AntiguaAndBarbuda": "Central & Latin America",
                                  "Australia": "Australasia",
                                  "Austria": "Europe Developed",
                                  "Azerbaijan": "Asia Emerging",
                                  "Burundi": "Middle East / Africa",
                                  "Belgium": "Europe Developed",
                                  "Benin": "Middle East / Africa",
                                  "BurkinaFaso": "Middle East / Africa",
                                  "Bangladesh": "Asia Emerging",
                                  "Bulgaria": "Europe Emerging",
                                  "Bahrain": "Middle East / Africa",
                                  "Bahamas": "Central & Latin America",
                                  "BosniaAndHerzegovina": "Europe Emerging",
                                  "Belarus": "Europe Emerging",
                                  "Belize": "Central & Latin America",
                                  "Bermuda": "Central & Latin America",
                                  "Bolivia": "Central & Latin America",
                                  "Brazil": "Central & Latin America",
                                  "Barbados": "Central & Latin America",
                                  "BruneiDarussalam": "Asia Developed",
                                  "Bhutan": "Asia Emerging",
                                  "BouvetIsland": "Middle East / Africa",
                                  "Botswana": "Middle East / Africa",
                                  "CentralAfricanRepublic": "Middle East / Africa",
                                  "Canada": "North America",
                                  "CocosKeelingIslands": "Asia Emerging",
                                  "Switzerland": "Europe Developed",
                                  "Chile": "Central & Latin America",
                                  "China": "Asia Emerging",
                                  "CoteDIvoire": "Middle East / Africa",
                                  "Cameroon": "Middle East / Africa",
                                  "CongoDemocraticRepublic": "Middle East / Africa",
                                  "Congo": "Middle East / Africa",
                                  "CookIslands": "Asia Emerging",
                                  "Colombia": "Central & Latin America",
                                  "Comoros": "Middle East / Africa",
                                  "CapeVerde": "Middle East / Africa",
                                  "CostaRica": "Central & Latin America",
                                  "Cuba": "Central & Latin America",
                                  "ChristmasIsland": "Asia Emerging",
                                  "CaymanIslands": "Central & Latin America",
                                  "Cyprus": "Europe Developed",
                                  "CzechRepublic": "Europe Emerging",
                                  "Germany": "Europe Developed",
                                  "Djibouti": "Middle East / Africa",
                                  "Dominica": "Central & Latin America",
                                  "Denmark": "Europe Developed",
                                  "DominicanRepublic": "Central & Latin America",
                                  "Algeria": "Middle East / Africa",
                                  "Ecuador": "Central & Latin America",
                                  "Egypt": "Middle East / Africa",
                                  "Eritrea": "Middle East / Africa",
                                  "WesternSahara": "Middle East / Africa",
                                  "Spain": "Europe Developed",
                                  "Estonia": "Europe Emerging",
                                  "Ethiopia": "Middle East / Africa",
                                  "Finland": "Europe Developed",
                                  "Fiji": "Asia Emerging",
                                  "FalklandIslands": "Central & Latin America",
                                  "France": "Europe Developed",
                                  "FaroeIslands": "Europe Developed",
                                  "Micronesia": "Asia Emerging",
                                  "Gabon": "Middle East / Africa",
                                  "UnitedKingdom": "United Kingdom",
                                  "Georgia": "Asia Emerging",
                                  "Guernsey": "United Kingdom",
                                  "Ghana": "Middle East / Africa",
                                  "Gibraltar": "Europe Developed",
                                  "Guinea": "Middle East / Africa",
                                  "Guadeloupe": "Central & Latin America",
                                  "Gambia": "Middle East / Africa",
                                  "GuineaBissau": "Middle East / Africa",
                                  "EquatorialGuinea": "Middle East / Africa",
                                  "Greece": "Europe Developed",
                                  "Grenada": "Central & Latin America",
                                  "Greenland": "Europe Developed",
                                  "Guatemala": "Central & Latin America",
                                  "FrenchGuiana": "Central & Latin America",
                                  "Guam": "Asia Developed",
                                  "Guyana": "Central & Latin America",
                                  "HongKong": "Asia Developed",
                                  "HeardIslandAndMcDonaldIslands": "Asia Emerging",
                                  "Honduras": "Central & Latin America",
                                  "Croatia": "Europe Emerging",
                                  "Haiti": "Central & Latin America",
                                  "Hungary": "Europe Emerging",
                                  "Indonesia": "Asia Emerging",
                                  "IsleofMan": "United Kingdom",
                                  "India": "Asia Emerging",
                                  "Ireland": "Europe Developed",
                                  "Iran": "Middle East / Africa",
                                  "Iraq": "Middle East / Africa",
                                  "Iceland": "Europe Developed",
                                  "Israel": "Middle East / Africa",
                                  "Italy": "Europe Developed",
                                  "Jamaica": "Central & Latin America",
                                  "Jersey": "United Kingdom",
                                  "Jordan": "Middle East / Africa",
                                  "Japan": "Japan",
                                  "Kazakhstan": "Asia Emerging",
                                  "Kenya": "Middle East / Africa",
                                  "Kyrgyzstan": "Asia Emerging",
                                  "Cambodia": "Asia Emerging",
                                  "Kiribati": "Asia Emerging",
                                  "StKittsAndNevis": "Central & Latin America",
                                  "SouthKorea": "Asia Developed",
                                  "Kuwait": "Middle East / Africa",
                                  "Laos": "Asia Emerging",
                                  "Lebanon": "Middle East / Africa",
                                  "Liberia": "Middle East / Africa",
                                  "Libya": "Middle East / Africa",
                                  "StLucia": "Central & Latin America",
                                  "Liechtenstein": "Europe Developed",
                                  "SriLanka": "Asia Emerging",
                                  "Lesotho": "Middle East / Africa",
                                  "Lithuania": "Europe Emerging",
                                  "Luxembourg": "Europe Developed",
                                  "Latvia": "Europe Emerging",
                                  "Macao": "Asia Developed",
                                  "Morocco": "Middle East / Africa",
                                  "Monaco": "Europe Developed",
                                  "Moldova": "Europe Emerging",
                                  "Madagascar": "Middle East / Africa",
                                  "Maldives": "Asia Emerging",
                                  "Mexico": "Central & Latin America",
                                  "MarshallIslands": "Asia Emerging",
                                  "Macedonia": "Europe Emerging",
                                  "Mali": "Middle East / Africa",
                                  "Malta": "Europe Developed",
                                  "Myanmar": "Asia Emerging",
                                  "Mongolia": "Asia Emerging",
                                  "NorthernMarianaIslands": "Asia Emerging",
                                  "Mozambique": "Middle East / Africa",
                                  "Mauritania": "Middle East / Africa",
                                  "Montserrat": "Central & Latin America",
                                  "Martinique": "Central & Latin America",
                                  "Mauritius": "Middle East / Africa",
                                  "Malawi": "Middle East / Africa",
                                  "Malaysia": "Asia Emerging",
                                  "Mayotte": "Middle East / Africa",
                                  "Namibia": "Middle East / Africa",
                                  "NewCaledonia": "Asia Developed",
                                  "Niger": "Middle East / Africa",
                                  "NorfolkIsland": "Asia Emerging",
                                  "Nigeria": "Middle East / Africa",
                                  "Nicaragua": "Central & Latin America",
                                  "Niue": "Asia Emerging",
                                  "Netherlands": "Europe Developed",
                                  "Norway": "Europe Developed",
                                  "Nepal": "Asia Emerging",
                                  "Nauru": "Asia Emerging",
                                  "NewZealand": "Australasia",
                                  "Oman": "Middle East / Africa",
                                  "Pakistan": "Asia Emerging",
                                  "Panama": "Central & Latin America",
                                  "Pitcairn": "Asia Emerging",
                                  "Peru": "Central & Latin America",
                                  "Philippines": "Asia Emerging",
                                  "Palau": "Asia Emerging",
                                  "PapuaNewGuinea": "Asia Emerging",
                                  "Poland": "Europe Emerging",
                                  "PuertoRico": "Central & Latin America",
                                  "NorthKorea": "Asia Emerging",
                                  "Portugal": "Europe Developed",
                                  "Paraguay": "Central & Latin America",
                                  "OccupiedPalestinianTerritory": "Middle East / Africa",
                                  "FrenchPolynesia": "Asia Developed",
                                  "Qatar": "Middle East / Africa",
                                  "Reunion": "Middle East / Africa",
                                  "Romania": "Europe Emerging",
                                  "Russia": "Europe Emerging",
                                  "Rwanda": "Middle East / Africa",
                                  "SaudiArabia": "Middle East / Africa",
                                  "Sudan": "Middle East / Africa",
                                  "Senegal": "Middle East / Africa",
                                  "Singapore": "Asia Developed",
                                  "StHelena": "Middle East / Africa",
                                  "SvalbardandJanMayen": "Europe Developed",
                                  "SolomonIslands": "Asia Emerging",
                                  "SierraLeone": "Middle East / Africa",
                                  "ElSalvador": "Central & Latin America",
                                  "SanMarino": "Europe Developed",
                                  "Somalia": "Middle East / Africa",
                                  "Serbia": "Europe Emerging",
                                  "SaoTomeAndPrincipe": "Middle East / Africa",
                                  "Suriname": "Central & Latin America",
                                  "Slovakia": "Europe Emerging",
                                  "Slovenia": "Europe Developed",
                                  "Sweden": "Europe Developed",
                                  "Swaziland": "Middle East / Africa",
                                  "Seychelles": "Middle East / Africa",
                                  "SyrianArabRepublic": "Middle East / Africa",
                                  "TurksAndCaicosIslands": "Central & Latin America",
                                  "Chad": "Middle East / Africa",
                                  "Togo": "Middle East / Africa",
                                  "Thailand": "Asia Emerging",
                                  "Tajikistan": "Asia Emerging",
                                  "Tokelau": "Asia Emerging",
                                  "Turkmenistan": "Asia Emerging",
                                  "TimorLeste": "Asia Emerging",
                                  "Tonga": "Asia Emerging",
                                  "TrinidadAndTobago": "Central & Latin America",
                                  "Tunisia": "Middle East / Africa",
                                  "Turkey": "Europe Emerging",
                                  "Tuvalu": "Asia Emerging",
                                  "Taiwan": "Asia Developed",
                                  "Tanzania": "Middle East / Africa",
                                  "Uganda": "Middle East / Africa",
                                  "Ukraine": "Europe Emerging",
                                  "Uruguay": "Central & Latin America",
                                  "UnitedStates": "North America",
                                  "Uzbekistan": "Asia Emerging",
                                  "Vatican": "Europe Developed",
                                  "StVincentAndTheGrenadines": "Central & Latin America",
                                  "Venezuela": "Central & Latin America",
                                  "BritishVirginIslands": "Central & Latin America",
                                  "USVirginIslands": "Central & Latin America",
                                  "Vietnam": "Asia Emerging",
                                  "Vanuatu": "Asia Emerging",
                                  "WallisAndFutunaIslands": "Asia Emerging",
                                  "Samoa": "Asia Emerging",
                                  "Yemen": "Middle East / Africa",
                                  "SouthAfrica": "Middle East / Africa",
                                  "Zambia": "Middle East / Africa",
                                  "Zimbabwe": "Middle East / Africa",
                                  "BonaireSintEustatiusAndSaba": "Central & Latin America",
                                  "Curacao": "Central & Latin America",
                                  "Supranational": "Supranational",                       
                                },                        
                         },  
              'Country': { 'url': 'https://www.emea-api.morningstar.com/sal/sal-service/fund/portfolio/regionalSectorIncludeCountries/{secid}/data',
                          'component': 'sal-components-mip-country-exposure',
                          'jsonpath': '$.fundPortfolio.countries[*]',
                          'category': 'name',
                          'percent': 'percent',
                          'url2': 'https://www.emea-api.morningstar.com/sal/sal-service/stock/companyProfile/{secid}',
                          'component2': '',
                          'jsonpath2': '$..contact.country',
                          },
        }



class Isin2secid:
    mapping = dict()
    
    @staticmethod
    def load_cache():
        if os.path.exists("isin2secid.json"):
            with open("isin2secid.json", "r") as f:
                try:
                    Isin2secid.mapping = json.load(f)
                except json.JSONDecodeError:
                    print("Invalid json file")
                    
        
    @staticmethod
    def save_cache():
        with open("isin2secid.json", "w") as f:
            json.dump(Isin2secid.mapping, f, indent=1, sort_keys=True)
            
    @staticmethod
    def get_secid(isin):
        cached_secid = Isin2secid.mapping.get(isin,"-")
        if cached_secid == "-" or len(cached_secid.split("|"))<3:
            url = f"https://global.morningstar.com/api/v1/{DOMAIN}/search/securities"
            if isin is None: isin=""
            params = {
                   "query": '((isin ~= "' + isin +'"))'
                 }
            headers = {
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate, br',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
                }
            resp = requests.get(url, headers=headers, params=params)		
            if resp.status_code == 200:
                response = resp.json()
                jsonpath = parse("$..securityID")
                index = 0             
                if jsonpath.find(response):
                  if len(jsonpath.find(response)) > 2: index=2
                  elif len(jsonpath.find(response)) > 1: index=1  
                  secid = jsonpath.find(response)[index].value              
                else:
                  secid =""  
                jsonpath = parse("$..universe")
                if jsonpath.find(response):
                  if jsonpath.find(response)[0].value == "EQ": secid_type = "stock"
                  else: secid_type = "fund"
                else:
                  secid_type = "unknown" 
                secid_type_domain = secid + "|" + secid_type + "|" + DOMAIN
                Isin2secid.mapping[isin] = secid_type_domain
            else:
                secid_type_domain = '||'
        else:
            secid_type_domain = Isin2secid.mapping[isin]
        return secid_type_domain.split("|")


class Security:
 
    def __init__ (self, **kwargs):
        self.__dict__.update(kwargs)
        self.holdings = []

    def load_holdings (self):
        if len(self.holdings) == 0:
            self.holdings = SecurityHoldingReport()
            self.holdings.load(isin = self.ISIN, secid = self.secid, name = self.name, isRetired = self.isRetired)
        return self.holdings


class SecurityHolding(NamedTuple):
    name: str
    isin: str
    country: str
    industry: str
    currency: str
    percentage: float


class Holding(NamedTuple):
    name: str
    percentage: float


class SecurityHoldingReport:
    def __init__ (self):
        self.secid=''
        pass


    
    def get_bearer_token(self, secid, domain):
        # the secid can change for retrieval purposes
        # find the retrieval secid
        global BEARER_TOKEN
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'}
        url = f'https://www.morningstar.{domain}/{domain}/funds/snapshot/snapshot.aspx?id={secid}'
        response = requests.get(url, headers=headers)
        secid_regexp = r"var FC =  '(.*)';"
        matches = re.findall(secid_regexp, response.text)
        if len(matches)>0:
            secid_to_search = matches[0]
        else:
            secid_to_search = secid
            
        # get one bearer token for all requests
        if BEARER_TOKEN == "":
          url = f'https://www.morningstar.{domain}/Common/funds/snapshot/PortfolioSAL.aspx'
          response = requests.get(url, headers=headers)
          token_regex = r"const maasToken \=\s\"(.+)\""
          resultstringtoken = re.findall(token_regex, response.text)[0]
          BEARER_TOKEN = resultstringtoken
        else:
          resultstringtoken = BEARER_TOKEN
        return resultstringtoken, secid_to_search

    def calculate_grouping(self, categories, percentages, grouping_name, long_equity):
        for category_name, percentage in zip(categories, percentages):
            self.grouping[grouping_name][escape(category_name)] = self.grouping[grouping_name].get(escape(category_name),0) +  percentage  

        if grouping_name !='Asset-Type':
            self.grouping[grouping_name] = {k:v*long_equity for k, v in 
                                            self.grouping[grouping_name].items()}

   
        
    def load (self, isin, secid, name, isRetired):
        secid, secid_type, domain = Isin2secid.get_secid(isin)
        if secid == '':
            print(f"@ isin {isin} not found in Morningstar, skipping it...")
            print(f"  [{name}]")
            return
        elif isRetired=="true":
            print(f"@ isin {isin} is inactive, skipping it...")
            print(f"  [{name}]")         
            return 
        self.secid = secid
        bearer_token, secid = self.get_bearer_token(secid, domain)
        if secid_type=="stock":
             if STOCKS:
                 print(f"@ Retrieving data for {secid_type} {isin} ({secid}) ...")
             else:    
                 print(f"@ isin {isin} is a stock, skipping it...")
        else:
             print(f"@ Retrieving data for {secid_type} {isin} ({secid}) ...")
        print(f"  [{name}]")
        headers_short = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            }
        headers = headers_short.copy()
        headers['Authorization'] = f'Bearer {bearer_token}'
        
        params = {
            'languageId': 'en-EU',
            'locale': 'en',
            'benchmarkId': 'undefined',
            'version': '4.65.0',
        }
    
        
        self.grouping=dict()
        for taxonomy in taxonomies:
            self.grouping[taxonomy] = defaultdict(float)
       
        non_categories = ['avgMarketCap', 'portfolioDate', 'name', 'masterPortfolioId' ]
        
        if secid_type!="stock":	              # secid_type=="fund"
          for grouping_name, taxonomy in taxonomies.items():
            url = taxonomy['url']
            # use corresponding id (secid or isin)
            url = url.replace("{secid}", secid)
            for urlparam in ['component']:			
              if taxonomy.get(urlparam): params[urlparam] = taxonomy[urlparam]
            resp = requests.get(url, params=params, headers=headers)
            if resp.status_code == 401:
                print(f"  Warning: No information on {grouping_name} for {secid}")
                continue
            try:
                response = resp.json()
                jsonpath = parse(taxonomy['jsonpath'])
                percent_field = taxonomy['percent']
                # single match of the jsonpath from sal-service means the path contains the categories
                if "sal-service" in url and len(jsonpath.find(response))==1:
                    value = jsonpath.find(response)[0].value 
                    keys = [key for key in value if key not in non_categories]
                    
                    if percent_field != "":
                        if value[keys[0]][percent_field] is not None:
                            percentages = [float(value[key][percent_field]) for key in keys]
                        else:
                            percentages =[]
                    else:
                        if value[keys[0]] is not None:
                            percentages = [float(value[key]) for key in keys]
                        else:
                            percentages = []
                        
                    if grouping_name == 'Asset-Type':
                        try:
                            long_equity = (float(value.get('assetAllocEquity',{}).get('longAllocation',0)) +
                                      float(value.get('AssetAllocNonUSEquity',{}).get('longAllocation',0)) +           
                                      float(value.get('AssetAllocUSEquity',{}).get('longAllocation',0)))/100
                        except TypeError:
                            print(f"  Warning: No information on {grouping_name} for {secid}")
                else:
                    # every match is a category
                    value = jsonpath.find(response)
                    keys = [key.value[taxonomy['category']] for key in value]
                    if len(value) == 0 or value[0].value.get(taxonomy['percent'],"") =="":
                        print(f"  Warning: percentages not found for {grouping_name} for {secid}")
                    else:
                        percentages = [float(key.value[taxonomy['percent']]) for key in value]

                # Map names if there is a map
                if len(taxonomy.get('map',{})) != 0:
                    categories = [taxonomy['map'][key] for key in keys if key in taxonomy['map'].keys()]
                    unmapped = [key for key in keys if key not in taxonomy['map'].keys()]
                    if  unmapped:
                        print(f"  Warning: Categories not mapped: {unmapped} for {secid}")
                else:
                    # capitalize first letter if not mapping
                    categories = [key[0].upper() + key[1:] for key in keys]
                
                if percentages:
                    self.calculate_grouping (categories, percentages, grouping_name, long_equity)
                
            except Exception:
                print(f"  Warning: Problem with {grouping_name} for secid {secid} in PortfolioSAL...")
                
                
        else:		# secid_type=="stock"
          
          if STOCKS:
              
           for grouping_name, taxonomy in taxonomies.items():
            url = taxonomy['url2']
            # use corresponding id (secid or isin)
            url = url.replace("{secid}", secid)			
            if taxonomy.get('component2'): params['component'] = taxonomy['component2']
            resp = requests.get(url, params=params, headers=headers)
            if resp.status_code != 200:                
                print(f"  Warning: No information on {grouping_name} for {secid}")
                continue
            response = resp.json()
            jsonpath = parse(taxonomy['jsonpath2'])
            value = jsonpath.find(response)[0].value
            if grouping_name == 'Asset-Type':
              print ("  Name:", value)
              value = "Stocks"
            if grouping_name in ['Country', 'Region']:
              value = re.sub(r'\([^)]*\)', '', value)
              value = value.replace(' ', '')
              value = value.replace('ofAmerica', '')
              value = value.replace('ofGreatBritainandNorthernIreland', '')
              value = value.replace('Korea','SouthKorea')
              value = value.replace('Czechia','CzechRepublic')
              value = value.replace('RussianFederation','Russia')
            if value is not None:
             if len(taxonomy.get('map2',{})) != 0:
               if value in taxonomy['map2'].keys():
                    value = taxonomy['map2'][value]
               else:
                    print (" ",grouping_name,":", value, "not mapped !!! Please report")
                    value = "" 
             if value != "":
              self.grouping[grouping_name][escape(value)] = 100.0
              continue              
            print(f"  Warning: No information on {grouping_name} for {secid}")                   
      
        
    def group_by_key (self,key):
        return self.grouping[key]


class PortfolioPerformanceCategory(NamedTuple):
    name: str
    color: str
    uuid: str    
    

class PortfolioPerformanceFile:

    def __init__ (self, filepath):
        self.filepath = filepath
        self.pp_tree = ET.parse(filepath)
        self.pp = self.pp_tree.getroot()
        self.securities = None
        if self.pp.get('id') is not None:
          print ("ABORTED: XML FORMAT WITH IDs IS NOT SUPPORTED")
          print ("Please save input file in original XML format of PP.")
          print ("Please don't use XML format with \"id\" attributes.")
          exit()

    def get_security(self, security_xpath):
        """return a security object """
        if (matching := self.pp.findall(security_xpath)):
            security = matching[0]
        else:
            return None 
        if security is not None:
            isin = security.find('isin') 
            if isin is not None:
                isin = isin.text
                name = security.find('name')
                if name is not None:
                    name = name.text
                secid = security.find('secid')
                if secid is not None:
                    secid = secid.text
                note = security.find('note')
                isRetired = security.find('isRetired').text
                security2 = None
                if note is not None:
                    note = note.text
                    if note is not None:
                       token_pattern = r'#PPC:\[ISIN2=([A-Z0-9]{12})'
                       match = re.search(token_pattern,note)
                       if match:
                           ISIN2 = match.group(1)
                           security2 = self.get_security2(ISIN2, isin, isRetired)
                return Security(
                    name = name,
                    ISIN = isin,
                    secid = secid,
                    UUID = security.find('uuid').text,
                    isRetired = isRetired,
                    note = note,
                    security2 = security2
                )
            else:
                name = security.find('name').text
                print(f"  Warning: security '{name}' does not have isin, skipping it...")
        return None
      
    def get_security2(self, isin2, isin, isRetired):				  
        """return an alternative security object """
        return Security(
                    name = "Alternative ISIN for " + isin,
                    ISIN = isin2,
                    secid = "",
                    UUID = "00000000-0000-0000-0000-000000000000",
                    isRetired = isRetired,
                    note = "alternative security for fetching classification"
                ) 

    def get_security_xpath_by_uuid (self, uuid):
        for idx, security in enumerate(self.pp.findall(".//securities/security")):
            sec_uuid =  security.find('uuid').text
            if sec_uuid == uuid and idx == 0:
                return "../../../../../../../../securities/security"
            if sec_uuid == uuid:
                return f"../../../../../../../../securities/security[{idx + 1}]"
        print (f"Error: No xpath found for UUID '{uuid}'") 

    def add_taxonomy (self, kind):
          securities = self.get_securities()
          color = cycle(COLORS)
        
          # Does taxonomy of type kind exist in xml file? If not, create an entry.
          if self.pp.find("taxonomies/taxonomy[name='%s']" % kind) is None:
          
            print (f"### No entry for '{kind}' found: Creating it from scratch")
            new_taxonomy_tpl =  """
    <taxonomy>
      <id>{{ outer_uuid }}</id>
      <name>{{ kind }}</name>
      <root>
        <id>{{ inner_uuid }}</id>
        <name>{{ kind }}</name>
        <color>#89afee</color>
        <children/>
        <assignments/>
        <weight>10000</weight>
         <rank>0</rank>
       </root>
    </taxonomy>
            """
            
            new_taxonomy_tpl = Environment(loader=BaseLoader).from_string(new_taxonomy_tpl)
            new_taxonomy_xml = new_taxonomy_tpl.render(
                                      outer_uuid = str(uuid.uuid4()),
                                      inner_uuid = str(uuid.uuid4()),
                                      kind = kind,                            
                                   )                                  
            self.pp.find('.//taxonomies').append(ET.fromstring(new_taxonomy_xml))
           
                                
          else:
            print (f"### Entry for '{kind}' found: updating existing data")
            
            # Substitute "'" with "....."  in all names of classifications of all taxonomies of type kind            
            for child in self.pp.findall(".//taxonomies/taxonomy[name='%s']/root/children/classification" % kind):
              category_name = child.find('name')
              if category_name is not None and category_name.text is not None:
                  category_name.text = category_name.text.replace("'", ".....")
                           
          double_entry = False
          
          for taxonomy in self.pp.findall("taxonomies/taxonomy[name='%s']" % kind):
             if double_entry == True:
                 print (f"### Another entry for '{kind}' found: updating existing data with same input")
             double_entry = True
             rank = 0       
                                                      
             # Run through all securities for which data was fetched (i.e. all securities that are not plain stocks)
             for security in securities:
                  security_xpath = self.get_security_xpath_by_uuid(security.UUID)
                  security_assignments = security.holdings.grouping[kind]
                       
                  # Set weight = 0 in all existing assignments of this specific security
                  # for all(!) categories, if anything was retrieved for this taxonomy (aka kind)
                  # (last step will remove all assignement with weight == 0)    
                  
                  if security.holdings.grouping[kind] == {}:
                     if security.security2 is not None:
                       if security.security2.holdings.grouping[kind] == {}:
                         grouping_exists = False
                         print (f"  Warning: No input for '{kind}' for '{security.name}' (also not in alternative ISIN): keeping existing data")
                       else:     
                         grouping_exists = True
                         security_assignments = security.security2.holdings.grouping[kind]
                         print (f"  Info: Using alternative ISIN {security.security2.ISIN} for '{kind}' for '{security.name}'")
                     else:
                       grouping_exists = False
                       print (f"  Warning: No input for '{kind}' for '{security.name}': keeping existing data")
                  else:
                     grouping_exists = True                       
                  
                  if grouping_exists:
                      for existing_assignment in taxonomy.findall("./root/children/classification/assignments/assignment"):                  
                           investment_vehicle = existing_assignment.find('investmentVehicle')
                           if investment_vehicle is not None and investment_vehicle.attrib.get('reference') == security_xpath:
                               weight_element = existing_assignment.find('weight')
                               if weight_element is not None:
                                   weight_element.text = "0"
                                   rank += 1
                                   next(color)            
                                    
                  # 1. Determine scaling factor for rounding issues when sum of percentages is in the range 100,01% to 100,05%
                  # 2a. Check for each category for which the security has a contribution, if there is already an entry in the file. If not, create the category.
                  # 2b. Also check, if there is already an assignment for the security in the category. If not, create one with weight = 0.
                  # 3.  Set the new weight values.                                    

                  scaling = 1
                  w_sum_initial = 0  
                  
                  while True:
                       w_sum = 0
                       for category, weight in security_assignments.items():
                              weight = round(weight*100*scaling)
                              if weight > 10000: weight = 10000    # weight value above 100% reduced to 100%
                              if weight > 0: w_sum += weight       # skip negative values
                       if w_sum_initial == 0: w_sum_initial = w_sum     # remember initial value without scaling
                       if w_sum > 10000 and w_sum < 10006:
                              scaling = scaling * 0.999999         # try again with new scaling
                       else: break                 
                                                                  
                  w_sum = 0                 
                  for category, weight in security_assignments.items():
                        
                        weight = round(weight*100*scaling)   
                        category = category.replace("'", ".....")
                        category = clean_text(category)                       
                        
                        if weight != 0:
                             for children in taxonomy.findall(".//root/children"):                                                
                                
                                # Does category already exist in xml file for this taxonomy (aka kind)?
                                if any(clean_text(child.find('name').text) == category for child in children if child.find('name') is not None):
                                   category_found = True
                                else:
                                   category_found = False
                                          
                                if category_found == False:                        

                                       new_child_tpl =  """                    
          <classification>
            <id>{{ uuid }}</id>
            <name>{{ name }}</name>
            <color>{{ color }}</color>
            <parent reference="../../.."/>
            <children/>
            <assignments/>
            <weight>0</weight>
            <rank>1</rank>
          </classification>
                                       """
                                       
                                       new_child_tpl = Environment(loader=BaseLoader).from_string(new_child_tpl)
                                       new_child_xml = new_child_tpl.render(
                                                  uuid = str(uuid.uuid4()),
                                                  name = category.replace("&","&amp;"),
                                                  color = next(color)                              
                                                )
                                       children.append(ET.fromstring(new_child_xml))    
                                                                                                                  
                                       print ("  Info: Entry for '%s' in '%s' created" % (category.replace(".....","'"),kind))          
                                                                           
                             # Does investment vehicle already exist in xml file for this security in this category in this taxonomy (aka kind)?
                             if any(existing_vehicle.attrib['reference'] == security_xpath for existing_vehicle in taxonomy.findall(".//root/children/classification[name='%s']/assignments/assignment/investmentVehicle" % category) if existing_vehicle.attrib['reference'] is not None):
                                   vehicle_found = True
                             else:
                                   vehicle_found = False                                                        
                             
                             if vehicle_found == False:
                             
                                       new_ass_tpl =  """
            <assignment>
                <investmentVehicle class="security" reference="{{ security_xpath }}"/>
                <weight>0</weight>
                <rank>{{ rank }}</rank>
            </assignment>                             
                                       """  
                                                                                                                       
                                       new_ass_tpl = Environment(loader=BaseLoader).from_string(new_ass_tpl)
                                       
                                       rank += 1
                                       new_ass_xml = new_ass_tpl.render(
                                                  security_xpath = security_xpath,
                                                  rank = str(rank)                            
                                                )
                                        
                                       new_ass = ET.fromstring(new_ass_xml)
                                       
                                       for assignments_element in taxonomy.findall(".//root/children/classification[name='%s']/assignments" % category):
                                            assignments_element.append(new_ass)
                                            print ("  Info: Entry for '%s' in '%s' created" % (security.name, category.replace(".....","'")))                            
        
                             for existing_assignment in taxonomy.findall(".//root/children/classification[name='%s']/assignments/assignment" % category):
                                  investment_vehicle = existing_assignment.find('investmentVehicle')
                                  if investment_vehicle is not None and investment_vehicle.attrib.get('reference') == security_xpath:
                                      weight_element = existing_assignment.find('weight')
                                      if weight_element is not None:
                                          if weight < 0:
                                               print (f"  !!! Warning: Skipping negative weight for '{security.name}' for '{category}' in '{kind}' ({weight/100}%) !!!") 
                                          else:
                                             if weight > 10000: 
                                                  print (f"  !!! Warning: Weight value > 100% reduced to 100% for '{security.name}' for '{category}' in '{kind}' (was: {weight/100}%) !!!")
                                                  weight = 10000                                         
                                             weight_element.text = str(weight)
                                             w_sum += weight
                                            
  
                  if scaling != 1:
                        print (f"  Warning: Sum adjusted to {(w_sum/100):.2f}% for '{security.name}' in '{kind}' (was: {w_sum_initial/100}%)") 
                  if w_sum > 10000:
                        print (f"  !!! Warning: Sum is higher than 100% for '{security.name}' in '{kind}' (kept: {w_sum/100}%) !!!")
              
            
          # Substitute "....." with "'" in all names of classifications of all taxonomies of type kind             
          for child in self.pp.findall(".//taxonomies/taxonomy[name='%s']/root/children/classification" % kind):
            category_name = child.find('name')
            if category_name is not None and category_name.text is not None:
                category_name.text = category_name.text.replace(".....", "'")
             
          # delete all assignments for this taxonomy with weight == 0:
          deletions = []
             
          for assignment_parent in self.pp.findall(".//taxonomies/taxonomy[name='%s']/root/children/classification/assignments" % kind):
            for assignment in assignment_parent:
              if assignment.find('weight').text == "0":
                  deletions.append((assignment_parent,assignment))
                    
          for parent,assignment_for_deletion in deletions:
             parent.remove(assignment_for_deletion)   

    def write_xml(self, output_file):
        with open(output_file, 'wb') as f:
            self.pp_tree.write(f, encoding="utf-8")


    def dump_xml(self):
        print (ET.tostring(self.pp, encoding="unicode"))

    def dump_csv(self):
        csv_file = open ("pp_data_fetched.csv", 'w')
        csv_file.write ("ISIN,Taxonomy,Classification,Percentage,Name\n")
        for security in sorted(self.securities, key=lambda security: security.name.upper()):
          for taxonomy in sorted(taxonomies):     
             for key, value in sorted(security.holdings.grouping[taxonomy].items(), reverse=False):   
                   csv_file.write (f"{security.ISIN},{clean_text(taxonomy)},{clean_text(key)},{value/100},{clean_text(security.name)}\n")
             if security.security2 is not None: 
               for key, value in sorted(security.security2.holdings.grouping[taxonomy].items(), reverse=False):   
                   csv_file.write (f"{security.security2.ISIN},{clean_text(taxonomy)},{clean_text(key)},{value/100},{clean_text(security.security2.name)}\n")

    def get_securities(self):
        if self.securities is None:
            self.securities = []
            sec_xpaths = []
            
            # create list of xpaths for all securities in the file
            for count, sec in enumerate(self.pp.findall(".//securities/security")):
               sec_xpaths.append('.//securities/security['+ str(count+1) + ']')     
    
            for sec_xpath in list(set(sec_xpaths)):
                security = self.get_security(sec_xpath)
                if security is not None:
                    security_h = security.load_holdings()
                    if security_h.secid !='':
                        if security.security2 is not None:
                           security.security2.load_holdings()
                        self.securities.append(security)
        return self.securities

def clean_text(text):
    return BeautifulSoup(text, "html.parser").text

def print_class (grouped_holding):
    for key, value in sorted(grouped_holding.items(), reverse=True):
        print (key, "\t\t{:.2f}%".format(value))
    print ("-"*30)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
    #usage="%(prog) <input_file> [<output_file>] [-d domain] [-stocks]",
    description='\r\n'.join(["reads a portfolio performance xml file and auto-classifies",
                 "the securities in it by asset-type, stock-style, sector, holdings, region and country weights",
                 "For each security, you need to have an ISIN"])
    )
    
    
    parser.add_argument('-d', default='de',  dest='domain', type=str,
                        help='Morningstar domain from which to retrieve the security token and the secid (default: de)')
    
    parser.add_argument('input_file', metavar='input_file', type=str,
                   help='path to unencrypted pp.xml file')
    
    parser.add_argument('output_file', metavar='output_file', type=str, nargs='?',
                   help='path to auto-classified output file', default='pp_classified.xml')
                   
    parser.add_argument('-stocks', action='store_true', dest='retrieve_stocks',
                   help='activates retrieval of data on individual stocks')
                   

    args = parser.parse_args()
    
    if "input_file" not in args:
        parser.print_help()
    else:
        DOMAIN = args.domain
        STOCKS = args.retrieve_stocks
        BEARER_TOKEN = ""
        # Isin2secid.load_cache()
        pp_file = PortfolioPerformanceFile(args.input_file)
        for taxonomy in taxonomies:
            pp_file.add_taxonomy(taxonomy)
        # Isin2secid.save_cache()
        pp_file.write_xml(args.output_file)
        pp_file.dump_csv()
