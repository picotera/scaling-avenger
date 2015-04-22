import re
import json
import os
import os.path
import helper
import logging
import time
import sys

# 3rd party libraries
import requests
from bs4 import BeautifulSoup

import pprint

import lexisparser

# BeautifulSoup made problems for large documents.
MAX_RECURSION = 3000
sys.setrecursionlimit(MAX_RECURSION)

HTML_STRUCTURE = '<html><head><meta charset="UTF-8"></head><body>%s</body>'

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36'}
OUTPUT_DIR = 'output\\binyamin\\'

# Update firstName, surName, newSourceDropdown
DEFAULT_PARAMS = {"additionalTerms1": "", "additionalTerms2": "", "additionalTerms3": "", "additionalTermsConnector1": "and", "additionalTermsConnector2": "and", "alertSelectedSubContType": "", "clientCodeMandatory": "false", "companiesDateSelector": "", "company_calendarUnit": "days", "company_day1": "", "company_day2": "", "company_month1": "", "company_month2": "", "company_numericUnit": "1", "company_year1": "", "company_year2": "", "connectorAnd": "and", "connectorOr": "or", "costCode": "", "costCodeType": "freeText", "currentLocale": "en_GB", "customSearchLabel": "Custom News", "dateSelector": "", "defaultNewsSrcCsi": "8399", "directorsDatesString": "", "dispatch": "", "dsCountrySelection": "", "dsDateSelection": "All", "editAlertOption": "", "firstName": "binyamin", "formID": "UK01PersonCheck", "legalDateOption": "-2|years", "legalDateSelector": "previous", "legalSourceDropdown": "All Legal", "legalSourceDropdownCountry": "PrsChkIntReviewSubContType|152864|Australian Law Journals, Combined;;PrsChkIntCasesSubContType|4318|Australian Commonwealth, State & Territory Case Law", "legalSourcesDateString": "", "legal_calendarUnit": "years", "legal_day1": "", "legal_day2": "", "legal_month1": "", "legal_month2": "", "legal_numericUnit": "2", "legal_year1": "", "legal_year2": "", "mode": "new", "newsDateOption": "-2|years", "newsDateSelector": "previous", "newsSourceDropdown": "8399,140952|English|All English Language News", "newsSourcesDateString": "", "news_calendarUnit": "years", "news_day1": "", "news_day2": "", "news_month1": "", "news_month2": "", "news_numericUnit": "2", "news_year1": "", "news_year2": "", "qlSrcInfoURI": "", "saveAlertFormBeanKey": "", "searchFormExpand": "true", "searchFormType": "PersonCheck", "selectedCostCodeType": "freeText", "showSrchInterPage": "false", "sources": "", "subContTypeCheckBoxes": ["PrsChkNegNewsSubContType|8399,140952|All English Language News", "PrsChkNewsSubContType|8399,140952|All English Language News", "PrsChkSanctionWarnSubContType|300840,347942|Sanctions and Actions;Autorit\u00e9 des march\u00e9s financiers - Commission des sanctions", "PrsChkAddnWatchListSubContType|286191,314048|Sanction Lists; Watchlists and Blacklists", "PrsChkFinraSubContType|169949,222852|Combined NYSE & NASD Disciplinary Decisions; Financial Industry Regulatory Authority (FINRA/NASD) Arbitration Awards", "PrsChkWorldComplianceSubContType|297582|World Compliance PEP List", "PrsChkInfo4CSubContType|286185|Politically Exposed Persons (PEP)", "", "PrsChkIntCasesSubContType|11059,360394,244212,163014,154616,290280,389359,268081,362711,4318,155410,388783,164604,5754,258623,394002,222698,244623,360688,360397,353584,148106,6760,375064,153132,163749|Federal & State Court Cases - After 1944, Combined ; UK Cases, Combined; All Hong Kong Case Law; Commonwealth and Irish Cases, Combined - Displayed by Date; Malaysia and Brunei Cases; International Court of Justice Decisions, Combined; Jurisprudence administrative; JurisData & Cours supr\u00c3\u00aames; In\u00c3\u00a9dit Cour d'appel; Australian Commonwealth, State & Territory Case Law; Canadian Cases; England & Wales Cases: Combined; EUR-Lex European Union Cases; European Court of Justice Cases Selected By Butterworths; Supreme Court of India Cases, Combined; International Human Rights Cases, Combined; World Trade Organization Dispute Settlement; ECHR Cases: 1960-2010*; ECHR Cases: 2011 to Current; Irish Cases, Combined; Supreme Court of Israel; Jurisprudencia de la Corte Suprema de Mexico - Mexican Caselaw; Northern Ireland Reported and Unreported Cases; Scots Cases Combined (UKRSCO); Butterworths South African Constitutional Law Reports; South Africa Tax Cases", "", "", "PrsChkIntAgencySubContType|164171,168607|Federal Agency Decisions, Combined ; State Administrative Agency Decisions, Combined", "", "", "", "PrsChkIntReviewSubContType|170663,152864,10763,159446|Law Reviews, CLE, Legal Journals & Periodicals, Combined; Australian Law Journals, Combined; UK Law Journals, Combined; Canadian Law Journals, Combined"], "submitButton": "Search", "surName": "netanyahu", "thresholdType": "search.common.threshold.off", "tpMaxSearchLimitReached": "false"}

PAGES = {'PrsChkNegNewsSubContType' : 'Negative News', # News - Negative news
         'PrsChkNewsSubContType' : 'All News', # News - All News
         'PrsChkSanctionWarnSubContType' : 'Sanctions & Watchlists', # Sanctions - Sanctions & Watchlists
         'PrsChkAddnWatchListSubContType' : 'Additional Watchlists', # Sanctions - Additional Watchlists
         'PrsChkFinraSubContType' : 'Finra Actions', # Santions - Finra Actions
         'PrsChkWorldComplianceSubContType' : 'World Compliance', # PEP - World Compliance
         'PrsChkInfo4CSubContType' : 'Info4C', # PEP - Info4C
         'PrsChkIntCasesSubContType' : 'Cases', # Legal - Cases
         'PrsChkIntAgencySubContType' : 'Agency Decisions', # Legal - Agency Decisions
         'PrsChkIntReviewSubContType' : 'Law Reviews',} # Legal - Law Reviews
         
MAX_ADDITIONAL_TERMS = 2 # The maximum number of additional terms
AND_CONNECTOR = 'and'
OR_CONNECTOR = 'or'
ADDITIONAL_TERM = 'additionalTerms%s'
ADDITIONAL_CONNECTOR = 'additionalTermsConnector%s'
         
MAIN_URL = 'http://www.lexisnexis.com'

class DuplicateFilter(object):
    OFF = 'search.common.threshold.off'
    HIGH = 'search.common.threshold.narrowrange'
    MODERATE = 'search.common.threshold.broadrange'

class Sources(object):
    ALL = 'All News, all languages'
   
    MAJOR_PUBLIC = 'Major World Publications (English)'
    MAJOR_PAPERS = 'Major World Newspapers (English)'
    UK_PUBLIC = 'UK Publications'
    US_NEWS = 'US News'
    ASIA_NEWS = 'Asia Pacific News'
    
    # By language
    ENGLISH_NEWS = 'All English Language News'
    NON_ENGLISH = 'All Non-English Language News'
    ARABIC = 'Arabic Language News'
    FRENCH_NEWS = 'French Language News'
    GERMAN_NEWS = 'German Language News'
    ITALIAN_NEWS = 'Italian Language News'
    SPANISH_NEWS = 'Spanish Language News'
    PORTUGUESE_NEWS = 'Portuguese Language News Combined'
    DUTCH_NEWS = 'Dutch Language News - Full Text'
    RUSSIAN_NEWS = 'Russian Language News (Cyrillic)'

def saveOut(name, cont):
    open(OUTPUT_DIR + name, 'w').write(cont.encode('utf8'))
    
class LexisNexis(object):
    
    def __init__(self):
        self.logger = helper.getLogger(logging.INFO)
        self.config = helper.Config()
        
        self.s = requests.session()
        self.s.verify = False
        
        self.s.headers = HEADERS
    
    def Login(self):
        ''' Login into dowjones '''
        form_url = '/dd'
        login_url = 'https://www.lexisnexis.com/dd/auth/srhandler.do'
        
        res = self.s.get(MAIN_URL + form_url)
        
        data = {
            'dispatch': 'signon',
            'originSignonForm': 'signonform',
            'webId': self.config.username,
            'password': self.config.password,
            'permanent': 'false',
        }
        res = self.s.post(login_url, data)
    
    def AddTerms(self, data, additional_terms, connectors):
    
        # Convert to tuple
        if type(additional_terms) == str:
            additional_terms = (additional_terms, )
        if type(connectors) == str:
            connectors = (connectors, )
        
        count = min(len(additional_terms), MAX_ADDITIONAL_TERMS)
        
        for i in xrange(count):
            connector = OR_CONNECTOR
            if i < len(connectors):
                connector = connectors[i]
            
            print 'Connector: %s, Term: %s' %(connector, additional_terms[i])
            data[ADDITIONAL_TERM %(i+1)] = additional_terms[i]
            data[ADDITIONAL_CONNECTOR %(i+1)] = connector
    
    def Query(self, first_name, last_name, additional_terms=(), connectors=(), source=Sources.ALL, duplicate_filter=DuplicateFilter.MODERATE):
        '''
        @param source: A source specification from Sources
        @param additional: Additional terms
        @type additional: list/tuple(str) or str
        @param connectors: The connectors between the terms. AND_CONNECTOR/OR_CONNECTOR, default or
        @type connectors: list/tuple(str) or str
        '''
        base_url = '/dd/auth/checkbrowser.do?t=%s&bhcp=1&bhqs=1'
        search_url = '/dd/search/submitForm.do'

        res = self.s.get(MAIN_URL + base_url %int(time.time() * 1000))
        
        soup = BeautifulSoup(res.text)
        
        form = soup.find('form', attrs = {'name': 'search_Form'})
        data = {}
        data.update(DEFAULT_PARAMS)
        
        data['thresholdType'] = duplicate_filter
        data['newsSourceDropdown'] = soup.find(id='newsSourcesSel').find(text=source).parent['value']
        data['firstName'] = first_name
        data['surName'] = last_name
        
        self.AddTerms(data, additional_terms, connectors)
        
        res = self.s.post(MAIN_URL + search_url, data)

        soup = BeautifulSoup(res.text)
        
        risb = soup.find('input', {'name':'risb'})['value'].strip()
        search_key = soup.find('input', {'name':'srchFormBeanKey'})['value'].strip()
        bean_key = soup.find('input', {'name':'formBeanKey'})['value'].strip()
        
        # Not sure why if needed
        #self.CountSearch(search_key)
        #self.ResClass(risb, bean_key)
        
        result_html = ''
        for page in PAGES:
            table = self.GetPage(page, search_key, bean_key)
            result_html += table
        
        docs = lexisparser.getDocUrls(result_html)
        
        i = 0
        for doc in docs:
            name = 'doc%s.html' %i
            cont = self.GetDocument(doc)
            
            saveOut(name, cont)
            print result_html.find(doc.replace('&', '&amp;'))
            result_html = result_html.replace(doc.replace('&', '&amp;'), name)
            i += 1
            
        saveOut('out.html', HTML_STRUCTURE %result_html)
            
    def GetPage(self, page, search_key, bean_key):
        print search_key, bean_key
        result_page = '/dd/results/ResultTabHandler.do?selectedTab=%s&selectedMainTab=&searchFormKey=%s&rsltListFormKey=%s&taggedValues=undefined&tertiaryTabSelected=&negnewsLvlSelected=0'
        
        res = self.s.post(MAIN_URL + result_page %(page, search_key, bean_key), 
                          {'focusTerms' : ''})
        
        table = lexisparser.getSearchResults(PAGES[page], res.text, self.config.result_count)
        
        return table

    def GetDocument(self, url):
        res = self.s.get(MAIN_URL + url)
        
        saveOut('temp.html', res.text)
        
        soup = BeautifulSoup(res.text)
        
        elem = soup.find(id='formReplicate').find(class_='resultsTopList')
        
        return elem.prettify()
        
def main():
    lexis = LexisNexis()
    lexis.Login()
    
    lexis.Query('binyamin', 'netanyahu', source = Sources.ALL, duplicate_filter = DuplicateFilter.MODERATE)
    
if __name__ == '__main__':
    main()
