from bs4 import BeautifulSoup
from urllib.request import urlopen as uReq
import json
import csv
import sys

''''
Gianluca Minardi and Clayton North 

In this project we allow the user to find financial info about companies in a quick and efficient manner.
We scrape a bunch of financial info from yahoo finance and then find out if a company is a buy.
We then put all this info in a csv file. 

User can chose to scrape company's individually, 
Scrape all fortune 500 companies 
Or scrape all 6000+ tkrs we have access too.

NOTE: We pull tkr info from two files:
Fortune500-public.csv 
stock-names.csv 
THEY MUST BE IN SAME FOLDER AS CODE SO THINGS WORK!!!
'''
def read_tkrs(filename):
    '''
    Reads tiker- compname from a csv file and returns them into a dict
    :param filename:stock-names.csv (string)
    :return: compdic--> Compname:: TKR
    '''
    compdict = {}
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            for item in row:
                # tkr - name
                comp_info = item.split('-')
                #account for comps with - in names
                if len(comp_info) == 2:
                    #name::tkr
                    compdict[comp_info[1].strip()] = comp_info[0].strip()
                elif len(comp_info) == 3:
                    name = comp_info[1] + comp_info[2]
                    compdict[name.strip()] = comp_info[0].strip()

    return compdict

def search_tkr(name):
    '''
    User inputs a company name and then returns tkr from csv file
    :param compname:
    :return: tkr--> string
    '''


    base = read_tkrs('stock-names.csv')
    keys = base.keys()
    results = []
    for key in keys:
        if name in key.lower():
            results.append(key)

    if len(results) == 0:
        print("Comp not found")
        #error with companies that do not exist.
        return "Not Found"

    if len(results) ==1:
        #print(base [results[0]])
        return base [results[0]]

    else:
        #FIX target ISSUE
        print('All names including ' + name + ' are')
        print(results)
        chosen = input('Type exact name, given choices above ').lower()
        for name in results:
            if name.lower() == chosen:
                return base [name]

        print("Error")
        return "Not found"


        #return base [results[0]]

def set_main_url(name):
    '''
    Sets url (main page) to be searched by yahoo based on a tkr
    Should be used with search_tkr
    :param name: string tkr to be searched
    :return: yahoo url
    '''

    if name == 'Not Found':
        print('Nothing found')
        return
    else:
        url = "https://finance.yahoo.com/quote/" + name
        #print(url)
        return url

def get_tkrs(url):
    '''
    WEBISTE DOES NOT WORK
    From https://stockanalysis.com/stocks/  get tkr name and company name
    :param url: STRING
    :return tkr_dict--> NAME:TKR
    '''

    # open connection, grab page
    uclient = uReq(url)
    page_html = uclient.read()
    uclient.close()

    soup = BeautifulSoup(page_html, "html.parser")

    names = soup.find_all(class_="no-spacing")

    print(names)

def scrapeMainInfo(url,tkr):
    '''Scrapes certain finatial metrics from yahoo finance page using beautiful soup
    Args: url- for American companies, Example--https://finance.yahoo.com/quote/AAPL/
          tkr-- tkr to be searched (only have this so can appear in spreadsheet)
    Returns: list of floats with specific info for specific url.
    [tkr,curr, open, P/E, EPS, MKTCAP]

    '''


    try:
        #open connection, grab page
        uclient = uReq(url)
        page_html = uclient.read()
        uclient.close()
        soup = BeautifulSoup(page_html, "html.parser")
        span = soup.find_all("span")
        #print(soup)
        #currprice
        curr = soup.find_all(class_="Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)")
        #get rid of commas
        curr_price1 = curr[0].string
        curr_price = float(curr_price1.replace(",",""))

        td = soup.find_all('span', class_="Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)")
        #print(td)

        nums = soup.find_all('table',class_= "W(100%)")
        #print(nums)
        '''Sourcery to get elements I want from page
        '''
        main_info = []
        for element in nums:
            for e in element:
                for k in e:
                    for m in k:
                        main_info.append(m.string)

        #print(main_info)
        # get elements I want.
        metrics = []
        metrics.append(tkr)
        count = 0
        open = 0
        metrics.append(curr_price)
        #things are always in same sport
        #open
        metrics.append(float(main_info[3].replace(",","")))
        #P/E
        metrics.append(float(main_info[21].replace(",","")))
        #EPS
        metrics.append(float(main_info[23].replace(",","")))
        #mktcap (string)
        metrics.append(main_info[17])

        return metrics
    except:
        try:
            print('Error with website ' + url )
            return [tkr,'n/a','n/a','n/a','n/a', 'n/a']
        except:
            print('Error' )
            return ['n/a','n/a','n/a','n/a','n/a', 'n/a']

def send_main_to_excel(file,dict_data):
    '''
    Wrties a formatted csv file.
    Also sends mkt cap as a float
    Then calulates shrs outsdanding
    :param file: string with file name
    :param dict_data: list with all metrics (should cone from scrapeMainInfo function
    :return: nothing
    '''
    column_names = ['Tkr','Current', 'Open', 'P/E', 'EPS', 'MktCap ($mm)', "shrs_outs (mm)"]

    mktcap = dict_data[-1]


    #deal with shrs outstanding
    #have set this num to 'millions"
    if mktcap[-1] == "M":
        dict_data [-1] = float(mktcap[:-1])
    elif mktcap[-1] == "B":
        dict_data[-1] = float(mktcap[:-1])*(10**3)
    elif mktcap[-1] == "T":
        dict_data[-1] = float(mktcap[:-1])*(10**6)

    #get shrs outs
    shrs_outs = dict_data[-1]/dict_data[1]
    dict_data.append(shrs_outs)

    print('saved file named' + file)
    with open(str(file),"w",newline='') as f:
        #set row names
        writer = csv.writer(f)
        writer.writerow(column_names)
        writer.writerow(dict_data)

def scrape_yahoo_BS(url):
    '''
    Scrapes certain finatial metrics from yahoo BS page using beautiful soup
    Args: url- for American companies, Example--https://finance.yahoo.com/quote/WMT/balance-sheet?p=WMT
          tkr-- tkr to be searched (only have this so can appear in spreadsheet)
    Returns: list of floats with specific info for specific url.
    '''
    try:
        #open connection, grab page
        uclient = uReq(url)
        page_html = uclient.read()
        uclient.close()

        soup = BeautifulSoup(page_html, "html.parser")
        fin_table = soup.find_all(class_="D(tbrg)")
        table_head = soup.find_all(class_= 'D(tbhg)')

        #get lastet yahoo balance sheet
        dates = []
        for item in table_head:
            for a in item:
                for b in a:
                    dates.append(b.string)
        #print(dates)
        latest = dates[1]

        #Get big picture bs_info
        bs_info = []
        asset = soup.find_all(class_="Ta(c) Py(6px) Bxz(bb) BdB Bdc($seperatorColor) Miw(120px) Miw(140px)--pnclg D(tbc)")
        for item in asset:
            bs_info.append(item.string)   #skips middle column -->y0,y2,y0,y2

        total_assets = bs_info [0].replace(',','')
        total_debt = bs_info[-8].replace(',','')
        total_liab = bs_info [2].replace(',','')
        net_debt = bs_info [-6].replace(',','')
        tang_bv = bs_info [16].replace(',','')
        #print(bs_info)


        #put in mm$
        wanted = []
        try:
            wanted.append(float(total_assets)/1000)
        except:
            wanted.append("n/a")
        try:
            wanted.append(float(total_liab)/1000)
        except:
            wanted.append("n/a")
        try:
            wanted.append(float(total_debt) / 1000)
        except:
            wanted.append("n/a")
        try:
            wanted.append(float(net_debt)/1000)
        except:
            wanted.append("n/a")
        try:
            wanted.append(float(tang_bv)/1000)
        except:
            wanted.append("n/a")

        return wanted
    except:
        try:
            print('Error with website ' + url)
            return ['n/a','n/a','n/a','n/a','n/a']
        except:
            print('Error with website ')
            return ['n/a','n/a','n/a','n/a','n/a']





    '''
    for item in fin_table:
        for a in item:
            for b in a:
                for c in b:
                    print(c.string)
    '''

def set_bs_url(name):
    '''
    Sets url (finance page) to be searched by yahoo based on a tkr
    Should be used with search_tkr
    :param name: string tkr to be searched
    :return: yahoo url
    '''

    if name == 'Not Found':
        print('Nothing found')
        return
    else:
        url = "https://finance.yahoo.com/quote/" + name +"/balance-sheet?p=" + name
        #print(url)
        return url
def join_info(main_info,bs_info):
    '''
    Joins both lists of scrapped infor for a particular stock into proper format
    :param main_info:
    :param bs_info:
    :return: all-->list
    '''

    #deal with mkt cap 't/b' issue
    mktcap = main_info[-1]

    if mktcap[-1] == "M":
        main_info[-1] = float(mktcap[:-1])
    elif mktcap[-1] == "B":
        main_info[-1] = float(mktcap[:-1])*(10**3)
    elif mktcap[-1] == "T":
        main_info[-1] = float(mktcap[:-1])*(10**6)

    # get shrs outs
    try:
        shrs_outs = main_info[-1] / main_info[1]
        main_info.append(shrs_outs)
    except:
        main_info.append('n/a')

    #determine if buy
    bv_p_share = is_buy(main_info,bs_info)
    buy = 0
    try:
        if main_info[1]<=bv_p_share:
            buy = 1
    except:
        buy = 0

    all = main_info+ bs_info
    all.append(bv_p_share)
    all.append(buy)

    return all
def send_to_excel(everything):
    '''
    Wright stock info to excel file (determined by user)
    args:all--> list of list list with all a stocks info
    :return:
    '''

    file = input('Name file that will be saved \n')

    column_names = ['Tkr', 'Current', 'Open', 'P/E', 'EPS', 'MktCap ($mm)', "shrs_outs (mm)", 'Total Assets',
                    'Total_liab', 'Total Debt', 'Net_debt', 'Tang BV', 'BV/SHARE', 'Is_Buy']

    with open(str(file),"w",newline='') as f:
        #set row names
        writer = csv.writer(f)
        writer.writerow(column_names)
        for item in everything:
            writer.writerow(item)
        print('saved file named' + file)

def send_main_and_bs_to_excel(file,dict_data,bs_list):
    '''
    Does same as send main to excel, but also sends BS info
    :param file:
    :param dict_data:
    :return:
    '''

    column_names = ['Tkr','Current', 'Open', 'P/E', 'EPS', 'MktCap ($mm)', "shrs_outs (mm)",'Total Assets', 'Total_liab', 'Total Debt', 'Net_debt', 'Tang BV','BV/SHARE', 'Is_Buy']

    mktcap = dict_data[-1]
    #deal with shrs outstanding
    #have set this num to 'millions"
    if mktcap[-1] == "M":
        dict_data [-1] = float(mktcap[:-1])
    elif mktcap[-1] == "B":
        dict_data[-1] = float(mktcap[:-1])*(10**3)
    elif mktcap[-1] == "T":
        dict_data[-1] = float(mktcap[:-1])*(10**6)

    #get shrs outs
    shrs_outs = dict_data[-1]/dict_data[1]
    dict_data.append(shrs_outs)

    bv_p_share = is_buy(dict_data,bs_list)

    buy = 0
    if dict_data[1]<=bv_p_share:
        buy = 1



    all = dict_data + bs_list
    all.append(bv_p_share)
    all.append(buy)
    with open(str(file),"w",newline='') as f:
        #set row names
        writer = csv.writer(f)
        writer.writerow(column_names)
        writer.writerow(all)
        print('saved file named' + file)
def is_buy(main_info, bs_info):
    '''
    Determines if a stock is buy based on metrics using values
    If error, returns 0
    :param main_info: list from main scrape func
    :param bs_info: list from bs scrape func
    :return:
    '''

    all = main_info + bs_info
    try:
        bv_p_sh = all[-1]/all[6]
    except:
        bv_p_sh = 0

    return  bv_p_sh



#a = scrapeMainInfo('https://finance.yahoo.com/quote/AAPL?p=AAPL&.tsrc=fin-srch')

#send_main_to_excel('dogs.csv',a)

#get_tkrs('https://stockanalysis.com/stocks/')


#sread_tkrs('stock-names.csv')
def call_single():
    '''
    order of funcitons that works for single stock name
    :return:
    '''
    name = input('Insert Company name\n').lower()
    tkr = search_tkr(name)
    url = set_main_url(tkr)
    bsurl = set_bs_url(tkr)
    info = scrapeMainInfo(url,tkr)
    bs_info = scrape_yahoo_BS(bsurl)
    #send_main_to_excel('test1.csv',info)
    send_main_and_bs_to_excel('test2.csv',info,bs_info)

#scrape_yahoo_BS('https://finance.yahoo.com/quote/WMT/balance-sheet?p=WMT','aa')

#call_single()

def call_many():
    '''
    Order of funcitons so user can call company 1 by 1 and send info to excel sheet
    :return:
    '''

    name = input('Insert Company name. Insert "n" to create file\n').lower()
    complete_info = []
    while name != "n":
        tkr = search_tkr(name)
        url = set_main_url(tkr)
        bsurl = set_bs_url(tkr)
        info = scrapeMainInfo(url, tkr)
        bs_info = scrape_yahoo_BS(bsurl)
        all_info = join_info(info,bs_info)
        complete_info.append(all_info)
        name = input('Insert Company name. Insert "n" to create file\n').lower()

    send_to_excel(complete_info)

#call_many()
#get_tkrs('https://stockanalysis.com/stocks/')

def find_all_our_tkrs(filename):
    '''
    Scrapes through excel file with all our comp tkrs and returns list with all of them
    MORE THAN 6000 TKRS IN LIST
    :return: list with all possible tkrs.
    '''
    tkr_list = []
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            for item in row:
                # tkr - name
                comp_info = item.split('-')
                tkr = comp_info[0].strip()
                tkr_list.append(tkr)
    return tkr_list

def find_fortune_500_tkrs(filename):
    '''
    Gets tkrs from fortune 500 data set and returns list of tkrs
    Actually only 454 DATA SET IS A LIEEE!!!!
    :param filename:
    :return:
    '''
    tkr_list = []
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            tkr = row[1].strip()
            tkr_list.append(tkr)
    return tkr_list
def scrape_all():
    '''
    order of funcitons so system scrapes eveything we have automatically
    :return:
    '''

    complete_info = []
    tkrs = find_all_our_tkrs('stock-names.csv')
    '''
    TEST OUT ON FST 10 COMPANIES WITH HAVE (ALL OBSCURE SO A BUNCH OF N/A
    for i in range (0,10):
        url = set_main_url(tkrs[i])
        bsurl = set_bs_url(tkrs[i])
        info = scrapeMainInfo(url, tkrs[i])
        bs_info = scrape_yahoo_BS(bsurl)
        all_info = join_info(info, bs_info)
        complete_info.append(all_info)
    '''
    #FOR ALL COMPANIES IN DATA SET, TAKES A MINUTE BUT WORKS :)
    for item in tkrs:
        url = set_main_url(item)
        bsurl = set_bs_url(item)
        info = scrapeMainInfo(url, item)
        bs_info = scrape_yahoo_BS(bsurl)
        all_info = join_info(info, bs_info)
        complete_info.append(all_info)
    send_to_excel(complete_info)
def scrape_fortune_500():
    complete_info = []
    tkrs = find_fortune_500_tkrs('Fortune500-public.csv')

    '''
    TEST WITH FST 10 COMPANIES
    for i in range(0, 10):
        url = set_main_url(tkrs[i])
        bsurl = set_bs_url(tkrs[i])
        info = scrapeMainInfo(url, tkrs[i])
        bs_info = scrape_yahoo_BS(bsurl)
        all_info = join_info(info, bs_info)
        complete_info.append(all_info)

    send_to_excel(complete_info)
    '''
    for item in tkrs:
        url = set_main_url(item)
        bsurl = set_bs_url(item)
        info = scrapeMainInfo(url, item)
        bs_info = scrape_yahoo_BS(bsurl)
        all_info = join_info(info, bs_info)
        complete_info.append(all_info)
    send_to_excel(complete_info)

if __name__ == '__main__':
    choice = input(' TYPE 1 TO SCRAPE COMPANY MANUALLY \n PRESS 2 TO SCRAPE ALL Fortune 500 Companies (Takes a little time to complete) \n PRESS 3 TO SCRAPE ALL 6000+ tkrs we have access too ** TAKES A LOT OF TIME TO COMPLETE\n')
    if choice == '1':
        call_many()
    elif choice == '2':
        scrape_fortune_500()
    elif choice == '3':
        scrape_all()
