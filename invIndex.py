from bs4 import BeautifulSoup, SoupStrainer
from collections import defaultdict
import unidecode
import requests
import json
import time
import sys
import os
from tabulate import tabulate
import pandas

dir_path = os.path.dirname(os.path.realpath(__file__))  #gets current working directory
urlCount = 0        #count total number of urls
visited = []        #array of visited urls
queue = []          #urls to visit
pageIndexer = {}    #index of pages, which document relates to which url
documents = {}      #contains the documents
fileLoaded = False  #ensures database is loaded 


#for demonstration purposes only, shows that each page is indexed
#during the build the indexes are stored in 'documents' 
def savePage(page, pageName):

    fileObject = {}     #object used to save file
    
    try:

        temp = '\indexData\\'
        fileName = dir_path+ temp+ str(pageName) +".txt"
    
        with open(fileName, 'w') as f:
    

            fileObject['indexes'] = pageName    #document name
            fileObject['data'] = page           #document data

            json.dump(fileObject, f)
            print("Page data saved in :",fileName)

    except:
         print("Save Failed")
    

def saveIndex(data):
    global pageIndexer
    fileObject = {}     #object used to save file

    try:
        with open("invertedIndex.txt", 'w') as f:
            fileObject['indexes'] = pageIndexer
            fileObject['data'] = data

            json.dump(fileObject, f)
        print("Save Successful")
    except:
        print("Save Failed")
    


def AnalyseText(mystring):
    #ensure is al unicode i.e. gets rid of accents
    mystring = unidecode.unidecode(mystring)

    #gets  rid of punctutation
    invalidCharacters = '''0123456789|!()-[]{};:'"\, <>./?@#$%^&*_~'''
    for character in mystring:
        if character in invalidCharacters:
            mystring = mystring.replace(character," ")

    #splits by space " "
    mystring = mystring.split()


    dict = {}
    for idx, word in enumerate(mystring):

    
        if word not in dict:

            #each word has word frequency and then position of word in the string
            dict[word] = 0

        dict[word] = dict[word] + 1

  

    return dict


def crawlPage(url):
    global queue
    global visited

    r = requests.get(url) #access the url

    soup = BeautifulSoup(r.content,'html.parser') #parse page
    soup = soup.find( "body") # get body of page
    soupMain = soup.find("section", {"class": "main row"}) #main content of page is held within 'mainrow' class

    #find all the links within the main section
    for a in soupMain.find_all('a', href=True): 

        #ignore 'edit' links 
        if ("edit" not in (a.text).lower() ) and ("edit" not in (a['href']).lower() ):

            # ignore visited links + queued links as well as iso links as they point to the same pages 
            if ("iso" not in (a['href']).lower() ) and (a['href'] not in visited) and (a['href'] not in queue):
                queue.append(a['href'])


    #get text from page and create index of words for page
    string = soupMain.get_text(separator="\n", strip=True)

    docInvertedIndex = AnalyseText(string)

    return docInvertedIndex


#used to combine the index data from all of the documents
def combine(webData):
    #default dict type is needed
    combinedData = defaultdict(list)
    
    #want the items of each documents as they're the words on the page
    documents = webData.items()

    #for each docuemnt look at each word
    #and add the document name into the dict list using the word as a key 
    for key, document in documents:
        for k,v in document.items():
            tempString = key,v
            combinedData[k].append(tempString)

    #save all the data
    saveIndex(combinedData)


def crawlSite(urlList):
    global urlCount
    global pageIndexer
    global documents
    global fileLoaded
    global visited

    #loops through all of the urls in list
    for key, url in enumerate(urlList):

        print("doc_"+str(urlCount)+" : "+str(url) )

        docName = "doc_"+str(urlCount)
        pageIndexer[docName]  = str(url)

        visited.append(url) #adds to visited list
        queue.remove(url)  #removes from queue

        fullUrl = "http://example.python-scraping.com" + url
        documents[docName] = crawlPage(fullUrl)  #crawl the page

        savePage(documents[docName],docName)  #saves page as txt to show how the inverted index is built

        print("Visited: ", len(visited) )
        print("Left in queue: ", len(queue) )

        print("\n\n")

        urlCount = urlCount + 1
        time.sleep(5)



def build():

    #starting url
    url = "http://example.python-scraping.com/"
    
    r = requests.get(url)
    #get content from body -> class 'main row'
    soup = BeautifulSoup(r.content,'html.parser')
    soup = soup.find( "body")
    soupMain = soup.find("section", {"class": "main row"})

    #find all links
    for a in soupMain.find_all('a', href=True):
        if ("edit" not in (a.text).lower() ) and ("edit" not in (a['href']).lower()  ):
            queue.append(a['href'])

    #while the queue is not empty keep crawling the site
    while queue:
        crawlSite(queue)

    #once site has been crawled combine all of the indexes
    combine(documents)

    print("Inverted Index Build Successful")

def loadData():
    global pageIndexer
    global documents
    global fileLoaded

    #attempt to open invertedIndex
    try:
        with open("invertedIndex.txt") as f:
            #data stored as dict in txt
            allData = json.load(f)

            #contains the document names and the urls they correpsond to 
            pageIndexer = allData['indexes']

            #data contains list of words and documents
            documents = allData['data']

        fileLoaded = True
        print("Loading Successful")
   


    except FileNotFoundError:
        print("\nInverted Index File not found! \nEnsure it's in your cunrrent directory.\nUse the 'build' command to create one.")

    except:
        print("Loading Failed")
     

def userInput():

    fromUser = input(">>>")
    terms = ['build','load','print','find','help','exit']

    words = fromUser.split(" ")
    word1 = words[0]

    #ensures first word is valid command 
    if word1 in terms:
        return fromUser
    else:
        print("use 'help' to get extra information")
        fromUser = userInput()

        return fromUser

#used to print inverted index of various words
def printFunc(words):

    if fileLoaded == False:
        print("Database file not  loaded")
        return

    elif len(words) > 2:
        print("Only one search term is accepted for this command!(No extra spaces either)")

    elif(len(words)<2):
        print("Please add search term for example '>>> print Peso'")

    else:
        searchTerm = words[1]

    results = []
    #checks if word is in db
    if(searchTerm in documents.keys()):
        for document in documents[searchTerm]:
            temp = []
            temp.append(document[0])
            temp.append(document[1])
            results.append(temp)
        print(tabulate(results,headers=['Doc','Frequency'], tablefmt="pretty"))
    else:
        print("Unable to find word")


#used to search for words in the db 
def find(words):

    if fileLoaded == False:
        print("Database file not  loaded")
        return

    elif(len(words)<2):
        print("Please add search term for example '>>> find Area'")

    else:

        validWords = []  #checks which words given are valid/in the db 
        counter = 1  #counter set to 1 to avoid counting the "find" word in the command e.g. "find Area" 
        while counter < len(words):

            if words[counter] != " " and words[counter] != "" and  words[counter] != None:
                searchTerm = words[counter]

                if(searchTerm in documents.keys()):
                    validWords.append(searchTerm)
                else:
                    print("Unable to find '" + searchTerm + "' in the database")

            counter = counter + 1



        numOfValidWords = len(validWords)

        if(numOfValidWords>0):
            ranking = {}
            for word in validWords:

                for document in documents[word]:

                    docName = document[0]
                    if docName not in ranking:
                        ranking[docName] = {}

                        fullURl = "http://example.python-scraping.com" + str(pageIndexer[docName])
                        ranking[docName]['url'] = fullURl

                        ranking[docName]['counter'] = 1
                        ranking[docName]['frequency'] = document[1]

                    else:
                        ranking[docName]['counter'] = ranking[docName]['counter'] + 1
                        ranking[docName]['frequency'] = ranking[docName]['frequency'] +  document[1]


            res = sorted(ranking.items(), key = lambda x:(x[1]['counter'],x[1]['frequency']), reverse=True)

            results = {}
            for x in res:
                docName = x[0]
                results[docName] = {}
                results[docName]['url'] = x[1]['url']
                results[docName]['counter'] = str(x[1]['counter']) + " of " + str(numOfValidWords)
                results[docName]['frequency'] = x[1]['frequency']

            print("Searching...")
            loop = 0
            while loop<2:
                blah="\|/-\|/-"
                for l in blah:
                    sys.stdout.write(l)
                    sys.stdout.flush()
                    sys.stdout.write('\b')
                    time.sleep(0.1)
                loop+=1


            df = pandas.DataFrame(results)
            print(tabulate(df.T, headers=['Doc','URL','Words Found','Frequency'], tablefmt="pretty"))



def client():
    global documents
    global pageIndexer

    folder = dir_path + "\indexData"
    try:
        os.mkdir(folder)
        print("Directory " , folder ,  " Created ")
        print("It is used to store the index files for the crawler. Folder can be deleted once built")
    except FileExistsError:
        print("Directory " , folder ,  " already exists")

    while True:
        terms = []
        print("Use 'build','load','print','find','help','exit'")
        print("Or use for 'help' for extra info")
        uInput = userInput()

        words = uInput.split(" ")
        word1 = words[0]

        if word1 == 'build':
            print("Index saved at end, do not kill!")
            print("building...")
            build()
        elif word1 == 'load':
            print('loading...')
            loadData()

        
        elif word1 == 'print':
            printFunc(words)

        elif word1 == 'find':
            find(words)
        

        elif word1 == 'help':
            print("Possible commands 'build','load','print','find','help','exit' ")
            print('''\n\n******** build ******** \nThis command instructs the search tool to crawl the website, build the index, and save the resulting index into the file system. For simplicity you can save the entire index in one file.\n
******** load ********
This command loads the index from the file system. Obviously, this command will only work if the index has previously been created using the ‘build’ command.
\n                    
******** print ********
This command prints the inverted index for a particular word, for example:
    >>> print Peso
will print the inverted index for the word ‘Peso’
  \n                  
******** find ********
This command is used to find a certain query phrase in the inverted index and returns a list of all
pages containing this phrase, for example:
    >>> find Dinar
will return a list of all pages containing the word ‘Dinar’, while
    find Area Afghanistan
will return all pages containing the words ‘Area’ and ‘Afghanistan’.
''')
        elif uInput == 'exit':
            exit()


client()

