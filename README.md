
This repository contains the code and data behind the
[Geography of US Health Care Industry Payments](http://) site.

### Overview

I obtained the OpenPayments dataset, processed it according to the methods below, 
and built an interactive map interface to visualize and explore the data.

This analysis is limited to undisputed general payments with published identifying information. 
The map only displays data for companies with greater than $1000 in total payments. 

### Methods

1. The data was obtained from  the [Open Payments Downloads](http://www.cms.gov/OpenPayments/Explore-the-Data/Dataset-Downloads.html) page at this url:

    wget http://download.cms.gov/openpayments/12192014_RFRSHDTL.zip
    unzip 12192014_RFRSHDTL.zip

2. The general payments csv was imported into a sqlite database using the [csv2sqlite](https://github.com/perrygeo/csv2sqlite) utility

    csv2sqlite OPPR_ALL_DTL_GNRL_12192014.csv openpayments.db generalpayments

3. The `generate_data.py` script is used to query the database and create all of 
json and support csv files used by the web interface. 



