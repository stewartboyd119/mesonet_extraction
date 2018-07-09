"""
Example script that scrapes data from the IEM ASOS download service
"""
from __future__ import print_function
import json
import time
import datetime
from pprint import pprint
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


    #states = "CA IL WA FL TX"
    #ca = "CA"
    faaid_key = "faaid"
    sitename_key = "sitename"
    states2airports = {"CA": [{faaid_key: "LAX", sitename_key: "LOS ANGELES INTL"}],
              "IL": [{faaid_key: "MDW", sitename_key: "CHICAGO"}],
              "WA": [{faaid_key: "SEA", sitename_key: "SEATTLE-TACOMA INTL"}],
              "FL": [{faaid_key: "DAB", sitename_key: "DAYTONA BEACH RGNL"}],
              "TX": [{faaid_key: "HOU", sitename_key: "HOUSTON/WILL HOBBY"},
                     {faaid_key: "SAT", sitename_key: "SAN ANTONIO INTL"}]}

    state2site = {}
    # IEM quirk to have Iowa AWOS sites in its own labeled network

    for state in states2airports:
        airports = states2airports[state]
        network = "{}_ASOS".format(state)

        # Get metadata
        uri = ("https://mesonet.agron.iastate.edu/"
               "geojson/network/%s.geojson") % (network,)
        print("#" * 10)
        print(network)
        for airport in airports:
            faaid = airport[faaid_key]
            sitename = airport[sitename_key]
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