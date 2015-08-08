#!/usr/bin/python

import BeautifulSoup
import cookielib
import datetime
import json
import mechanize
import os
import re
import subprocess
import sys
import time
import urllib
import urlparse

# Create .airtricitybilldownload in your home directory like this:
# { "username": "user@example.com", "passsword": "letmein" }
with open(os.path.expanduser('~/.airtricitybilldownload')) as fp:
  config = json.load(fp)

if len(sys.argv) > 1:
  os.chdir(sys.argv[1])

# Browser
br = mechanize.Browser()
bill = mechanize.Browser()

# Browser options
br.set_handle_robots(False)
bill.set_handle_robots(False)

# Want debugging messages?
def debug():
  br.set_debug_http(True)
  br.set_debug_responses(True)
  bill.set_debug_http(True)
  bill.set_debug_responses(True)

cj = mechanize.CookieJar()
br.addheaders = [('User-Agent', 'airtricitybilldownload/0.1')]
br.set_cookiejar(cj)
bill.addheaders = br.addheaders
bill.set_cookiejar(cj)

# Index - Get php session cookie
br.open('https://my.sseairtricity.com/oss_web/login.htm')

# Login
br.select_form(name='loginForm')
br.form['j_username'] = config['username']
br.form['j_password'] = config['password']

br.submit()

# Invoices
br.open('account-history.htm?paymentMode=billsOnly')

# Parse html and download pdfs
html = br.response().read()
soup = BeautifulSoup.BeautifulSoup(html)

for a in soup.find(id='acc-history').findAll('a'):

  bill.open(urlparse.urljoin(br.geturl(), a['href']))

  bill_html = bill.response().read()
  bill_soup = BeautifulSoup.BeautifulSoup(bill_html)

  bill_a = bill_soup.find(href=re.compile('^bill-pdf'))

  bill_href = bill_a['href']
  query = urlparse.urlparse(bill_href).query
  parts = urlparse.parse_qs(query)

  customer_id = bill_soup.find('input', {'name':'customerId'})['value']
  statement_date = datetime.datetime.strptime(parts['secondaryId'][0], '%Y%m%d')

  localPdf = 'airtricity-%s-%s.pdf' % (
      customer_id, statement_date.strftime('%Y-%m'))

  if os.path.exists(localPdf):
    continue

  print 'Fetching %s...' % localPdf

  pdf_data = bill.open(bill_href).read()

  with open(localPdf, 'wb') as f:
    f.write(pdf_data)
