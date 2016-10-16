## About: this process shipping orders from ebay in csv format.
## By: Brian Khuu briankhuu.com
## First started on 2012 Q1

###To use this, just move your SalesHistory.csv to this folder, then run Process_csv_ebay.py
##Note: make sure there is a PackListArchive folder in the same folder as the script

## v4.3.2 -- Parse and suggest postage rate.
## v4.3 - Display Customer's User ID
## v4.2 - Formatting adjustment, and some common mispelling for ACT.
## v4.1 - Switch to markdown presentation, compactifying presentation
##          ... as well as hacks for dealing with multi orders to same address. (Script is starting to be hacky...)
##          ... Should really start considering revamping the whole script.
## v4.0 - BIG SWITCH TO PYTHONv3.XX
## v3.0 - Fixed symbol replace to only trigger when needed.
## v2.9.1 - added special UTF symbol for easy identification
## v2.9 - attept to fix &amp
## v2.8 - duplicate address detection ( Possibility of saving postage cost )
## v2.7 - fixed multiple quantity alerts message (wasn't displaying before)
## v2.6 - fixed bug where customer may give crappy postcode and crash the script, also move alerts up higher to be seen easier.
## v2.5 - removed "????OR?????" in addr2 print, since it's not a "second address"
## v2.4 - optimise progressbar. Autojoined when cust split address to two fields (addr1='76', addr2='saint st').
## v2.3 - minior bugfix for autocorrect addr2. Now more accurate.
## v2.2 - progress bar fix. Autocorrect common mistake in addr2 being used as suburb field, instead of city
## v2.1 - fixing a loading bug and also make it load faster. Added fancy loading bar.
## v2.0 - Ready to use now. Just some cleanup, and added a "more than one item" notice for orders with multiple quantity.
## v1.9 - CSV parsing of postcode area is fixed, is more accurate now.
## v1.8 - fixed a 24 hour notation bug, changed filename timestamp format
## v1.7 - switch to local time, not GMT; Also set to 12 hour time format
## v1.6 - Auto checks the suburbs to make sure it matches postcode
## v1.5 - Fixed to make sure the v1.4 changes only occours for australia addresses
## v1.4 - Added ruleset recognition for state abbrev
## V1.3 - Added "variation" and custom label fields
## V1.2 - Appends time as well

import csv
import datetime
import sys
import time
from time import gmtime,localtime, strftime

import html.parser #for escaping and unescaping HTML char http://stackoverflow.com/questions/275174/how-do-i-perform-html-decoding-encoding-using-python-django
html_parser = html.parser.HTMLParser()

#### FUNCTIONS ####

# update_progress() : Displays or updates a console progress bar
## Accepts a float between 0 and 1. Any int will be converted to a float.
## A value under 0 represents a 'halt'.
## A value at 1 or bigger represents 100%
def update_progress(progress):
    barLength = 20 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt... \r\n"
    if progress >= 1:
        progress = 1
        status = "Done... \r\n"
    block = int(round(barLength*progress))
    text = "\rPercent: [{0}] {1}% {2}".format( "#"*block + "-"*(barLength-block), progress*100, status)
    sys.stdout.write(text)
    sys.stdout.flush()

#### What is the current date and time ####
print("load time and date")
dateTimeString = strftime("%a %d-%m-%Y %I:%M%p %Ssec",localtime())
filenameTimeStamp = strftime("%a.%d-%m-%Y.H%I_M%M%p.S%S",localtime())

#### Load postcode to suburb database from a CSV file ####
print("load postcode database")
postcodeToSuburbDict = dict()
with open('pc_full_lat_long.csv', 'r') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in spamreader:
        #print str(row[0]) + ' ' + str(row[1])
        # btw row[0] postcode, row[1] suburb name
        #Only accept entries that have numeric postcodes in row[0]
        if row[0].isdigit():
            suburbCity = row[1].lower() # lowercase to ease matching
            postcode = int(row[0])
            nameBSP = row[8].lower() # not sure why, but I think some people use this
            # Creates or append a value to a list in a dict
            if postcode in postcodeToSuburbDict:
                postcodeToSuburbDict[postcode].append(suburbCity)
            else:
                postcodeToSuburbDict[postcode] = [suburbCity]
            if nameBSP not in postcodeToSuburbDict[postcode]:
                postcodeToSuburbDict[postcode].append(nameBSP)

#### PROCESSSING POSTAGE METHOD DB ####
print("load postage method")
with open('postage_method.csv', 'r') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    postmethod = []
    productName = ""
    i = 0
    for row in spamreader:
        if row[0] != "" : # Assume previous product name, if current field is left blank.
            productName = row[0]
        postmethod.append({"Product":productName,"ProductConfig":row[1],"CustomField":row[2],"PostMethod":row[3],"NumStamps":row[4],"Comments":row[5] })
        i = i + 1
        
#### PROCESSING THE SALES HISTORY REPORT IN CSV ####
print("load sales history")
with open('SalesHistory.csv', 'r') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    csvarray = []
    for row in spamreader:
        if row == []:
            continue
        if row[0] == "Sales Record Number": #skip the data descriptors
            field_info = row
        if row[0].isdigit():
            csvarray.append( row )
    #also pop the second last, which contains just the 'total records download'
    csvarray.pop()

#Initialize key list/vars
uniqueAddressList = []

#########################
print("generating packing list")
update_progress(0)

#now create the recipt
sl = [] #stringlist
sl.append( '_____________________')
sl.append( '#   PACKING LIST   #') 
sl.append(  dateTimeString ) 
sl.append( '=====================')

## total numbers of orders
totalOrders = len(csvarray)

#sl.append( str(totalOrders) +' ORDERS TO PACK')
#sl.append( '' )

i = 0
for row in csvarray:
    #increment progressbar
    update_progress(i/float(totalOrders))

    ##alertList
    alertList = []
    
    i += 1

    ### Multiple quantity alerts
    if int(row[14]) > 1:
        alertList.append('MORE THAN 1 QUANTITY – SO IGNORE POSTAGE SUGGESTIONS')

    ### address, city, state, postcode
    addr1 = str(row[5])
    if ( str(row[6]) != ''):
        addr2 = str(row[6])
    else:
        addr2 = ""
    city = row[7]
    state = row[8]
    postcode = row[9]
    country = row[10]

    #Processing addresses for common errors or stylistic deviation or opportunities
    #Check if sent to same address
    if addr1+' '+addr2+' '+city+' '+state+' '+postcode in uniqueAddressList:
        alertList.append("Duplicate address to "+ str(row[2])+" detected. So ignore postage recommendations but merge with duplicate for postage savings. " )
    else:
        uniqueAddressList.append(addr1+' '+addr2+' '+city+' '+state+' '+postcode)
        
    #Only if from australia
    if country.lower() == 'australia':
        ## state should be in 3 letter notation usally
        stateAbbrevList = {'australia capital territory':'ACT','australian capital territory':'ACT','new south wales':'NSW', 'northern territory':'NT', 'queensland':'QLD', 'south australia':'SA', 'tasmania':'TAS', 'victoria':'VIC','western australia':'WA'}
        if state.lower() in stateAbbrevList:
            state = stateAbbrevList[state.lower()]
            
        ## some states are confused for cities
        commonStateErrorList = {'sydney':'NSW', 'brisbane':'QLD', 'melbourne':'VIC'}
        if state.lower() in commonStateErrorList:
            state = commonStateErrorList[state.lower()]
            alertList.append("Customer confused states for cities in state field (Autocorrected)")

        ## some people get postcode number totally incorrect and will break my code if not addressed
        if int(postcode) in postcodeToSuburbDict:
            ## autocorrect when customer put suburb in addr2
            ## This is fine to autocorrect, as customer usally set city as a major city ceneter
            ## which is incorrect. Just in case, the autocorrect will display the original field in alert.
            if addr2.lower() in postcodeToSuburbDict[int(postcode)]:
                alertList.append("In city field, "+city+" was autocorrected to "+addr2)
                city = addr2
                addr2 = ''

            ## check if postcode match suburb/city
            if city.lower() not in postcodeToSuburbDict[int(postcode)]:
                suburbsInPostcode = ""
                for suburbMatched in postcodeToSuburbDict[int(postcode)]:
                    suburbsInPostcode = suburbsInPostcode  + suburbMatched + ", "
                alertList.append("Cannot match postcode to suburb: SUBURBS IN POSTCODE: "+suburbsInPostcode)
        else:
            alertList.append("customer suppied postcode number "+postcode+" does not match to any known postcodes")


        ## autocorrect when cust put streetNo in addr1 and address in addr2
        if addr1.isdigit() and addr2 != '':
            alertList.append("Cust appears to split strt addr to addr1 & addr2: autojoined")
            addr1 = addr1 + ' ' + addr2
            addr2 = ''
            
    #generate order, alerts and address

    ## Order headers
    if( ( addr1 != '') or ( addr2 != '') ): # Bloody hacks to deal with multi item send to same address (via ebay not showing addresses)
        #sl.append('')
        sl.append( '_____________________' )
        sl.append( '## ORDER '+str(i)+" ##" )
        sl.append( '' )
    else:
        sl.append( '' )
    
    ### Alerts
    for strAlert in alertList:
        sl.append("**ALERT**: " + strAlert)
    sl.append("")

    # Processing order for common postage method
    # recall that postmethod has ({"Product":,"ProductConfig":,"CustomField":,"PostMethod":,"NumStamps":,"Comments": })
    # for saleshistory: vairation details (33), custom label (13), Item title 
    for postmethod_row in postmethod:
        if ( row[13] == "" ): # For now we are only dealing with custom field of ebay, so no empty fields allowed
            print("canclePostMethodScanning")
            break
        if ( int(row[14]) > 1 ): # if multiple quantity, then ignore autosuggestion.
            break
        if addr1+' '+addr2+' '+city+' '+state+' '+postcode in uniqueAddressList: # if duplicate, then ignore autosuggestion
            break
        if ( postmethod_row["CustomField"] == row[13] ) and  ( postmethod_row["CustomField"] !="" ) :
            print("detected"+postmethod_row["CustomField"])
            if postmethod_row["Comments"] == "":
                sl.append(" Envelope: "+ postmethod_row["PostMethod"] +",\n stamps:"+postmethod_row["NumStamps"]+",\n")
            else:
                sl.append(" Envelope: "+ postmethod_row["PostMethod"] +",\n stamps:"+postmethod_row["NumStamps"]+",\n comments:"+postmethod_row["Comments"]+",\n")
        
    ## Quanties and type and variant
    sl.append('> QTY: ' + str(row[14])+'x '+str(row[13]) + " "+str(row[33]))
    ## item name
    if (str(row[12]) != ''):
        sl.append('> DESC: '+str(row[12]))
    sl.append('')
    ## postal address
    if( ( addr1 != '') or ( addr2 != '') ): # Bloody hacks to deal with multi item send to same address (via ebay not showing addresses)
        ### UserID
        sl.append( '### SEND TO '+str(row[1])+' ###' )
        ### NAME
        sl.append( str(row[2]) )
        ### address
        sl.append( addr1 )
        if ( addr2 != ''):
            sl.append(addr2)
        ### suburb, state and postcode
        sl.append( city + ' ' + state + ' ' + postcode)
        ### Country
        if ( country.lower() != 'australia' ): # Excludes australia in address if in Australia
            sl.append( country )
sl.append( '_____________________')
sl.append( ' END OF PACKING LIST')
sl.append( '=====================' )



#Completed generation
update_progress(1.0)


#replace keywords/phrases with sybol or phrases
# add "_" before symbol replace commands as a escape char to prevent accidental trigger
searchAndReplace = [
    ## Symbol replace fields
    ["_BLKSQR",      "\u25A0"], # Black SQUARE SYMBOL
    ["_WHTSQR",      "\u25A1"], # WHITE SQUARE SYMBOL
    ["_UP_ARROW",    "\u25B2"], 
    ["_RIGHT_ARROW", "\u25BA"],
    ["_DOWN_ARROW",  "\u25BC"],
    ["_LEFT_ARROW",  "\u25C4"],
    ["_CRYSTAL",     "\u25CA"], # Hollow diamond
    ["_SMILE",       "\u263A"], # Smily face
    ["_BLK_SMILE",   "\u263B"],
    ["_SPADE",       "\u2660"], # Playing card symbols etc...
    ["_CLUB",        "\u2663"],
    ["_HEART",       "\u2665"],
    ["_DIAMOND",     "\u2666"],
    ["_MUSIC",       "\u266B"],
    ["_STAR",        "\u2736"],
    ["_DOT_CIRCLE",  "\u25CC"],
    ["_BLK_CIRCLE",  "\u25CF"],
    ["_WHT_CIRCLE",  "\u25CB"],
    ["_GEAR",        "\u263C"],
    ["_FEMALE",      "\u2640"],
    ["_MALE",        "\u2642"]
    ]

print("search and replace certain words or phrases (hardcoded)")
for i, val in enumerate(sl):
    for sARentry in searchAndReplace:
        sl[i] = sl[i].replace(sARentry[0],sARentry[1])

#file to save to
print("generating filename")
packlistfilename = './PackListArchive/pkList.'+filenameTimeStamp+'.txt'

#save result (This time ensuring all lines is encoded in UTF-8)
print("saving file")
ext_file = open(packlistfilename, "w", encoding="utf-8")
for line in sl:
    #escape html characters
    line = html_parser.unescape(line)
    #print line
    ext_file.write( (line+"\n") )
ext_file.close()

#display file
print("displaying generated packing orders")
import subprocess
subprocess.call(['notepad.exe',packlistfilename])


