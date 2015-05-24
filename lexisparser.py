import traceback
import re
from bs4 import BeautifulSoup

DOC_PATT = re.compile('\/dd\/results\/ResultsDocRenderer.+')
VALID_PATT = re.compile('(\/dd\/results\/ResultsDocRenderer.+&docNo=(\d+))(&hitNo.+)?')
def getDocUrls(cont, result_count):
    # Get the urls of the articles
    soup = BeautifulSoup(cont)
    
    total_found = soup.find('input', {'name': 'totalAnswersForAnswerSet'})['value']
    
    docs = []
    links = soup.find_all('a', href=DOC_PATT)
    
    for link in links:
        url = link['href']
        
        res = VALID_PATT.findall(url)
        if len(res) == 0:
            continue
            
        res = res[0]
        # This avoids duplicate links, and limits results
        if len(res[2]) == 0 and int(res[1]) <= result_count:
            title = link.text.strip()
            docs.append((url, title))
    
    return docs, total_found