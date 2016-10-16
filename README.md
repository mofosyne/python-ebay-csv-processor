# python-ebay-csv-processor

```
## About: this process shipping orders from ebay in csv format.
## By: Brian Khuu briankhuu.com
## First started on 2012 Q1

### To use this, just move your SalesHistory.csv to this folder, then run Process_csv_ebay.py
## Note: make sure there is a PackListArchive folder in the same folder as the script
```

This is the source for a csv ebay processor used to assist a small company trying to avoid using the ebay API, and just wanted to hack together a csv processor that can read the manual output from ebay csv output of the packlist.

It has been redacted, and certain files cannot be included for confidentiality or commercial reasons. But at the very least, it will provide a starting reference point in developing your own solution to automating your ebay system. 

I would warn against just straight up using this, as there has been accumulated cruft in coding over the years during my attempt at getting better at programming (before I even knew what github was, hence the `old version` folder). Instead you are better off using this as a lesson of how not to code, and instead try to pick out what features are most important for you.

There is no warranty or assurance given to the actual usefulness of this script, as its usefulness and reliability will always apply case by case to every company. If you want good software, the best one are tailor made for your problem case. 

## General workflow

0. Make sure `PackListArchive` folder exist.
1. Go to ebay and download the latest shipping orders as CSV, and put it in the root folder of the script. Name the shipping order CSV file as `SalesHistory.csv`. 
2. Run the python script e.g. `process_csv_ebayPythonV3_V4.3.8.py`
3. It will process your order and create a packlist text file in `PackListArchive`, and opens the file in notepad.
  - `packlistfilename = './PackListArchive/pkList.' + filenameTimeStamp + '.txt'`
4. Notepad being open, would halt the script temporarily until you close the notepad window. This gives you time to edit and print the packlist, and review the output for corrections (e.g. incorrectly entered addresses, which is common)
5. Closing the notepad, will run the next section of this script. This scans the generated textual packlist for any valid address starting with `### SEND TO `, and creates a csv list of addresses in './generatedBulkAddresses.csv'. 
  - This allows for sending this csv list to a label printer, and saves the labour of copying and pasting addresses. Allowing for more focus on checking the validity of the actual orders.
  - The simple check for `### SEND TO ` has the side effect of allowing the user to indicate not to print label for a particular address by renaiming `### SEND TO` to something else like `### DO NOT SEND TO `, which would not match and thus no label.

## Design choices

* packlist is done via plain text, which aids in copy and pasting if needed. And is robust if extra comments and changes to orders is needed. Also minimum training. In addition, it allows for outputting in varity of printer outputs e.g. thermal printer.
  - Which is important if a bug occours, and thus manual corrections is required until a fix can be coded in time. 
* Simple error checking of addresses was done via a postcode list. If suburb doesn't match postcode, throw up an error.
* Other checks are provided for common most customer address errors, which cuts down in correction time. 
* Address printing was done via outputting in CSV and relying on users to use the csv file manually in a label printer. This gives users more control over what to do with the label, or to add more addresses randomly.

So while full automation could be possible, for flexibility and robustness, certain design choices was intentionally made to ensure that any situations (like say parts of the script is buggy on certain inputs) does not totally shut down the workflow. E.g. use of text output allows for correction of orders in a freeform manner. 

### Error correction

* state should be in 3 letter notation usally
* some states are confused for cities
* autocorrect when customer put suburb in addr2
* check if postcode match suburb/city
* autocorrect when cust put streetNo in addr1 and address in addr2

### Postage method detection

Also to save time, if the ebay custom field maches a particular keyword in the `CustomField` csv file `postage_method.csv`, it would print a custom instruction in the order on posting method.

This would apply to most simple orders, which would allow the user to focus on the more complex orders which would need more complex packing options. 

### Hard coded search and replace

This was intended to be fully programmable, but just didn't get around to it. Basically there may be times where it would be useful to have a small keyword expand to a full version. Or one that replaces with a unicode symbol (e.g. not allowed unicode in ebay?)

## Requirements

These are required for this script to work.

* python V3 			- Needed for running the script
* pc_full_lat_long.csv 	- Needed for postcode error checking
* postage_method.csv
* SalesHistory.csv

### pc_full_lat_long.csv

Is a CSV file with these fields.

```
"Pcode","Locality","State","Comments","DeliveryOffice","PresortIndicator","ParcelZone","BSPnumber","BSPname","Category","Lat","Long"
```

### postage_method.csv

Is a CSV file with these fields. 

```
Product,Product Configuration,Custom Field on eBay,Recommended Postage Method,Number of Stamps,Number of Labels to print,Is this a click and send label?
```

Which in the code, corresponds to this line

```
        postmethod.append({"Product": productName, "ProductConfig": row[1], "CustomField": row[2], "PostMethod": row[3],
                           "NumStamps": row[4], "NumberOfLabelsToPrint": row[5], "ClickAndSend": row[6]})
```