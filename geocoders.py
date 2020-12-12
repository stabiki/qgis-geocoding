# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Geocoding
Description          : Geocoding and reverse Geocoding using Web Services
Date                 : 23/02/2018
copyright            : (C) 2009-2018 by ItOpen
email                : info@itopen.it
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import re
from pyproj import Proj, transform
from .networkaccessmanager import NetworkAccessManager
import sys, os, json
from qgis.core import QgsSettings, QgsMessageLog

NAM = NetworkAccessManager()

def logMessage(msg):
    if QgsSettings().value('PythonPlugins/GeoCoding/writeDebug'):
        QgsMessageLog.logMessage(msg, 'GeoCoding')
    

class GeoCodeException(Exception):
    pass

class OsmGeoCoder():

    url = 'https://nominatim.openstreetmap.org/search?format=json&q={address}'
    reverse_url = 'https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}'

    def geocode(self, address):
        try: 
            url = self.url.format(**{'address': address.decode('utf8')})
            logMessage(url)
            results = json.loads(NAM.request(url, blocking=True)[1].decode('utf8'))
            return [(rec['display_name'], (rec['lon'], rec['lat'])) for rec in results]
        except Exception as e:
            raise GeoCodeException(str(e))

    def reverse(self, lon, lat):
        """single result"""
        try: 
            url = self.reverse_url.format(**{'lon': lon, 'lat': lat})
            logMessage(url)
            rec = json.loads(NAM.request(url, blocking=True)[1].decode('utf8'))
            return [(rec['display_name'], (rec['lon'], rec['lat']))]
        except Exception as e:
            raise GeoCodeException(str(e))

class DorisGeoCoder():
    url = 'https://srv.doris.at/solr/searchservice/search/all2/?q={address}'
     
    fromProj = Proj('epsg:3857')
    toProj   = Proj('epsg:4326')
    
    def geoToLonLat(self, geo):
        geo = [re.sub('[^0-9\\.]', '', part) for part in geo.split(' ')]
        return transform(self.fromProj, self.toProj, geo[0], geo[1])[::-1]

    def geocode(self, address):
        try: 
            url = self.url.format(**{'address': address.decode('utf8')})
            logMessage(url)
            results = json.loads(NAM.request(url, blocking = True)[1].decode('utf8'))['response']['docs']
            return [(rec['title'][0], (self.geoToLonLat(rec['geo'][0]))) for rec in results]
        except Exception as e:
            raise GeoCodeException(str(e))

    def reverse(self, lon, lat):
        return ['unsupported']

class GoogleGeoCoder():

    url = 'https://maps.googleapis.com/maps/api/geocode/json?address={address}'
    reverse_url = 'https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}'

    def __init__(self, api_key=None):
        self.api_key = api_key

    def geocode(self, address):

        if self.api_key is not None and self.api_key.replace(' ', '') != '':
            url += self.url + '&key=' + self.api_key
        else:
            url = self.url

        try: 
            url = url.format(**{'address': address.decode('utf8')})
            logMessage(url)
            results = json.loads(NAM.request(url, blocking=True)[1].decode('utf8'))['results']
            return [(rec['formatted_address'], (rec['geometry']['location']['lng'], rec['geometry']['location']['lat'])) for rec in results]
        except Exception as e:
            raise GeoCodeException(str(e))

    def reverse(self, lon, lat):
        if self.api_key is not None:
            url = self.reverse_url + '&key=' + self.api_key
        else:
            url = self.reverse_url
        try:
            url = url.format(**{'lon': lon, 'lat': lat})
            logMessage(url)
            results = json.loads(NAM.request(url, blocking=True)[1].decode('utf8'))['results']
            return [(rec['formatted_address'], (rec['geometry']['location']['lng'], rec['geometry']['location']['lat'])) for rec in results]
        except Exception as e:
            raise GeoCodeException(str(e))


