import traceback
import re
from bs4 import BeautifulSoup

def getSearchResults(page, cont, result_count):
    ''' Get the html of the top search results '''
    print 'bla2'
    soup = BeautifulSoup(cont)
    total_found = soup.find('input', {'name': 'totalAnswersForAnswerSet'})['value']
    
    table = soup.find(id='resultsTable')
    if table == None: # No results
        return ''
    
    result = '<h1>%s: total %s</h1>' %(page, total_found)
    
    matches = soup.find(id='resultsTable').find_all('tr', recursive = False)[:result_count]
    for match in matches:
        result += match.prettify()
        
    return '<table>%s</table>' %result

IGNORE_PART = '&hitNo' # Ignore evertyhing from this point
DOC_PATT = re.compile('\/dd\/results\/ResultsDocRenderer.+')
def getDocUrls(cont):
    # Get the urls of the articles
    soup = BeautifulSoup(cont)
    
    docs = set()
    links = soup.find_all('a', href=DOC_PATT)
    
    for link in links:
        url = link['href']
        ignore = url.find(IGNORE_PART)
        if ignore != -1:
            url = url[:ignore]
        docs.add(url)
    
    return docs