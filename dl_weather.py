"""
Example script that scrapes data from the IEM ASOS download service
"""
from __future__ import print_function
import json
import time
import datetime
#import timedelta
# Python 2 and 3: alternative 4
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

# Number of attempts to download data
MAX_ATTEMPTS = 6
# HTTPS here can be problematic for installs that don't have Lets Encrypt CA
SERVICE = "http://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?"
#_SERVCE = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=PHX&data=metar&year1=2018&month1=6&day1=18&year2=2018&month2=6&day2=18&tz=Etc%2FUTC&format=onlycomma&latlon=no&direct=no&report_type=2

def download_data(uri):
    """Fetch the data from the IEM
    The IEM download service has some protections in place to keep the number
    of inbound requests in check.  This function implements an exponential
    backoff to keep individual downloads from erroring.
    Args:
      uri (string): URL to fetch
    Returns:
      string data
    """
    attempt = 0
    while attempt < MAX_ATTEMPTS:
        try:
            data = urlopen(uri, timeout=300).read().decode('utf-8')
            if data is not None and not data.startswith('ERROR'):
                return data
        except Exception as exp:
            print("download_data(%s) failed with %s" % (uri, exp))
            time.sleep(5)
        attempt += 1

    print("Exhausted attempts to download, returning empty data")
    return ""


def main():
    """Our main method"""
    # timestamps in UTC to request data for

    startts = datetime.datetime.today() - datetime.timedelta(days=1)
    endts = datetime.datetime.today() - datetime.timedelta(days=1)
    service = SERVICE + "data=metar&tz=Etc%2FUTC&format=onlycomma&latlon=no&direct=no&report_type=2&"
    service += startts.strftime('year1=%Y&month1=%m&day1=%d&')
    service += endts.strftime('year2=%Y&month2=%m&day2=%d&')

    '''
    1) Phoenix, AZ(KPHX)
    2) Colorado
    Springs, (KCOS)
    3) Fargo
    ND, (KFAR)
    4) Chicago
    Midway, (KMDW)
    5) Daytonna
    Beach, FL(KDAB)
    6) Dallas
    Love(KDAL)
    '''


    states = "AZ CO IL ND FL TX"
    # IEM quirk to have Iowa AWOS sites in its own labeled network
    networks = []
    for state in states.split():
        networks.append("%s_ASOS" % (state,))

    for network in networks:
        # Get metadata
        uri = ("https://mesonet.agron.iastate.edu/"
               "geojson/network/%s.geojson") % (network,)
        data = urlopen(uri)
        jdict = json.load(data)
        for site in jdict['features']:
            faaid = site['properties']['sid']
            sitename = site['properties']['sname']
            uri = '%s&station=%s' % (service, faaid)
            print(('Network: %s Downloading: %s [%s]'
                   ) % (network, sitename, faaid))
            print(uri)
            data = download_data(uri)
            outfn = '%s_%s_%s.txt' % (faaid, startts.strftime("%Y%m%d%H%M"),
                                      endts.strftime("%Y%m%d%H%M"))
            out = open(outfn, 'w')
            out.write(data)
            out.close()


if __name__ == '__main__':
    main()