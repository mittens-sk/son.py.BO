import pandas as pd
import sys
import numpy as np
import os
from datetime import datetime
from result import *

def getRequest(seq, yymmdd = None) :

    inputPrefix = "SON_TO_TEOS_RL_REQUEST_"

    if yymmdd is None:
        yymmdd = datetime.today().strftime("%Y%m%d")

    nm = inputPrefix + str(yymmdd) + "_" + str(seq) + ".csv"

    try :
        df = pd.read_csv(nm, encoding = 'cp949')
        return df

    except FileNotFoundError:
        pass


def getSiteInfo() :
    df = pd.read_csv('site_info.csv', encoding = 'utf-8', header = 1)
    df = df[['SISUL Code', 'NBR(1st).1']]
    df.columns = ['SISUL_CD1', 'NBR_CD1']
    df = df.dropna(how ='any')
    return df


def getState(seq, yymmdd = None):

    state = getRequest(seq, yymmdd)

    # Src E-Tilt
    etilt = state['E_TILT']
    bins = [-8, -6, -4, -2, 0, 1, 5, 9]
    labels = ["s1", "s2", "s3", "s4", "s5", "s6", "s7"]
    cats = pd.cut(etilt, bins, labels=labels, include_lowest=True, right=False)
    state['SRC_STATE'] = cats

    def getNbrState(x):
        nbrSite = getSiteInfo()
        tmp = list(state.SISUL_CD)

        nbrCell = list(nbrSite.NBR_CD1[nbrSite.SISUL_CD1 == x])

        if len(nbrCell) == 1:
            nbrState = state.E_TILT[tmp.index(nbrCell[0])]
        else:
            nbrState = 99999  #

        return nbrState

    # Nbr E-Tilt
    state['NBR_TILT'] = list(map(lambda i: getNbrState(i), state.SISUL_CD.to_list()))
    catsNbr = pd.cut(state['NBR_TILT'], bins, labels=labels, include_lowest=True, right=False)
    state['NBR_STATE'] = catsNbr


    return state

# def targetSite(filename) :
#
#     try :
#         df = pd.read_csv(filename, encoding = 'cp949')
#         targetSite = df[df['Target']=='Y']['SiteName']
#         return targetSite
#
#     except FileNotFoundError:
#         pass


if __name__ == "__main__":
    input = getState(seq = 1, yymmdd = '20191008')
    result = getStateQuality(seq = 1, yymmdd = '20191008', wa = 0.5, wb = 0.5)

    input = pd.merge(input, result, how = 'left', left_on = 'SISUL_CD', right_on= 'SISUL_CD')
    input = input[['SISUL_CD', 'SRC_STATE', 'NBR_STATE', 'SINR1_Mean', 'RSRP1_Mean', 'gsq']] #SINR1, RSRP1 cut
    input = input.dropna(how = 'any')
    print(input)
    input.to_csv('sample1.csv')

