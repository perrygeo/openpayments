#!/bin/env python
"""
Generates JSON and CSV datasets for use in web mapping interface 
see http:// 
Relies on getting the openpayments db into sqlite using csv2sqlite 
"""
from __future__ import print_function
import json
import os
import sqlite3
from glob import glob

thisdir = os.path.abspath(os.path.dirname(__file__))
outdir = os.path.join(thisdir, 'static', 'data')
db = os.path.join(thisdir, 'openpayments.db')
conn = sqlite3.connect(db)
COMPANIES_JSON = os.path.join(outdir, 'companies.json')


def get_allcompanies():
    # Special case
    sql = """SELECT 
        g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Id" as company_id,
        min(g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Name") as company_name,
        min(g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_State") as company_state,
        min(g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Country") as company_country,
        sum(CASE WHEN "Covered_Recipient_Type" = 'Covered Recipient Physician'
            THEN "Total_Amount_of_Payment_USDollars" ELSE 0 END) as physican_dollars,
        sum(CASE WHEN "Covered_Recipient_Type" != 'Covered Recipient Physician'
            THEN "Total_Amount_of_Payment_USDollars" ELSE 0 END) as hospital_dollars,
        sum("Total_Amount_of_Payment_USDollars") as total_dollars,
        sum(CASE WHEN "Covered_Recipient_Type" = 'Covered Recipient Physician'
            THEN "Number_of_Payments_Included_in_Total_Amount" ELSE 0 END) as physican_payments,
        sum(CASE WHEN "Covered_Recipient_Type" != 'Covered Recipient Physician'
            THEN "Number_of_Payments_Included_in_Total_Amount" ELSE 0 END) as hospital_payments,
        sum("Number_of_Payments_Included_in_Total_Amount") as total_payments,
        count(1) as records
    FROM generalpayments as g
    WHERE g."Dispute_Status_for_Publication" = 'No'  -- undisputed ONLY
    GROUP BY g."Dispute_Status_for_Publication"
    """

    cursor = conn.cursor()
    cursor.execute(sql)
    d = cursor.fetchone()
    return {
        "id": -1,
        "name": "_All Companies",
        "location": None,
        "dollars_phys": d[4],
        "dollars_hosp": d[5],
        "dollars_total": d[6],
        "payments_phys": d[7],
        "payments_hosp": d[8],
        "products": [] }

def get_companies():
    sql = """SELECT 
        g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Id" as company_id,
        min(g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Name") as company_name,
        min(g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_State") as company_state,
        min(g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Country") as company_country,
        -- psuedo crosstab
        sum(CASE WHEN "Covered_Recipient_Type" = 'Covered Recipient Physician'
            THEN "Total_Amount_of_Payment_USDollars" ELSE 0 END) as physican_dollars,
        sum(CASE WHEN "Covered_Recipient_Type" != 'Covered Recipient Physician'
            THEN "Total_Amount_of_Payment_USDollars" ELSE 0 END) as hospital_dollars,
        sum("Total_Amount_of_Payment_USDollars") as total_dollars,
        sum(CASE WHEN "Covered_Recipient_Type" = 'Covered Recipient Physician'
            THEN "Number_of_Payments_Included_in_Total_Amount" ELSE 0 END) as physican_payments,
        sum(CASE WHEN "Covered_Recipient_Type" != 'Covered Recipient Physician'
            THEN "Number_of_Payments_Included_in_Total_Amount" ELSE 0 END) as hospital_payments,
        sum("Number_of_Payments_Included_in_Total_Amount") as total_payments,
        count(1) as records
    FROM generalpayments as g
    WHERE g."Dispute_Status_for_Publication" = 'No'  -- undisputed ONLY
    GROUP BY 
        g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Id"
    ORDER BY  sum("Total_Amount_of_Payment_USDollars") DESC;
    """
    cursor = conn.cursor()

    yield get_allcompanies()

    for d in cursor.execute(sql):
        if d[6] < 1000:  #1e6:
            # minimum dollar threshold
            continue
        yield {
            "id": d[0],
            "name": d[1],
            "location": "{}, {}".format(d[2], d[3]),
            "dollars_phys": d[4],
            "dollars_hosp": d[5],
            "dollars_total": d[6],
            "payments_phys": d[7],
            "payments_hosp": d[8],
            "products": None }

def find_products(company):

    if company['id'] == -1:
        return company

    sql = """SELECT DISTINCT(g."Name_of_Associated_Covered_Drug_or_Biological1") as product
        FROM generalpayments as g 
        WHERE g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Id" = '{id}'
        AND g."Name_of_Associated_Covered_Drug_or_Biological1" != ''

        UNION

        SELECT DISTINCT(g."Name_of_Associated_Covered_Drug_or_Biological2") as product
        FROM generalpayments as g
        WHERE g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Id" = '{id}'
        AND g."Name_of_Associated_Covered_Drug_or_Biological2" != ''

        UNION

        SELECT DISTINCT(g."Name_of_Associated_Covered_Drug_or_Biological3") as product
        FROM generalpayments as g
        WHERE g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Id" = '{id}'
        AND g."Name_of_Associated_Covered_Drug_or_Biological3" != ''

        UNION

        SELECT DISTINCT(g."Name_of_Associated_Covered_Drug_or_Biological4") as product
        FROM generalpayments as g
        WHERE g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Id" = '{id}'
        AND g."Name_of_Associated_Covered_Drug_or_Biological4" != ''

        UNION

        SELECT DISTINCT(g."Name_of_Associated_Covered_Drug_or_Biological5") as product
        FROM generalpayments as g
        WHERE g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Id" = '{id}'
        AND g."Name_of_Associated_Covered_Drug_or_Biological5" != '';
    """.format(**company)

    cursor = conn.cursor()
    products = []
    for d in cursor.execute(sql): 
        # print(company, d)
        products.append(d[0])

    company['products'] = products
    
    return company


def write_companies(companies):
    with open(COMPANIES_JSON, 'w') as fh:
        fh.write(json.dumps(companies))

def write_report_bystate(company):
    csv_path = os.path.join(outdir, 'bycompany', "{}.csv".format(company['id']))
    print("Generating report", csv_path)

    sql = """SELECT 
            "Recipient_State" as state,

            sum("Total_Amount_of_Payment_USDollars") as dollars,
            sum("Number_of_Payments_Included_in_Total_Amount") as payments,

            sum(CASE WHEN "Covered_Recipient_Type" = 'Covered Recipient Physician'
                THEN "Total_Amount_of_Payment_USDollars" ELSE 0 END) as physican_dollars,
            sum(CASE WHEN "Covered_Recipient_Type" = 'Covered Recipient Physician'
                THEN "Number_of_Payments_Included_in_Total_Amount" ELSE 0 END) as physican_payments,

            sum(CASE WHEN "Covered_Recipient_Type" != 'Covered Recipient Physician'
                THEN "Total_Amount_of_Payment_USDollars" ELSE 0 END) as hospital_dollars,
            sum(CASE WHEN "Covered_Recipient_Type" != 'Covered Recipient Physician'
                THEN "Number_of_Payments_Included_in_Total_Amount" ELSE 0 END) as hospital_payments

        FROM generalpayments as g
        WHERE g."Dispute_Status_for_Publication" = 'No'  -- undisputed ONLY
        AND g."Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Id" = '{}'
        GROUP BY 
            "Recipient_State";""".format(company['id'])
    
    if company['id'] == -1:
        # special case, all companies
        sqltemp = []
        for line in sql.split('\n'):
            if not line.strip().startswith("AND"): 
                sqltemp.append(line)
        sql = "\n".join(sqltemp)

    cursor = conn.cursor()

    with open(csv_path, 'w') as fh:
        fh.write("state,dollars,payments,physican_dollars,physican_payments,"
            "hospital_dollars,hospital_payments\n")
        for row in cursor.execute(sql):    
            fh.write(','.join([str(d) for d in row]) + "\n")

def main():

    # Create list of company objects 
    print("Getting company summaries...")
    companies = list(get_companies())

    print("Finding company products..")
    companies = map(find_products, companies)

    print("Writing json..")
    write_companies(companies)

    print("Generating state reports for each company...")
    _ = map(write_report_bystate, companies)

    print("DONE")

if __name__ == '__main__':
    main()


