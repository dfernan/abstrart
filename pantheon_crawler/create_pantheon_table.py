#!/usr/bin/env python

def csv_to_mysql(filename, tablename):
    '''this piece of code reads in a .csv file and saves it to a MySQL database
        'filename' and 'tablename' need to be strings.
        I.e., csv_to_mysql('/Users/daniel/insight/pantheon_data/pantheon_no_null.csv','pantheon')
    '''
    
    import pymysql as mdb
    import pandas as pd

    con =  mdb.connect('localhost', 'root','','abstrart_db'); 
    
    data = pd.read_csv(filename)
    
    ## fixing table columns
    data.columns = [i.replace(' ','_') for i in data.columns]
    
    
    ### replacing nan with null to make it mysql friendly
    data = data.where((pd.notnull(data)), None)
    
    
    with con:
            cur = con.cursor()
            cur.execute("USE abstrart_db;")
            data.to_sql(con = con, name = tablename, if_exists = 'replace', flavor = 'mysql')
            
if __name__ == "__main__":
    csv_to_mysql('/Users/daniel/insight/pantheon_data/pantheon_no_null.csv', 'pantheon')