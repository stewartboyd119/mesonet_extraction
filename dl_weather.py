"""
Example script that scrapes data from the IEM ASOS download service
"""
from __future__ import print_function
import json
import time
import datetime
import os
# Python 2 and 3: alternative 4
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

# Number of attempts to download data
MAX_ATTEMPTS = 6
# HTTPS here can be problematic for installs that don't have Lets Encrypt CA
SERVICE = "http://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?"


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

    #states = 'AK AL AR AZ CA CO CT DE FL GA HI IA ID IL IN KS KY LA MA MD ME MI MN MO MS MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY'
    # --- edit the line below to have the 2 letter abbreviation of the states for which you want to download.
    # --- Above is the full list if you forget the abbreviation for a states
    states = 'AK AL AR AZ CA CO CT DE FL GA HI IA ID IL IN KS KY LA MA MD ME MI MN MO MS MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY'
    
    # IEM quirk to have Iowa AWOS sites in its own labeled network
    out_dir = "python_output"
    try:
        os.mkdir(out_dir)
    except OSError:
        # directory probably is already created
        pass
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
            data = download_data(uri)
            outfn = '%s_%s_%s_%s.txt' % (network, faaid, startts.strftime("%Y%m%d%H%M"),
                                      endts.strftime("%Y%m%d%H%M"))
            outfn = os.path.join(out_dir, outfn)
            out = open(outfn, 'w')
            out.write(data)
            out.close()


if __name__ == '__main__':
    main()