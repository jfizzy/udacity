from xml.dom import minidom
from xml.parsers.expat import ExpatError
import re

coord_check = re.compile(r"^(-{0,1}[0-9]+\.{1}[0-9]+),(-{0,1}[0-9]+\.{1}[0-9]+)$")

def get_coords(ip):
    url = IP_URL + ip
    content = None
    try:
        content = urllib2.urlopen(url).read()
    except urllib2.URLError:
        return
    
    if content:
        #parse xml and find coordinates
        try:
            xmldoc = minidom.parseString(xml)
            coords = xmldoc.getElementsByTagName('gml:coordinates')[0].firstChild.nodeValue
            coords.strip()
            if not coord_check.match(coords):
                return
            lon, lat = coords.split(',')
            if lon and lat:
                return db.GeoPt(lat, lon)
        except (IOError, ExpatError) as e:
            return

#solution:

from xml.dom import minidom

def get_coords(xml):
	d = minidom.parseString(xml)
	coords = d.getElementsByTagName("gml:coordinates")
	if coords and coords[0].childNodes[0].nodeValue:
		lon, lat = coords[0].childNodes[0].nodeValue.split(',')
		return lat, lon
