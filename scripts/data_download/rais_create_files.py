# -*- coding: utf-8 -*-
'''
 python scripts/data_download/rais_create_files.py
 The files will be saved in scripts/data/rais

clear data files 
rm scripts/data/files_*/*
'''
from collections import namedtuple
from common import engine, get_colums
from dictionary import en, pt
import pandas as pd
import os
import bz2
import sys
import logging

# logging.basicConfig(filename=os.path.join(sys.argv[1], 'rais-data-download.log'),level=logging.DEBUG)

def select_table(conditions):
    s = 'y'

    if conditions[1] != ' 1 = 1 ':
        s += 'b'

    if conditions[1] == ' 1 = 1 ' and conditions[2] == ' 1 = 1 ' and conditions[3] == ' 1 = 1 ':
        s += 'b'

    if conditions[2] != ' 1 = 1 ':
        s += 'i'

    if conditions[3] != ' 1 = 1 ':
        s += 'o'

    return 'rais_' + s



def get_colums(table):
    column_rows = engine.execute("SELECT COLUMN_NAME FROM information_schema.columns WHERE TABLE_NAME='"+table+"' AND COLUMN_NAME NOT LIKE %s", "%_len")
    return [row[0] for row in column_rows]


def save(years, locations, industrys, occupations, lang, output_path):
    conditions = [' 1 = 1', ' 1 = 1', ' 1 = 1', ' 1 = 1']  # 4 condicoes
    table_columns = {}
    output_path='scripts/data/rais/'+lang
    columns_deleted=['num_emp', 'hist', 'Gini', 'bra_id_len', 'cbo_id_len', 'cnae_id_len']

    if lang == 'en':
        dic_lang = en
    else:
        dic_lang = pt

    for year in years:
        conditions[0] = year.condition
        for location in locations:
            conditions[1] = location.condition
            for industry in industrys:
                conditions[2] = industry.condition
                for occupation in occupations:

                    if location.condition == ' 1 = 1 ' and industry.condition == ' 1 = 1 ' and occupation.condition == ' 1 = 1 ':
                            continue;

                    conditions[3] = occupation.condition
                    table = select_table(conditions)
                    name_file = 'rais'+str(year.name)+str(location.name)+str(industry.name)+str(occupation.name)
                    
                    if table not in table_columns.keys():
                        table_columns[table] = [ i+" as '"+dic_lang[i]+"'" for i in get_colums(table, columns_deleted)]

                    query = 'SELECT '+','.join(table_columns[table])+' FROM '+table+' WHERE '+' and '.join(conditions)

                    print name_file
                    # logging.info(query)
                    # f = pd.read_sql_query(query, engine)
                    
                    # new_file_path = os.path.abspath(os.path.join(output_path, name_file+".csv.bz2")) #pega desda da rais do pc
                    # new_file_path='/home/ubuntu/files/rais/'+lang+'/'+name_file+'.csv.bz2';
                    # f.to_csv(bz2.BZ2File(new_file_path, 'wb'), sep=",", index=False, float_format="%.3f", encoding='utf-8')



Condition = namedtuple('Condition', ['condition', 'name'])


years = [
    Condition('year=2002', '-2002'),
    Condition('year=2003', '-2003'),
    Condition('year=2004', '-2004'),
    Condition('year=2005', '-2005'),
    Condition('year=2006', '-2006'),
    Condition('year=2007', '-2007'),
    Condition('year=2008', '-2008'),
    Condition('year=2009', '-2009'),
    Condition('year=2010', '-2010'),
    Condition('year=2011', '-2011'),
    Condition('year=2012', '-2012'),
    Condition('year=2013', '-2013')]

locations = [
    Condition(' 1 = 1 ', ''),
    Condition('bra_id_len=1', '-regions'),
    Condition('bra_id_len=3', '-states'),
    Condition('bra_id_len=5', '-mesoregions'),
    Condition('bra_id_len=7', '-microregions'),
    Condition('bra_id_len=9', '-municipalities')]

industrys = [
    Condition(' 1 = 1 ', ''),
    Condition('cnae_id_len=1', '-sections'),
    Condition('cnae_id_len=3', '-divisions'),
    Condition('cnae_id_len=6', '-classes')]

occupations = [
    Condition(' 1 = 1 ', ''),
    Condition('cbo_id_len=1', '-main_groups'),
    Condition('cbo_id_len=4', '-families')]


if len(sys.argv) != 2 or (sys.argv[1:][0] not in ['pt', 'en']):
    print "ERROR! use :\npython scripts/data_download/secex_create_files.py en/pt"
    exit()

save(years=years, locations=locations, industrys=industrys, occupations=occupations, lang=sys.argv[1:][0])

