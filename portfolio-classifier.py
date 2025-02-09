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


requests_cache.install_cache(expire_after=60) #cache downloaded files for one minute
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


taxonomies = {'Asset-Type': {'url': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                             'idtype' : 'ISIN',  
                             'viewid' : 'ITsnapshot',
                             'jsonpath': '$.[0].Portfolios[0].AssetAllocations[?(@.Type == "MorningStarDefault" & @.SalePosition == "N")].BreakdownValues.[*]',
                             'category': 'Type',
                             'percent': 'Value',
                             'table-xr': 0,
                             'column-xr': 2,
                             'table-stock-xr': {0},
                             'column-stock-xr': 0,
                             'map':{"1" : "Stocks", 
                                    "3" : "Bonds", 
                                    "7" : "Cash",
                                    "2" : "Other",
                                    "4" : "Other",
                                    "5" : "Other",
                                    "6" : "Other",
                                    "8" : "Other",
                                    "99" : "Not classified",
                                    }
                             },
              'Stock-style': {'url': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                            'idtype' : 'ISIN',  
                            'viewid' : 'ITsnapshot',
                            'jsonpath': '$.[0].Portfolios[0].StyleBoxBreakdown[?(@.SalePosition == "N")].BreakdownValues.[*]',
                            'category': 'Type',
                            'percent': 'Value',
                            'table-xr': 9,
                            'column-xr': 2,
                             'table-stock-xr': {17},
                             'column-stock-xr': 0,
                            'map':{ "1":"Large Value", 
                                    "2":"Large Blend",
                                    "3":"Large Growth",
                                    "4":"Mid-Cap Value", 
                                    "5":"Mid-Cap Blend",
                                    "6":"Mid-Cap Growth",
                                    "7":"Small Value",
                                    "8":"Small Blend",
                                    "9":"Small Growth",
                                    },
                            'map3':{"Large-Blend":"Large Blend", 
                                    "Large-Growth":"Large Growth",
                                    "Large-Value":"Large Value",
                                    "Mid-Blend":"Mid-Cap Blend", 
                                    "Mid-Growth":"Mid-Cap Growth",
                                    "Mid-Value":"Mid-Cap Value",
                                    "Small-Blend":"Small Blend",
                                    "Small-Growth":"Small Growth",
                                    "Small-Value":"Small Value",
                                    "Not Classified":"Not Classified",
                                    }   
                            },                            

              'Sector': {'url': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                         'idtype' : 'ISIN',  
                         'viewid' : 'ITsnapshot',
                         'jsonpath': '$.[0].Portfolios[0].GlobalStockSectorBreakdown[?(@.SalePosition == "N")].BreakdownValues.[*]',
                         'category': 'Type',
                         'percent': 'Value',
                         'table-xr': 1,
                         'column-xr': 0,
                         'table-stock-xr': {5,6,7},
                         'column-stock-xr': 0,
                         'map':{"101":"Basic Materials",
                                "102":"Consumer Cyclical",
                                "103":"Financial Services",
                                "104":"Real Estate",
                                "205":"Consumer Defensive",
                                "206":"Healthcare",
                                "207":"Utilities",
                                "308":"Communication Services",
                                "309":"Energy",
                                "310":"Industrials",
                                "311":"Technology",
                                }
                         },   
              'Region': { 'url': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                         'idtype' : 'ISIN',  
                         'viewid' : 'ITsnapshot',
                         'jsonpath': '$.[0].Portfolios[0].RegionalExposure[?(@.SalePosition == "N")].BreakdownValues.[*]',
                         'category': 'Type',
                         'percent': 'Value',
                         'table-xr': 2,
                         'column-xr': 0,
                         'table-stock-xr': {1,2,3},
                         'column-stock-xr': 0,
                         'map':{"1":"North America", 	# United States
                                "2":"North America", 	# Canada
                                "3":"Central & Latin America",  # Latin America
                                "4":"United Kingdom",
                                "5":"Europe Developed", # Eurozone
                                "6":"Europe Developed", # Europe - ex Euro
                                "7":"Europe Emerging",
                                "8":"Middle East / Africa", # Africa
                                "9":"Middle East / Africa", # Middle East
                                "10":"Japan",
                                "11":"Australasia",
                                "12":"Asia Developed",                              
                                "13":"Asia Emerging",
                                # "14", "15", "16" in non_categories
                                },
                         'map2':{"United States":"North America", 
                                 "Canada":"North America", 
                                "Western Europe - Euro":"Europe Developed",
                                "Western Europe - Non Euro":"Europe Developed",
                                "Emerging 4 Tigers":"Asia Developed",
                                "Emerging Asia - Ex 4 Tigers":"Asia Emerging", 
                                "Australasia":"Australasia",
                                "Emerging Europe":"Europe Emerging",
                                "Japan":"Japan",
                                "Central & Latin America":"Central & Latin America",
                                "United Kingdom":"United Kingdom",
                                "Middle East / Africa":"Middle East / Africa",
                                "Africa":"Middle East / Africa",
                                "Middle East":"Middle East / Africa",
                                "Not Classified": "Not Classified",
                                "North America":"North America",
                                "Europe Developed":"Europe Developed",
                                "Asia Developed":"Asia Developed",
                                "Europe Emerging":"Europe Emerging"
                                },
                         'map3':{"United States":"North America", 
                                 "Canada":"North America", 
                                "Western Europe - Euro":"Europe Developed",
                                "Western Europe - Non Euro":"Europe Developed",
                                "Emerging 4 Tigers":"Asia Developed",
                                "Emerging Asia - Ex 4 Tigers":"Asia Emerging", 
                                "Australasia":"Australasia",
                                "Emerging Europe":"Europe Emerging",
                                "Japan":"Japan",
                                "Central & Latin America":"Central & Latin America",
                                "United Kingdom":"United Kingdom",
                                "Middle East / Africa":"Middle East / Africa",
                                "Africa":"Middle East / Africa",
                                "Middle East":"Middle East / Africa",
                                "Not Classified": "Not Classified",
                                "North America":"North America",
                                "Europe Developed":"Europe Developed",
                                "Asia Developed":"Asia Developed",
                                "Europe Emerging":"Europe Emerging"
                                }                         
                         },  
              'Country': { 'url': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                          'idtype' : 'ISIN',
                          'viewid' : 'ITsnapshot',
                          'jsonpath': '$.[0].Portfolios[0].CountryExposure[?(@.Type == "Equity" & @.SalePosition == "N")].BreakdownValues.[*]',
                          'category': 'Type',
                          'percent': 'Value',
                          'table-xr': -1,
                          'column-xr': -1,
                          'table-stock-xr': {14},
                          'column-stock-xr': -1,
                          'map':{"ABW" : "Aruba",
                                 "AFG" : "Afghanistan",
                                 "AGO" : "Angola",
                                 "AIA" : "Anguilla",
                                 "ALA" : "AlandIslands",
                                 "ALB" : "Albania",
                                 "AND" : "Andorra",
                                 "ARE" : "UnitedArabEmirates",
                                 "ARG" : "Argentina",
                                 "ARM" : "Armenia",
                                 "ASM" : "AmericanSamoa",
                                 "ATA" : "Antarctica",
                                 "ATF" : "FrenchSouthernTerritories",
                                 "ATG" : "AntiguaAndBarbuda",
                                 "AUS" : "Australia",
                                 "AUT" : "Austria",
                                 "AZE" : "Azerbaijan",
                                 "BDI" : "Burundi",
                                 "BEL" : "Belgium",
                                 "BEN" : "Benin",
                                 "BFA" : "BurkinaFaso",
                                 "BGD" : "Bangladesh",
                                 "BGR" : "Bulgaria",
                                 "BHR" : "Bahrain",
                                 "BHS" : "Bahamas",
                                 "BIH" : "BosniaAndHerzegovina",
                                 "BLR" : "Belarus",
                                 "BLZ" : "Belize",
                                 "BMU" : "Bermuda",
                                 "BOL" : "Bolivia",
                                 "BRA" : "Brazil",
                                 "BRB" : "Barbados",
                                 "BRN" : "BruneiDarussalam",
                                 "BTN" : "Bhutan",
                                 "BVT" : "BouvetIsland",
                                 "BWA" : "Botswana",
                                 "CAF" : "CentralAfricanRepublic",
                                 "CAN" : "Canada",
                                 "CCK" : "CocosKeelingIslands",
                                 "CHE" : "Switzerland",
                                 "CHI" : "ChannelIslands",
                                 "CHL" : "Chile",
                                 "CHN" : "China",
                                 "CIV" : "CoteDIvoire",
                                 "CMR" : "Cameroon",
                                 "COD" : "CongoDemocraticRepublic",
                                 "COG" : "Congo",
                                 "COK" : "CookIslands",
                                 "COL" : "Colombia",
                                 "COM" : "Comoros",
                                 "CPV" : "CapeVerde",
                                 "CRI" : "CostaRica",
                                 "CUB" : "Cuba",
                                 "CXR" : "ChristmasIsland",
                                 "CYM" : "CaymanIslands",
                                 "CYP" : "Cyprus",
                                 "CZE" : "CzechRepublic",
                                 "DEU" : "Germany",
                                 "DJI" : "Djibouti",
                                 "DMA" : "Dominica",
                                 "DNK" : "Denmark",
                                 "DOM" : "DominicanRepublic",
                                 "DZA" : "Algeria",
                                 "ECU" : "Ecuador",
                                 "EGY" : "Egypt",
                                 "ERI" : "Eritrea",
                                 "ESH" : "WesternSahara",
                                 "ESP" : "Spain",
                                 "EST" : "Estonia",
                                 "ETH" : "Ethiopia",
                                 "FIN" : "Finland",
                                 "FJI" : "Fiji",
                                 "FLK" : "FalklandIslands",
                                 "FRA" : "France",
                                 "FRO" : "FaroeIslands",
                                 "FSM" : "Micronesia",
                                 "GAB" : "Gabon",
                                 "GBL" : "Global",
                                 "GBR" : "UnitedKingdom",
                                 "GEO" : "Georgia",
                                 "GGY" : "Guernsey",
                                 "GHA" : "Ghana",
                                 "GIB" : "Gibraltar",
                                 "GIN" : "Guinea",
                                 "GLP" : "Guadeloupe",
                                 "GMB" : "Gambia",
                                 "GNB" : "GuineaBissau",
                                 "GNQ" : "EquatorialGuinea",
                                 "GRC" : "Greece",
                                 "GRD" : "Grenada",
                                 "GRL" : "Greenland",
                                 "GTM" : "Guatemala",
                                 "GUF" : "FrenchGuiana",
                                 "GUM" : "Guam",
                                 "GUY" : "Guyana",
                                 "HKG" : "HongKong",
                                 "HMD" : "HeardIslandAndMcDonaldIslands",
                                 "HND" : "Honduras",
                                 "HRV" : "Croatia",
                                 "HTI" : "Haiti",
                                 "HUN" : "Hungary",
                                 "IDN" : "Indonesia",
                                 "IMN" : "IsleofMan",
                                 "IND" : "India",
                                 "IOT" : "BritishIndianOceanTerritory",
                                 "IRL" : "Ireland",
                                 "IRN" : "Iran",
                                 "IRQ" : "Iraq",
                                 "ISL" : "Iceland",
                                 "ISR" : "Israel",
                                 "ITA" : "Italy",
                                 "IXX" : "Ireland",
                                 "JAM" : "Jamaica",
                                 "JEY" : "Jersey",
                                 "JOR" : "Jordan",
                                 "JPN" : "Japan",
                                 "KAZ" : "Kazakhstan",
                                 "KEN" : "Kenya",
                                 "KGZ" : "Kyrgyzstan",
                                 "KHM" : "Cambodia",
                                 "KIR" : "Kiribati",
                                 "KNA" : "StKittsAndNevis",
                                 "KOR" : "SouthKorea",
                                 "KWT" : "Kuwait",
                                 "LAO" : "Laos",
                                 "LBN" : "Lebanon",
                                 "LBR" : "Liberia",
                                 "LBY" : "Libya",
                                 "LCA" : "StLucia",
                                 "LIE" : "Liechtenstein",
                                 "LKA" : "SriLanka",
                                 "LSO" : "Lesotho",
                                 "LTU" : "Lithuania",
                                 "LUX" : "Luxembourg",
                                 "LVA" : "Latvia",
                                 "MAC" : "Macao",
                                 "MAR" : "Morocco",
                                 "MCO" : "Monaco",
                                 "MDA" : "Moldova",
                                 "MDG" : "Madagascar",
                                 "MDV" : "Maldives",
                                 "MEX" : "Mexico",
                                 "MHL" : "MarshallIslands",
                                 "MKD" : "Macedonia",
                                 "MLI" : "Mali",
                                 "MLT" : "Malta",
                                 "MMR" : "Myanmar",
                                 "MNE" : "Montenegro",
                                 "MNG" : "Mongolia",
                                 "MNP" : "NorthernMarianaIslands",
                                 "MOZ" : "Mozambique",
                                 "MRT" : "Mauritania",
                                 "MSR" : "Montserrat",
                                 "MTQ" : "Martinique",
                                 "MUS" : "Mauritius",
                                 "MWI" : "Malawi",
                                 "MYS" : "Malaysia",
                                 "MYT" : "Mayotte",
                                 "NAM" : "Namibia",
                                 "NCL" : "NewCaledonia",
                                 "NER" : "Niger",
                                 "NFK" : "NorfolkIsland",
                                 "NGA" : "Nigeria",
                                 "NIC" : "Nicaragua",
                                 "NIU" : "Niue",
                                 "NLD" : "Netherlands",
                                 "NOR" : "Norway",
                                 "NPL" : "Nepal",
                                 "NRU" : "Nauru",
                                 "NZL" : "NewZealand",
                                 "OMN" : "Oman",
                                 "PAK" : "Pakistan",
                                 "PAN" : "Panama",
                                 "PCN" : "Pitcairn",
                                 "PER" : "Peru",
                                 "PHL" : "Philippines",
                                 "PLW" : "Palau",
                                 "PNG" : "PapuaNewGuinea",
                                 "POL" : "Poland",
                                 "PRI" : "PuertoRico",
                                 "PRK" : "NorthKorea",
                                 "PRT" : "Portugal",
                                 "PRY" : "Paraguay",
                                 "PSE" : "OccupiedPalestinianTerritory",
                                 "PYF" : "FrenchPolynesia",
                                 "QAT" : "Qatar",
                                 "REU" : "Reunion",
                                 "ROU" : "Romania",
                                 "RUS" : "Russia",
                                 "RWA" : "Rwanda",
                                 "SAU" : "SaudiArabia",
                                 "SDN" : "Sudan",
                                 "SEN" : "Senegal",
                                 "SGP" : "Singapore",
                                 "SGS" : "SouthGeorgiaAndTheSouthSandwichIslands",
                                 "SHN" : "StHelena",
                                 "SJM" : "SvalbardandJanMayen",
                                 "SLB" : "SolomonIslands",
                                 "SLE" : "SierraLeone",
                                 "SLV" : "ElSalvador",
                                 "SMR" : "SanMarino",
                                 "SOM" : "Somalia",
                                 "SPM" : "St.PierreAndMiquelon",
                                 "SRB" : "Serbia",
                                 "STP" : "SaoTomeAndPrincipe",
                                 "SUR" : "Suriname",
                                 "SVK" : "Slovakia",
                                 "SVN" : "Slovenia",
                                 "SWE" : "Sweden",
                                 "SWZ" : "Swaziland",
                                 "SYC" : "Seychelles",
                                 "SYR" : "SyrianArabRepublic",
                                 "TCA" : "TurksAndCaicosIslands",
                                 "TCD" : "Chad",
                                 "TGO" : "Togo",
                                 "THA" : "Thailand",
                                 "TJK" : "Tajikistan",
                                 "TKL" : "Tokelau",
                                 "TKM" : "Turkmenistan",
                                 "TLS" : "TimorLeste",
                                 "TON" : "Tonga",
                                 "TTO" : "TrinidadAndTobago",
                                 "TUN" : "Tunisia",
                                 "TUR" : "Turkey",
                                 "TUV" : "Tuvalu",
                                 "TWN" : "Taiwan",
                                 "TZA" : "Tanzania",
                                 "UGA" : "Uganda",
                                 "UKR" : "Ukraine",
                                 "UMI" : "USMinorOutlyingIslands",
                                 "URY" : "Uruguay",
                                 "USA" : "UnitedStates",
                                 "UZB" : "Uzbekistan",
                                 "VAT" : "Vatican",
                                 "VCT" : "StVincentAndTheGrenadines",
                                 "VEN" : "Venezuela",
                                 "VGB" : "BritishVirginIslands",
                                 "VIR" : "USVirginIslands",
                                 "VNM" : "Vietnam",
                                 "VUT" : "Vanuatu",
                                 "WBG" : "WestBankofGaza",
                                 "WLF" : "WallisAndFutunaIslands",
                                 "WSM" : "Samoa",
                                 "YEM" : "Yemen",
                                 "ZAF" : "SouthAfrica",
                                 "ZMB" : "Zambia",
                                 "ZWE" : "Zimbabwe",
                                 "BES" : "BonaireSintEustatiusAndSaba",
                                 "CUW" : "Curacao",
                                 "SXM" : "SintMaarten",
                                 "XSN" : "Supranational",
                                 "SSD" : "SouthSudan",

                               },
                          'map2':{"United States":"UnitedStates", 
                                 "Canada":"Canada", 
                                 "Western Europe - Euro":"Western Europe - Euro",
                                 "Western Europe - Non Euro":"Western Europe - Non Euro",
                                 "Emerging 4 Tigers":"Hong Kong, Singapore, SouthKorea and Taiwan",
                                 "Emerging Asia - Ex 4 Tigers":"Asia Emerging", 
                                 "Australasia":"Australasia",
                                 "Emerging Europe":"Europe Emerging",
                                 "Japan":"Japan",
                                 "Central & Latin America":"Central & Latin America",
                                 "United Kingdom":"United Kingdom",
                                 "Middle East / Africa":"Middle East / Africa",
                                 "Not Classified": "Not Classified",
                                },                                                           

                          },
                          
              'Holding': { 'url': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                          'idtype' : 'ISIN',
                          'viewid' : '{viewid}',
                          'jsonpath': '$.[0].Portfolios[0].PortfolioHoldings[?(@.ISIN)]',
                          'category': 'SecurityName',
                          'percent': 'Weighting',
                          'table-xr': -1,
                          'column-xr': -1,
                          'table-stock-xr': {14},
                          'column-stock-xr': 0,
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
            url = f"https://www.morningstar.{DOMAIN}/en/util/SecuritySearch.ashx"
            payload = {
                'q': isin,
                'preferedList': '',
                'source': 'nav',
                'moduleId': 6,
                'ifIncludeAds': False,
                'usrtType': 'v'
                }
            headers = {
                'accept': '*/*',
                'accept-encoding': 'gzip, deflate, br',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
                }
            resp = requests.post(url, data=payload, headers=headers)
            response = resp.content.decode('utf-8')
            if response:
                secid = re.search(r'\{"i":"([^"]+)"', response).group(1) 
                secid_type =response.split("|")[2].lower()
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

    def calculate_grouping(self, categories, percentages, grouping_name, net_equity):
        for category_name, percentage in zip(categories, percentages):
            self.grouping[grouping_name][escape(category_name)] = self.grouping[grouping_name].get(escape(category_name),0) +  percentage  

        if grouping_name !='Asset-Type':
            self.grouping[grouping_name] = {k:v*net_equity for k, v in 
                                            self.grouping[grouping_name].items()}


     
        
    def load (self, isin, secid, name, isRetired):
        secid, secid_type, domain = Isin2secid.get_secid(isin)
        if secid == '':
            print(f"@ isin {isin} not found in Morningstar for domain '{DOMAIN}', skipping it... Try another domain with -d <domain>")
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
                 print(f"@ Retrieving data for {secid_type} {isin} ({secid}) using x-ray (de)")
             else:    
                 print(f"@ isin {isin} is a stock, skipping it...")
        else:
             print(f"@ Retrieving data for {secid_type} {isin} ({secid}) using domain '{domain}'...")
        print(f"  [{name}]")
        headers_short = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            }
        headers = headers_short.copy()
        headers['Authorization'] = f'Bearer {bearer_token}'
        
        params = {
            'premiumNum': '10',
            'freeNum': '10',
            'languageId': 'de-DE',
            'locale': 'en',
            'clientId': 'MDC_intl',
            'benchmarkId': 'category',
            'version': '3.60.0',
            'currencyId' : 'EUR',
            'responseViewFormat' : 'json'
        }
    
        
        self.grouping=dict()
        for taxonomy in taxonomies:
            self.grouping[taxonomy] = defaultdict(float)
       
        non_categories = ['avgMarketCap', 'portfolioDate', 'name', 'masterPortfolioId', "14", "15", "16" ]
        json_not_found = False
        
        if secid_type!="stock":
          for grouping_name, taxonomy in taxonomies.items():
            url = taxonomy['url'] 
            # use etf or fund endpoint
            url = url.replace("{type}", secid_type)
            # use corresponding id (secid or isin)
            url = url.replace("{secid}", secid)
            url = url.replace("{isin}", isin)
            for urlparam in ['component', 'idtype', 'viewid']:
              if taxonomy.get(urlparam): params[urlparam] = taxonomy[urlparam]
            if params.get('viewid'): params['viewid'] = params['viewid'].replace("{viewid}", HOLDING_VIEW_ID)
            resp = requests.get(url, params=params, headers=headers)
            if resp.status_code == 401:
                json_not_found = True
                if grouping_name != 'Holding' and grouping_name != 'Country' and not NO_XRAY:
                    print(f"  {grouping_name} for secid {secid} will be retrieved from x-ray...")
                else:
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
                            net_equity = long_equity          # legacy behaviour was with long instead of net
                        except TypeError:
                            print(f"  Warning: No information on {grouping_name} for {secid}")
                else:
                    # every match is a category 
                    if grouping_name == 'Holding' and MAX_HOLDINGS >= 0:
                      value = jsonpath.find(response)[:MAX_HOLDINGS]
                    elif grouping_name == 'Asset-Type':
                      value = jsonpath.find(response)[:9]
                    else:
                      value = jsonpath.find(response)[:3200]
                    keys = [key.value[taxonomy['category']] for key in value if key.value[taxonomy['category']] not in non_categories]
                    if len(value) == 0 or value[0].value.get(taxonomy['percent'],"") =="":
                        print(f"  Warning: percentages not found for {grouping_name} for {secid}")
                        json_not_found = True
                    else:
                        percentages = [float(key.value[taxonomy['percent']]) for key in value]
                    if grouping_name == 'Asset-Type':
                        net_equity = 0.0
                        for key in value:
                          if (key.value[taxonomy['category']] == "1"):
                            net_equity = min (1.0, float(key.value[taxonomy['percent']])/100)                   

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
                    self.calculate_grouping (categories, percentages, grouping_name, net_equity)
                
            except Exception:
                print(f"  Warning: Problem with {grouping_name} for secid {secid} in PortfolioSAL...")
                json_not_found = True
                
            
          if json_not_found:       
           if not NO_XRAY:
            
            non_categories = ['Defensive', 'Cyclical',  'Sensitive',
                              'Greater Europe', 'Americas', 'Greater Asia', 
                              ]
            url = "https://lt.morningstar.com/j2uwuwirpv/xray/default.aspx?LanguageId=en-EN&PortfolioType=2&SecurityTokenList=" + secid + "]2]0]FOESP%24%24ALL_1340&values=100"
            # print(url)
            resp = requests.get(url, headers=headers_short)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for grouping_name, taxonomy in taxonomies.items():
                if self.grouping[grouping_name]:
                    continue
                if grouping_name == 'Holding' or grouping_name == 'Country':
                    continue  
                table = soup.select("table.ms_data")[taxonomy['table-xr']]
                trs = table.select("tr")[1:]
                if grouping_name == 'Asset-Type':
                    net_equity = float(trs[0].select("td")[0].text.replace(",","."))/100
                categories = []
                percentages = []
                for tr in trs:
                    if len(tr.select('th'))>0:
                        header = tr.th
                    else:
                        header = tr.td
                    if tr.text != '' and header.text not in non_categories:
                        categories.append(header.text)                                     
                        if len(tr.select("td")) > taxonomy['column-xr']:
                            percentages.append(float('0' + tr.select("td")[taxonomy['column-xr']].text.replace(",",".").replace("-","")))
                        else:
                            percentages.append(0.0)
                if len(taxonomy.get('map2',{})) != 0:
                    categories = [taxonomy['map2'][key] for key in categories]
                if categories:
                    print (f"  {grouping_name} retrieved from x-ray (lt.morningstar.com)")
                else:
                    print (f"  Warning: {grouping_name} not retrieved from x-ray (lt.morningstar.com)")
        
                self.calculate_grouping (categories, percentages, grouping_name, net_equity)
                
        else:		# secid_type=="stock"
         if STOCKS:
              
           non_categories = ['Defensive', 'Cyclical',  'Sensitive',
                              'Greater Europe', 'Americas', 'Greater Asia', 
                            ] 
           url = f'https://tools.morningstar.de/de/xray/default.aspx?LanguageId=en-EN&PortfolioType=2&SecurityTokenList={secid}&values=100'      
           # print(url)
           resp = requests.get(url, headers=headers_short)
           soup = BeautifulSoup(resp.text, 'html.parser')
           table = soup.select("table")
           issue_with_xray = False
           
           for grouping_name, taxonomy in taxonomies.items():           
             categories = []
             percentages = []
             for table_number in taxonomy['table-stock-xr']:
                trs = table[table_number].select("tr")[1:]
                if grouping_name == 'Asset-Type':
                    net_equity = float(trs[0].select("td")[0].text.replace(",","."))/100
                if grouping_name == 'Country':
                    categories.append(table[table_number].select("tr")[1].select('td')[3].text.replace(" ",""))
                    percentages.append(float(100))
                    continue
                if grouping_name == 'Holding':
                    categories.append(table[table_number].select("tr")[1].select('td')[taxonomy['column-stock-xr']].text)
                    percentages.append(float(100))
                    continue                    
                for tr in trs:
                    if len(tr.select('th'))>0:
                        header = tr.th
                    else:
                        header = tr.td
                    if tr.text != '' and header.text not in non_categories:
                        categories.append(header.text)                                     
                        if len(tr.select("td")) > taxonomy['column-stock-xr']:
                            percentages.append(float('0' + tr.select("td")[taxonomy['column-stock-xr']].text.replace(",",".").replace("-","")))
                        else:
                            percentages.append(0.0)
                try:
                  if len(taxonomy.get('map3',{})) != 0:
                    categories = [taxonomy['map3'][key] for key in categories]
                  if sum(percentages) == 0:
                    categories = [] 
                except Exception:
                    categories = []
                    issue_with_xray = True

             if issue_with_xray == True:
                 categories = []

             if categories:
                    # print (f"  {grouping_name} retrieved from x-ray (de)")
                    pass
             else:
                    print (f"  Warning: {grouping_name} not retrieved from x-ray (de)")
        
             self.calculate_grouping (categories, percentages, grouping_name, net_equity)                        
      
        
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
    #usage="%(prog) <input_file> [<output_file>] [-d domain] [-stocks] [-xr] [-top_holdings {0,10,25,50,100,1000,3200}]",
    description='\r\n'.join(["reads a portfolio performance xml file and auto-classifies",
                 "the securities in it by asset-type, stock-style, sector, holdings, region and country weights",
                 "For each security, you need to have an ISIN"])
    )

    # Morningstar domain where your securities can be found
    # e.g. es for spain, de for germany, fr for france...
    # this is only used to find the corresponding secid from the ISIN
    
    
    parser.add_argument('-d', default='de',  dest='domain', type=str,
                        help='Morningstar domain from which to retrieve the secid (default: de)')
    
    parser.add_argument('input_file', metavar='input_file', type=str,
                   help='path to unencrypted pp.xml file')
    
    parser.add_argument('output_file', metavar='output_file', type=str, nargs='?',
                   help='path to auto-classified output file', default='pp_classified.xml')
                   
    parser.add_argument('-stocks', action='store_true', dest='retrieve_stocks',
                   help='activates retrieval of stocks from x-ray')
                   
    parser.add_argument('-xr', action='store_true', dest='xray',
                   help='activates retrieval from x-ray as backup for etfs/funds')
                   
    parser.add_argument('-top_holdings', choices=['0', '10', '25', '50', '100', '1000', '3200'], default='10', dest='top_holdings',
                   help='defines how many top holdings are retrieved for etfs/funds (values above 100 are not recommened, \'0\' keeps existing holding data)')
                   

    args = parser.parse_args()
    
    if "input_file" not in args:
        parser.print_help()
    else:
        DOMAIN = args.domain
        NO_XRAY = not args.xray
        STOCKS = args.retrieve_stocks
        BEARER_TOKEN = ""
        if args.top_holdings == '0':
            HOLDING_VIEW_ID, MAX_HOLDINGS = "Top10", int(0)
        elif args.top_holdings == '10': 
            HOLDING_VIEW_ID, MAX_HOLDINGS = "Top10", int(-1)
        elif args.top_holdings == '25': 
            HOLDING_VIEW_ID, MAX_HOLDINGS = "Top25", int(-1)            
        elif args.top_holdings == '50': 
            HOLDING_VIEW_ID, MAX_HOLDINGS = "Allholdings", int(50)            
        elif args.top_holdings == '100':
            HOLDING_VIEW_ID, MAX_HOLDINGS = "Allholdings", int(100)
        elif args.top_holdings == '1000':
            HOLDING_VIEW_ID, MAX_HOLDINGS = "Allholdings", int(1000)    # values above 100 might overload the GUI of PP
        elif args.top_holdings == '3200':
            HOLDING_VIEW_ID, MAX_HOLDINGS = "Allholdings", int(-1)      # general enforcement of 3200 in code      
        # Isin2secid.load_cache()
        pp_file = PortfolioPerformanceFile(args.input_file)
        for taxonomy in taxonomies:
            pp_file.add_taxonomy(taxonomy)
        # Isin2secid.save_cache()
        pp_file.write_xml(args.output_file)
        pp_file.dump_csv()
      
