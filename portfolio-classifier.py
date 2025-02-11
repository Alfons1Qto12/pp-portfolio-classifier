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
                             'url2': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                             'idtype2' : 'ISIN',  
                             'viewid2' : 'snapshot',
                             'jsonpath2': '$.[0].Type',
                             'map':{"1" : "Stocks", 
                                    "3" : "Bonds", 
                                    "7" : "Cash",
                                    "2" : "Other",
                                    "4" : "Other",
                                    "5" : "Other",
                                    "6" : "Other",
                                    "8" : "Other",
                                    "99" : "Not classified",
                                    },
                             'map2':{"Stock" : "Stocks",
                                    },       
                             },
              'Stock-style': {'url': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                             'idtype' : 'ISIN',  
                             'viewid' : 'ITsnapshot',
                             'jsonpath': '$.[0].Portfolios[0].StyleBoxBreakdown[?(@.SalePosition == "N")].BreakdownValues.[*]',
                             'category': 'Type',
                             'percent': 'Value',
                             'url2': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                             'idtype2' : 'ISIN',  
                             'viewid2' : 'snapshot',
                             'jsonpath2': '$..InvestmentStyle',                            
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
                             'map2':{ 1:"Large Value", 
                                     2:"Large Blend",
                                     3:"Large Growth",
                                     4:"Mid-Cap Value", 
                                     5:"Mid-Cap Blend",
                                     6:"Mid-Cap Growth",
                                     7:"Small Value",
                                     8:"Small Blend",
                                     9:"Small Growth",
                                    },
                            },                            

              'Sector': {    'url': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                             'idtype' : 'ISIN',  
                             'viewid' : 'ITsnapshot',
                             'jsonpath': '$.[0].Portfolios[0].GlobalStockSectorBreakdown[?(@.SalePosition == "N")].BreakdownValues.[*]',
                             'category': 'Type',
                             'percent': 'Value',
                             'url2': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                             'idtype2' : 'ISIN',  
                             'viewid2' : 'snapshot',
                             'jsonpath2': '$.[0].Sector.SectorCode',                                                    
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
              'Region': {    'url': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                             'idtype' : 'ISIN',  
                             'viewid' : 'ITsnapshot',
                             'jsonpath': '$.[0].Portfolios[0].RegionalExposure[?(@.SalePosition == "N")].BreakdownValues.[*]',
                             'category': 'Type',
                             'percent': 'Value',
                             'url2': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                             'idtype2' : 'ISIN',  
                             'viewid2' : 'snapshot',
                             'jsonpath2': '$.[0].Country',         # will be mapped by map2 to Region                                           
                             'map' : { "1" : "North America",      # United States
                                 "2" : "North America",            # Canada
                                 "3" : "Central & Latin America",  # Latin America
                                 "4": "United Kingdom",
                                 "5": "Europe Developed",          # Eurozone
                                 "6": "Europe Developed",          # Europe - ex Euro
                                 "7": "Europe Emerging",
                                 "8": "Middle East / Africa",      # Africa
                                 "9": "Middle East / Africa",      # Middle East
                                 "10" :"Japan",
                                 "11" :"Australasia",
                                 "12" :"Asia Developed",                              
                                 "13" :"Asia Emerging",
                                  # "14", "15", "16" in non_categories
                                 },
                              'map2' : { "USA" : "North America",
                                         "CAN" : "North America",
                                         "AIA" : "Central & Latin America",
                                         "ATG" : "Central & Latin America",
                                         "ARG" : "Central & Latin America",
                                         "ABW" : "Central & Latin America",
                                         "BHS" : "Central & Latin America",
                                         "BRB" : "Central & Latin America",
                                         "BLZ" : "Central & Latin America",
                                         "BMU" : "Central & Latin America",
                                         "BOL" : "Central & Latin America",
                                         "BES" : "Central & Latin America",
                                         "BRA" : "Central & Latin America",
                                         "VGB" : "Central & Latin America",
                                         "CYM" : "Central & Latin America",
                                         "CHL" : "Central & Latin America",
                                         "COL" : "Central & Latin America",
                                         "CRI" : "Central & Latin America",
                                         "CUB" : "Central & Latin America",
                                         "CUW" : "Central & Latin America",
                                         "DMA" : "Central & Latin America",
                                         "DOM" : "Central & Latin America",
                                         "ECU" : "Central & Latin America",
                                         "SLV" : "Central & Latin America",
                                         "FLK" : "Central & Latin America",
                                         "GUF" : "Central & Latin America",
                                         "GRD" : "Central & Latin America",
                                         "GLP" : "Central & Latin America",
                                         "GTM" : "Central & Latin America",
                                         "GUY" : "Central & Latin America",
                                         "HTI" : "Central & Latin America",
                                         "HND" : "Central & Latin America",
                                         "JAM" : "Central & Latin America",
                                         "MTQ" : "Central & Latin America",
                                         "MEX" : "Central & Latin America",
                                         "MSR" : "Central & Latin America",
                                         "NIC" : "Central & Latin America",
                                         "PAN" : "Central & Latin America",
                                         "PRY" : "Central & Latin America",
                                         "PER" : "Central & Latin America",
                                         "PRI" : "Central & Latin America",
                                         "KNA" : "Central & Latin America",
                                         "LCA" : "Central & Latin America",
                                         "VCT" : "Central & Latin America",
                                         "SUR" : "Central & Latin America",
                                         "TTO" : "Central & Latin America",
                                         "TCA" : "Central & Latin America",
                                         "URY" : "Central & Latin America",
                                         "VIR" : "Central & Latin America",
                                         "VEN" : "Central & Latin America",
                                         "GBR" : "United Kingdom",
                                         "IMN" : "United Kingdom",
                                         "AND" : "Europe Developed",
                                         "AUT" : "Europe Developed",
                                         "BEL" : "Europe Developed",
                                         "CYP" : "Europe Developed",
                                         "DNK" : "Europe Developed",
                                         "FRO" : "Europe Developed",
                                         "FIN" : "Europe Developed",
                                         "FRA" : "Europe Developed",
                                         "DEU" : "Europe Developed",
                                         "GIB" : "Europe Developed",
                                         "GRC" : "Europe Developed",
                                         "GRL" : "Europe Developed",
                                         "ISL" : "Europe Developed",
                                         "IRL" : "Europe Developed",
                                         "ITA" : "Europe Developed",
                                         "LIE" : "Europe Developed",
                                         "LUX" : "Europe Developed",
                                         "MLT" : "Europe Developed",
                                         "MCO" : "Europe Developed",
                                         "NLD" : "Europe Developed",
                                         "NOR" : "Europe Developed",
                                         "PRT" : "Europe Developed",
                                         "SMR" : "Europe Developed",
                                         "SVN" : "Europe Developed",
                                         "ESP" : "Europe Developed",
                                         "SJM" : "Europe Developed",
                                         "SWE" : "Europe Developed",
                                         "CHE" : "Europe Developed",
                                         "VAT" : "Europe Developed",
                                         "ALB" : "Europe Emerging",
                                         "BLR" : "Europe Emerging",
                                         "BIH" : "Europe Emerging",
                                         "BGR" : "Europe Emerging",
                                         "HRV" : "Europe Emerging",
                                         "CZE" : "Europe Emerging",
                                         "EST" : "Europe Emerging",
                                         "HUN" : "Europe Emerging",
                                         "LVA" : "Europe Emerging",
                                         "LTU" : "Europe Emerging",
                                         "MKD" : "Europe Emerging",
                                         "MDA" : "Europe Emerging",
                                         "POL" : "Europe Emerging",
                                         "ROU" : "Europe Emerging",
                                         "RUS" : "Europe Emerging",
                                         "SRB" : "Europe Emerging",
                                         "SVK" : "Europe Emerging",
                                         "TUR" : "Europe Emerging",
                                         "UKR" : "Europe Emerging",
                                         "DZA" : "Middle East / Africa",
                                         "AGO" : "Middle East / Africa",
                                         "BHR" : "Middle East / Africa",
                                         "BEN" : "Middle East / Africa",
                                         "BWA" : "Middle East / Africa",
                                         "BVT" : "Middle East / Africa",
                                         "BFA" : "Middle East / Africa",
                                         "BDI" : "Middle East / Africa",
                                         "CMR" : "Middle East / Africa",
                                         "CPV" : "Middle East / Africa",
                                         "CAF" : "Middle East / Africa",
                                         "TCD" : "Middle East / Africa",
                                         "COM" : "Middle East / Africa",
                                         "COG" : "Middle East / Africa",
                                         "CIV" : "Middle East / Africa",
                                         "COD" : "Middle East / Africa",
                                         "DJI" : "Middle East / Africa",
                                         "EGY" : "Middle East / Africa",
                                         "GNQ" : "Middle East / Africa",
                                         "ERI" : "Middle East / Africa",
                                         "ETH" : "Middle East / Africa",
                                         "GAB" : "Middle East / Africa",
                                         "GMB" : "Middle East / Africa",
                                         "GHA" : "Middle East / Africa",
                                         "GIN" : "Middle East / Africa",
                                         "GNB" : "Middle East / Africa",
                                         "IRN" : "Middle East / Africa",
                                         "IRQ" : "Middle East / Africa",
                                         "ISR" : "Middle East / Africa",
                                         "JOR" : "Middle East / Africa",
                                         "KEN" : "Middle East / Africa",
                                         "KWT" : "Middle East / Africa",
                                         "LBN" : "Middle East / Africa",
                                         "LSO" : "Middle East / Africa",
                                         "LBR" : "Middle East / Africa",
                                         "LBY" : "Middle East / Africa",
                                         "MDG" : "Middle East / Africa",
                                         "MWI" : "Middle East / Africa",
                                         "MLI" : "Middle East / Africa",
                                         "MRT" : "Middle East / Africa",
                                         "MUS" : "Middle East / Africa",
                                         "MYT" : "Middle East / Africa",
                                         "MAR" : "Middle East / Africa",
                                         "MOZ" : "Middle East / Africa",
                                         "NAM" : "Middle East / Africa",
                                         "NER" : "Middle East / Africa",
                                         "NGA" : "Middle East / Africa",
                                         "OMN" : "Middle East / Africa",
                                         "QAT" : "Middle East / Africa",
                                         "REU" : "Middle East / Africa",
                                         "RWA" : "Middle East / Africa",
                                         "STP" : "Middle East / Africa",
                                         "SAU" : "Middle East / Africa",
                                         "SEN" : "Middle East / Africa",
                                         "SYC" : "Middle East / Africa",
                                         "SLE" : "Middle East / Africa",
                                         "SOM" : "Middle East / Africa",
                                         "ZAF" : "Middle East / Africa",
                                         "SHN" : "Middle East / Africa",
                                         "SDN" : "Middle East / Africa",
                                         "SWZ" : "Middle East / Africa",
                                         "SYR" : "Middle East / Africa",
                                         "TZA" : "Middle East / Africa",
                                         "TGO" : "Middle East / Africa",
                                         "TUN" : "Middle East / Africa",
                                         "UGA" : "Middle East / Africa",
                                         "ARE" : "Middle East / Africa",
                                         "PSE" : "Middle East / Africa",
                                         "ESH" : "Middle East / Africa",
                                         "YEM" : "Middle East / Africa",
                                         "ZMB" : "Middle East / Africa",
                                         "ZWE" : "Middle East / Africa",
                                         "JPN" : "Japan",
                                         "AUS" : "Australasia",
                                         "NZL" : "Australasia",
                                         "BRN" : "Asia Developed",
                                         "PYF" : "Asia Developed",
                                         "GUM" : "Asia Developed",
                                         "HKG" : "Asia Developed",
                                         "MAC" : "Asia Developed",
                                         "NCL" : "Asia Developed",
                                         "SGP" : "Asia Developed",
                                         "KOR" : "Asia Developed",
                                         "TWN" : "Asia Developed",
                                         "AFG" : "Asia Emerging",
                                         "ASM" : "Asia Emerging",
                                         "ARM" : "Asia Emerging",
                                         "AZE" : "Asia Emerging",
                                         "BGD" : "Asia Emerging",
                                         "BTN" : "Asia Emerging",
                                         "MMR" : "Asia Emerging",
                                         "KHM" : "Asia Emerging",
                                         "CHN" : "Asia Emerging",
                                         "CXR" : "Asia Emerging",
                                         "CCK" : "Asia Emerging",
                                         "COK" : "Asia Emerging",
                                         "TLS" : "Asia Emerging",
                                         "FJI" : "Asia Emerging",
                                         "GEO" : "Asia Emerging",
                                         "HMD" : "Asia Emerging",
                                         "IND" : "Asia Emerging",
                                         "IDN" : "Asia Emerging",
                                         "KAZ" : "Asia Emerging",
                                         "KIR" : "Asia Emerging",
                                         "KGZ" : "Asia Emerging",
                                         "LAO" : "Asia Emerging",
                                         "MYS" : "Asia Emerging",
                                         "MDV" : "Asia Emerging",
                                         "MHL" : "Asia Emerging",
                                         "FSM" : "Asia Emerging",
                                         "MNG" : "Asia Emerging",
                                         "NRU" : "Asia Emerging",
                                         "NPL" : "Asia Emerging",
                                         "NIU" : "Asia Emerging",
                                         "NFK" : "Asia Emerging",
                                         "PRK" : "Asia Emerging",
                                         "MNP" : "Asia Emerging",
                                         "PAK" : "Asia Emerging",
                                         "PLW" : "Asia Emerging",
                                         "PNG" : "Asia Emerging",
                                         "PHL" : "Asia Emerging",
                                         "PCN" : "Asia Emerging",
                                         "WSM" : "Asia Emerging",
                                         "SLB" : "Asia Emerging",
                                         "LKA" : "Asia Emerging",
                                         "TJK" : "Asia Emerging",
                                         "THA" : "Asia Emerging",
                                         "TKL" : "Asia Emerging",
                                         "TON" : "Asia Emerging",
                                         "TKM" : "Asia Emerging",
                                         "TUV" : "Asia Emerging",
                                         "UZB" : "Asia Emerging",
                                         "VUT" : "Asia Emerging",
                                         "VNM" : "Asia Emerging",
                                         "WLF" : "Asia Emerging"                      
                               },
                         },  
              'Country': {   'url': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                             'idtype' : 'ISIN',
                             'viewid' : 'ITsnapshot',
                             'jsonpath': '$.[0].Portfolios[0].CountryExposure[?(@.Type == "Equity" & @.SalePosition == "N")].BreakdownValues.[*]',
                             'category': 'Type',
                             'percent': 'Value',
                             'url2': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                             'idtype2' : 'ISIN',  
                             'viewid2' : 'snapshot',
                             'jsonpath2': '$.[0].Country',                                                    
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
                          },
                          
              'Holding': {   'url': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                             'idtype' : 'ISIN',
                             'viewid' : '{viewid}',
                             'jsonpath': '$.[0].Portfolios[0].PortfolioHoldings[?(@.ISIN)]',
                             'category': 'SecurityName',
                             'percent': 'Weighting',
                             'url2': 'https://www.emea-api.morningstar.com/ecint/v1/securities/{isin}',
                             'idtype2' : 'ISIN',  
                             'viewid2' : 'snapshot',
                             'jsonpath2': '$.[0].Name',
                         },                                
                          
        }


                    

class Security:
 
    def __init__ (self, **kwargs):
        self.__dict__.update(kwargs)
        self.holdings = []

    def load_holdings (self):
        if len(self.holdings) == 0:
            self.holdings = SecurityHoldingReport()
            self.holdings.load(isin = self.ISIN, name = self.name, isRetired = self.isRetired)
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

    
    def get_bearer_token(self, domain):
        global BEARER_TOKEN         
        # get one bearer token for all requests
        if BEARER_TOKEN == "":
          headers = {
           'accept': '*/*',
           'accept-encoding': 'gzip, deflate, br',
           'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
                }               
          url = f'https://www.morningstar.{domain}/Common/funds/snapshot/PortfolioSAL.aspx'
          response = requests.get(url, headers=headers)
          token_regex = r"const maasToken \=\s\"(.+)\""
          resultstringtoken = re.findall(token_regex, response.text)[0]
          BEARER_TOKEN = resultstringtoken
        else:
          resultstringtoken = BEARER_TOKEN
        return resultstringtoken

    def calculate_grouping(self, categories, percentages, grouping_name, net_equity):
        for category_name, percentage in zip(categories, percentages):
            self.grouping[grouping_name][escape(category_name)] = self.grouping[grouping_name].get(escape(category_name),0) +  percentage  

        if grouping_name !='Asset-Type':
            self.grouping[grouping_name] = {k:v*net_equity for k, v in 
                                            self.grouping[grouping_name].items()}
    
        
    def load (self, isin, name, isRetired):
                
        print(f"[{name}]:")
        if isRetired=="true":
            print(f"  @ ISIN {isin} is inactive, skipping it...")
            return
        elif isin == "":
            print(f"  @ No ISIN, skipping it...")       
            return       
        
        domain = DOMAIN       
        bearer_token = self.get_bearer_token(domain)
        secid_type = ""
        secid = isin
        
        # Retrieve basics about the security
        headers_short = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            }
        headers = headers_short.copy()
        headers['Authorization'] = f'Bearer {bearer_token}'
        url = 'https://www.emea-api.morningstar.com/ecint/v1/securities/' + isin
        params = {
            'idtype' : 'ISIN',				
            'viewid' : 'snapshot',			
            'currencyId' : 'EUR',
            'responseViewFormat' : 'json',
            'languageId': 'en-UK',
           }
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code == 200:
            response = resp.json() 
            jsonpath = parse('$.[0].Type')
            if len(jsonpath.find(response)) > 0:
              secid_type = jsonpath.find(response)[0].value
            jsonpath = parse('$.[0].Name')
            if len(jsonpath.find(response)) > 0:
              secid_name = jsonpath.find(response)[0].value  
            
        if secid_type != 'Stock' and secid_type != 'Fund':
            print(f" @ No matching information for ISIN {isin} found on Morningstar, skipping it...")
            return
        elif secid_type == "Stock":
             if STOCKS:
                 print(f"  @ Retrieving data for stock {isin}")
                 print(f"    (Name: \"{secid_name}\")") 
             else:    
                 print(f"  @ ISIN {isin} is a stock, skipping it...")
                 print(f"    (Name: \"{secid_name}\")") 
                 return
        else:
             print(f"  @ Retrieving data for fund {isin} from Morningstar")
             print(f"    (Name: \"{secid_name}\")") 

        self.secid = secid		# marks the security as retrieved
            
        self.grouping=dict()
        for taxonomy in taxonomies:
            self.grouping[taxonomy] = defaultdict(float)
       
        non_categories = ['avgMarketCap', 'portfolioDate', 'name', 'masterPortfolioId', "14", "15", "16" ]
        
        if secid_type !="Stock":
          for grouping_name, taxonomy in taxonomies.items():
            categories = []
            url = taxonomy['url'] 
            url = url.replace("{isin}", isin)
            for urlparam in ['idtype', 'viewid']:
              if taxonomy.get(urlparam): params[urlparam] = taxonomy[urlparam]
            if params.get('viewid'): params['viewid'] = params['viewid'].replace("{viewid}", HOLDING_VIEW_ID)
            resp = requests.get(url, params=params, headers=headers)
            if resp.status_code == 401:
                print(f"  Warning: No information on {grouping_name} for {secid}")
                continue
            try:
                response = resp.json()
                jsonpath = parse(taxonomy['jsonpath'])
                percent_field = taxonomy['percent']

                
                if grouping_name == 'Holding' and MAX_HOLDINGS >= 0:
                  value = jsonpath.find(response)[:MAX_HOLDINGS]
                elif grouping_name == 'Asset-Type':
                  value = jsonpath.find(response)[:9]
                else:
                  value = jsonpath.find(response)[:3200]
                      
                keys = [key.value[taxonomy['category']] for key in value if key.value[taxonomy['category']] not in non_categories]
                if len(value) == 0 or value[0].value.get(taxonomy['percent'],"") =="":
                    print(f"  Warning: percentages not found for {grouping_name} for {secid}")
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
                        print(f"  Warning: Categories not mapped: {unmapped} for {secid} for {grouping_name}")
                else:
                    # capitalize first letter if not mapping
                    categories = [key[0].upper() + key[1:] for key in keys]                
                if percentages:
                    self.calculate_grouping (categories, percentages, grouping_name, net_equity)
                
            except Exception:
                print(f"  Warning: Problem with {grouping_name} for ISIN {secid} ...")                    
                
        else:  # if secid_type=="Stock"
         if STOCKS:
          for grouping_name, taxonomy in taxonomies.items():
            categories = []
            percentages = []
            keys = []
            url = taxonomy['url2'] 
            url = url.replace("{isin}", isin)
            if taxonomy.get('idtype2'): params['idtype'] = taxonomy['idtype2']
            if taxonomy.get('viewid2'): params['viewid'] = taxonomy['viewid2']
            resp = requests.get(url, params=params, headers=headers)
            if resp.status_code == 401:
                print(f"  Warning: No information on {grouping_name} for {secid}")
                continue
            if True == True:
                response = resp.json()
                jsonpath = parse(taxonomy['jsonpath2'])
                if len(jsonpath.find(response)) > 0:
                     categories.append(jsonpath.find(response)[0].value)
                     keys.append(jsonpath.find(response)[0].value)
                     percentages.append(float (100.0))
                     net_equity = float (1.0)
                     
                # Map names if there is a map2 or a map
                unmapped = []
                if len(taxonomy.get('map2',{})) != 0:
                    categories = [taxonomy['map2'][key] for key in keys if key in taxonomy['map2'].keys()]
                    unmapped = [key for key in keys if key not in taxonomy['map2'].keys()]
                    if  unmapped:
                        print(f"  Warning: Categories not mapped: {unmapped} for {secid} for {grouping_name}")
                elif len(taxonomy.get('map',{})) != 0:
                    categories = [taxonomy['map'][key] for key in keys if key in taxonomy['map'].keys()]
                    unmapped = [key for key in keys if key not in taxonomy['map'].keys()]
                    if  unmapped:
                        print(f"  Warning: Categories not mapped: {unmapped} for {secid} for {grouping_name}")
                    
                if percentages:
                    self.calculate_grouping (categories, percentages, grouping_name, net_equity)
               
            else:
                print(f"  Warning: Problem with {grouping_name} for ISIN {secid} ...")         
          

            if categories:
                    # print (f"  {grouping_name} retrieved for stock")
                    pass
            else:
                    print (f"  Warning: {grouping_name} not retrieved for stock")
        
            # self.calculate_grouping (categories, percentages, grouping_name, net_equity)                        
      
        
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
                if isin.text is not None:
                   isin = isin.text
                else:
                   isin = ""
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
        pp_file = PortfolioPerformanceFile(args.input_file)
        for taxonomy in taxonomies:
            pp_file.add_taxonomy(taxonomy)
        pp_file.write_xml(args.output_file)
        pp_file.dump_csv()
      
