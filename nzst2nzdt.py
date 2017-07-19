# Author James O'Brien 01/07/2015
# Help from Kristian, Chris, PPG (Peters Python Group)
# Script to convert time to daylight savings.
#
# Limitations:
# Will print error "January (Next Year Value) not found" if:
#   1) The input file is based on a calander year and the December 31st value is > 2300
#   2) The input file is based on a financial year and the last date entry is > 2300.
# In both instances the value will be removed from the output file as it wouldn't be correct in the calander type.
#
#V.1: Release
#V.1.1: Minor changes to conform to LINZ standards, removed need to specify file extension


import sys
import os
from datetime import datetime,tzinfo,timedelta
import calendar
import pytz
import xml.etree.ElementTree as ET
import xml.dom.minidom

#Designated custom TZ. Pulled from SX (not mine).

class FixedOffset(tzinfo):
    """Fixed offset in minutes: `time = utc_time + utc_offset`."""
    def __init__(self, offset):
        self.__offset = timedelta(minutes=offset)
        hours, minutes = divmod(offset, 60)
        #NOTE: the last part is to remind about deprecated POSIX GMT+h timezones
        #  that have the opposite sign in the name;
        #  the corresponding numeric value is not used e.g., no minutes
        self.__name = "<%+03d%02d>%+d" % (hours, minutes, -hours)
    def utcoffset(self, dt=None):
        return self.__offset
    def tzname(self, dt=None):
        return self.__name
    def dst(self, dt=None):
        return timedelta(0)
    def __repr__(self):
        return "FixedOffset(%d)" % (self.utcoffset().total_seconds() / 60)

tree = ET.parse(raw_input("Input .xml filename (reads for initial conversion) :")+".xml")
root = tree.getroot()

xml = xml.dom.minidom.parse(raw_input("Input .xml filename again (reads for correct formatting) :")+".xml")
pretty_xml_as_strong = xml.toprettyxml()

root.tag
root.attrib

nzst=pytz.timezone("Pacific/Auckland")
dtformat="%Y %B %d %H %M"
insertlist=[]
for month in root.findall(".//Month"):
    monthname,year=month.get("Name").split()
    for day in month.findall("Day"):
        dayno=day.get("Num")
        for hilo in day.findall("HiLo"):
            time=hilo.find("Time").text
            hour=time[:2]
            min=time[2:]
            dt=datetime.strptime(" ".join((year,monthname,dayno,hour,min)),dtformat)
            dt=dt.replace(tzinfo=FixedOffset(12*60))
            dt2=dt.astimezone(nzst)
            if str(dt) == str(dt2):
                continue
            newtime=dt2.strftime("%H%M")
            hilo.find("Time").text=newtime
            if newtime.startswith("00"):
                day.remove(hilo)
                newmonth=dt2.strftime("%B %Y")
                newday=str(dt2.day)
                search=".//Month[@Name='"+newmonth+"']/Day[@Num='"+newday+"']"
                newparent=root.find(search)
                if newparent is None:
                    print "Cannot find parent for",newday,newmonth
                else:
                    insertlist.append((newparent,hilo))

for newparent,hilo in insertlist:
    newparent.insert(0,hilo)

#replaces 'Local Std Time' with 'Local Std or Daylight Time'.
for elem in root.getiterator():
    if elem.text:
        elem.text = elem.text.replace("Local Std Time", "Local Std or Daylight Time")
    if elem.tail:
        elem.tail = elem.tail.replace("Local Std Time", "Local Std or Daylight Time")

tree.write(raw_input("Output xml filename :")+".xml")
