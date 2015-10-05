#!/usr/bin/python


# cbr2ecbformat.cgi Converts XML file with currency exchange rates
# from www.cbr.ru to www.ecb.int XML format.
# All rates are recalculated to emulate ECB's data.
# RUB rate is added, but EUR removed.
#
# Copyright (C) 2011 Vasily Eremenko <vasily.eremenko@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


passwd = "abc123"; # WARNING! Change this pass to anything You want! This is security pass!
# This password should be the same here and at convertECB.php

import os;
import sys;
import xml.dom.minidom;
import httplib;

"""
retrieve_data() returns string, representing XML from cbr.ru
"""
def retrieve_data() :
    # Retrieve data from www.cbr.ru
    conn = httplib.HTTPConnection("www.cbr.ru")
    conn.request("GET", "/scripts/XML_daily.asp")
    r = conn.getresponse()
    if r.reason != "OK" :
        # Error occured during data retrieving!
        sys.stderr.write("Error occured during data retrieving!\n");
        sys.exit(1);
    d = r.read();
    return d;

"""
parse_data() parsing from_cbr
"""
def parse_data(from_cbr) :
    doc = xml.dom.minidom.parseString(from_cbr);
    return doc;

"""
convert_date() convert date from cbr to ecb format
"""
def convert_date(cbrdate) :
    d = cbrdate[:2];
    m = cbrdate[3:5];
    y = cbrdate[6:];
    retval = y + "-" + m + "-" + d;
    return retval;
"""
get_cbr_rate() returns cbr.ru rate for given currency as float
"""
def get_cbr_rate(node) :
    val = node.getElementsByTagName("Value")[0];
    nom = node.getElementsByTagName("Nominal")[0];
    val = val.firstChild.data;
    nom = nom.firstChild.data;
    val = val.replace(",", ".");
    nom = nom.replace(",", ".");
    val = float(val);
    nom = float(nom);
    retval = val/nom;
    return retval;

"""
get_euro_cbr_rate() returns cbr.ru rate of Euro as float
"""
def get_euro_cbr_rate(root) :
    nodes = root.getElementsByTagName("Valute");
    for node in nodes :
        curCode = node.getElementsByTagName("CharCode")[0];
        curCode = curCode.firstChild.data;
        if curCode == "EUR" :
            return get_cbr_rate(node);
    # If Euro rate was not found--- ERROR!
    sys.stderr.write("Error: Euro rate was not found at cbr.ru data!\n");
    sys.exit(1);


"""
handle_cbr_currency() convert currency rate from cbr to ecb format
"""
def handle_cbr_currency(node) :
    curCode = node.getElementsByTagName("CharCode")[0];
    curCode = curCode.firstChild.data;
    if curCode == "EUR" :
        return ""; # Nothing to return
    cbr_rate = get_cbr_rate(node);
    ecb_rate = euro_cbr_rate / cbr_rate;
    retval = "\t\t\t<Cube currency='%s' " % curCode;
    retval += "rate='%s'/>\n" % str(ecb_rate);
    return retval;




# Pass check
if not "QUERY_STRING" in os.environ :
    sys.stderr.write("Error: Unauthorized request of rates!\n");
    sys.exit(1);

if os.environ["QUERY_STRING"] != ("pass=" + passwd) :
    sys.stderr.write("Error: Unauthorized request of rates!\n");
    sys.exit(1);


# Print CGI header
print "Content-Type: text/xml;"
print "";

# Retrieve data
cbrdata = retrieve_data();
cbrdoc = parse_data(cbrdata);
cbr_root = cbrdoc.documentElement;

# ECB XML header
as_ecb = """<?xml version="1.0" encoding="UTF-8"?>
<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01" xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
	<gesmes:subject>Reference rates</gesmes:subject>
	<gesmes:Sender>
		<gesmes:name>European Central Bank</gesmes:name>
	</gesmes:Sender>
	<Cube>
"""

# Once more level
cbrdate = cbr_root.getAttribute("Date");
ecbdate = convert_date(cbrdate);
tmp = "\t\t<Cube time='%s'>\n" % ecbdate;
as_ecb += tmp;

# Get EUR rate in RUB
euro_cbr_rate = get_euro_cbr_rate(cbr_root);

# Generate contents
nodes = cbr_root.getElementsByTagName("Valute");
for node in nodes :
    as_ecb += handle_cbr_currency(node);

# Add RUB rate
as_ecb += "\t\t\t<Cube currency='%s' " % "RUB";
as_ecb += "rate='%s'/>\n" % str(euro_cbr_rate);

# Close tags
as_ecb += "\t\t</Cube>\n";
as_ecb += "\t</Cube>\n";
as_ecb += "</gesmes:Envelope>";

print as_ecb;

