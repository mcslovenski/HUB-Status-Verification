import pdftotext
import tkinter as tk
from tkinter.filedialog import askopenfilenames
import mechanize
from bs4 import BeautifulSoup
from datetime import datetime
import os


# create directories for logfiles to be categorized into
# agreement directory will contain logfiles for subcontractors for whom listed status and found status agreed
os.makedirs(os.path.join(os.path.curdir, 'agreement'), exist_ok=True)
# disagreement directory will contain logfiles for subcontractors for whom listed status and found status disagreed
os.makedirs(os.path.join(os.path.curdir, 'disagreement'), exist_ok=True)
# no_vendor_cmbl directory will contain logfiles for subcontractors that were not found in the CMBL search and thus their listed status cannot be confirmed or denied
os.makedirs(os.path.join(os.path.curdir, 'no_vendor_cmbl'), exist_ok=True)



## File Selection
#
# create tkinter interface object and withdraw standing interface
root = tk.Tk()
root.withdraw()

# call tk fileopener and convert returned file from tuple to list
filenames = askopenfilenames()
filenames = list(filenames)

# for each file in list of files selected to be opened in tk fileopener, run the full verification process process
for file in filenames:
    # convert pdf to text
    with open(file, "rb") as f:
        pdf = pdftotext.PDF(f)
    # write converted text to a txt file
    output = file[:-3] + "txt"
    with open(output, 'w', encoding='UTF-8') as f:
        f.write("".join(pdf))

    # initialize result routing counters to be printed at the end of each iteration (at the end of each file processed)
    agreement_counter = 0
    disagreement_counter = 0
    notFound_counter = 0



    ## Local File Parsing
    #
    #
    with open(output, 'r', encoding='UTF-8') as infile:
        # read converted text for txt file
        file_text = infile.readlines()

        # initialize list of subcontractors to be populated by all subcontractors listed on pdf
        subcontractors = []

        # read text line-by-line and identify lines that are rows of tables containing subcontractor information
        # each row that is identified for parsing execution represents a subcontractor so iteration is acting on each subcontractor
        for row in file_text:
            if "✔" in row:
                if "%" in row:
                    # split found subcontractor table row into column elements and whitespace
                    row = row.split("  ")

                    # remove whitespace elements from found subcontractor table row
                    row = [element for element in row if element]

                    # create subcontractor dictionary object from column elements
                    # initialize subcontractor dictionary
                    subcontractor = {}
                    # name of subcontractor
                    subcontractor['name'] = row[0].strip()
                    # Texas Vendor ID (VID) or federal EIN (EIN) of subcontractor
                    if "$" not in row[4]:
                        subcontractor['VID/EIN'] = row[4].strip()
                    # HUB status of subcontractor:
                    #   bool based on list position order of checkmark
                    if "Yes" in row[1]:
                        subcontractor['hub_status'] = False
                    else:
                        subcontractor['hub_status'] = True

                    # add inividual subcontractor dictionary to list of subcontractor dictionaries
                    subcontractors.append(subcontractor)
                    # print each subcontractor to the command line
                    print(subcontractor)



    # CMBL Search and Parsing
    #
    # for each subcontractor dictionary in the list of subcontractor dictionaries
    # perform search of the Texas Centralized Master Bidders List (CMBL) and create a dictionary that represents the subcontractor as a CMBL vendor
    # iteration also executes "Logging" process
    for subcontractor in subcontractors:
        # initialize Mechanize browser object
        br = mechanize.Browser()
        # set browser to ignore robots.txt files and to represent itself as a user-operated instance of Mozilla Firefox
        br.set_handle_robots(False)
        br.addheaders = [('User-agent', 'Mozilla/5.0')]
        # open browser to CMBL search address
        br.open("https://mycpa.cpa.state.tx.us/tpasscmblsearch/tpasscmblsearch.do")

        # select the CMBL Vendor Search form
        # br.form is now equal to this form
        br.select_form("tpassCmblSearchForm")
        # set all form fields to be editable
        br.form.set_all_readonly(False)

        # set "Search Type" to search all vendors in the CMBL
        searchType_control = br.form.find_control("searchType")
        searchType_control.value = ['All Vendors']

        # if VID number has been provided (not EIN), search by VID
        # else search by vendor name
        if subcontractor['VID/EIN'] is not None:
            # verify that VID number has been provided, not EIN
            if len(subcontractor['VID/EIN']) > 9:
                if "-" not in subcontractor['VID/EIN']:
                    # input VID in the VID search field
                    vendorVID_control = br.form.find_control("vendorId")
                    vendorVID_control.value = subcontractor['VID/EIN']
        else:
            # set the vendor name search condition to search for any vendor names that contain the listed subcontractor name
            #   to account for slight variations e.g. the addition of "Inc." in the CMBL listing
            vendorSearchType_control = br.form.find_control("vndrNameCond")
            vendorSearchType_control.value = ['contains']
            # input the listed subcontractor in the name search field
            vendorNameText_control = br.form.find_control("vendorName")
            vendorNameText_control.value = subcontractor['name']

        # submit search
        response = br.submit(id="search")

        # read search results into a Beautiful Soup object
        soup = BeautifulSoup(response, features='html5lib')
        # identify results table
        table_rows = soup.find_all('tr')
        # read top result into columns
        columns = table_rows[1].find_all('td')

        # create dictionary for vendor found in CMBL as a dictionary object derived from the columns object
        # initialize dictionary for found vendor as cmbl_vendor dictionary
        cmbl_vendor = {}
        # name of vendor from CMBL
        cmbl_vendor['name'] = columns[1].string
        # VID of vendor from CMBL
        cmbl_vendor['VID'] = columns[0].string
        # HUB status code of vendor from CMBL
        cmbl_vendor['hub_status_code'] = columns[-1].string
        # HUB status of vendor:
        #   bool based on comptroller HUB status codes
        #   only creates this key-value if vendor was found
        if cmbl_vendor['hub_status_code'] is not None:
            if cmbl_vendor['hub_status_code'][0]=='A':
                cmbl_vendor['hub_status'] = True
            else:
                cmbl_vendor['hub_status'] = False

        # print each vendor dictionary to the command line
        # vendors that were not found will have None values
        print(cmbl_vendor)



        ## logging
        #
        # perform comparison between the information listed about the subcontractor on the pdf and the information about the subcontractor pulled from the CMBL
        # categorize comparison results and write logfiles

        # set a variable to use in logfile creation
        # remove whitespace and characters disallowed in file names
        vendor_name = subcontractor['name']
        vendor_name = vendor_name.replace(',', '')
        vendor_name = vendor_name.replace('.', '')
        vendor_name = vendor_name.replace('/', '')
        vendor_name = vendor_name.replace('\\', '')
        vendor_name = vendor_name.replace('*', '')
        vendor_name = vendor_name.replace('<', '')
        vendor_name = vendor_name.replace('>', '')
        vendor_name = vendor_name.replace('?', '')
        vendor_name = vendor_name.replace(' ', '')

        # create the timestamp to use in file names and log content
        # format timestamp replacing whitespace and colons, and removing measurement under 1 second
        timestamp = str(datetime.now())
        timestamp = timestamp.replace(' ', '--')
        timestamp = timestamp.replace(':', '-')
        timestamp = timestamp[:-7]

        # create full file name as name of listed subcontractor plus the timestamp
        file_name = vendor_name + "--" + timestamp + ".txt"

        # set variables as full paths for logfiles to write to
        confirmed_logfile = os.path.join(os.path.curdir, 'agreement', file_name)
        disagreement_logfile = os.path.join(os.path.curdir, 'disagreement', file_name)
        notFound_logfile = os.path.join(os.path.curdir, 'no_vendor_cmbl', file_name)

        # if subcontractor was not found in CMBL search
        if 'hub_status' not in cmbl_vendor:
            # increment counter of subcontractors who could not be found in search
            notFound_counter += 1
            # write to logfile
            with open(notFound_logfile, 'w', encoding='UTF-8') as logfile:
                logfile.write(f"vendor name on subcontracting plan:\n    {subcontractor['name']}\n")
                logfile.write(f"vendor ID or EIN on subcontracting plan:\n    {subcontractor['VID/EIN']}\n")
                logfile.write(f"HUB status on subcontracting plan:\n    {subcontractor['hub_status']}\n\n")
                logfile.write("vendor not found in CMBL search\n")
                logfile.write(timestamp)
        # if subcontractor was found in CMBL but the listed HUB status and the HUB status found in CMBL are not equivalent
        elif subcontractor['hub_status'] != cmbl_vendor['hub_status']:
            # increment counter of subcontractors whose listed HUB status was refuted by results from CMBL search
            disagreement_counter += 1
            # write to logfile
            with open(disagreement_logfile, 'w', encoding='UTF-8') as logfile:
                logfile.write(f"vendor name on subcontracting plan:\n    {subcontractor['name']}\n")
                logfile.write(f"vendor name from CMBL search:\n    {cmbl_vendor['name']}\n")
                logfile.write(f"vendor ID or EIN on subcontracting plan:\n    {subcontractor['VID/EIN']}\n")
                logfile.write(f"vendor ID from CMBL:\n    {cmbl_vendor['VID']}\n")
                logfile.write(f"HUB status on subcontracting plan:\n    {subcontractor['hub_status']}\n")
                logfile.write(f"HUB status from CMBL:\n    {cmbl_vendor['hub_status_code']}\n\n")
                logfile.write("HUB status DISAGREEMENT\n")
                logfile.write(timestamp)
        # if subcontractor was found in CMBL and the listed HUB status and the status found in CMBL were equivalent
        else:
            # increment counter of subcontractors whose listed HUB status was confirmed by results from the CMBL
            agreement_counter += 1
            # write to logfile
            with open(confirmed_logfile, 'w', encoding='UTF-8') as logfile:
                logfile.write(f"vendor name on subcontracting plan:\n    {subcontractor['name']}\n")
                logfile.write(f"vendor name from CMBL search:\n    {cmbl_vendor['name']}\n")
                logfile.write(f"vendor ID or EIN on subcontracting plan:\n    {subcontractor['VID/EIN']}\n")
                logfile.write(f"vendor ID from CMBL:\n    {cmbl_vendor['VID']}\n")
                logfile.write(f"HUB status on subcontracting plan:\n    {subcontractor['hub_status']}\n")
                logfile.write(f"HUB status from CMBL:\n    {cmbl_vendor['hub_status_code']}\n\n")
                logfile.write("HUB status AGREEMENT\n")
                logfile.write(timestamp)

    # print counters to command line on completion of each file iteration
    print(str(agreement_counter + disagreement_counter + notFound_counter) + " vendors processed")
    print(str(agreement_counter) + " confirmed vendors")
    print(str(disagreement_counter) + " conflicts")
    print(str(notFound_counter) + " not found in CMBL search")
