import pandas as pd
import numpy as np
from datetime import datetime

def getResult(seq, yymmdd = None) :

    resultPrefix = "SON_TO_TEOS_RL_RESULT_"

    if yymmdd is None :
         yymmdd = datetime.today().strftime("%Y%m%d")

    nm = resultPrefix + str(yymmdd) + "_" + str(seq) + ".csv"

    try:
        df = pd.read_csv(nm)
        print(nm)

    except FileNotFoundError:
        pass

    return(df)


def getSiteInfo() :
    df = pd.read_csv('site_info.csv', encoding = 'utf-8', header = 1) # 한글명 인코딩 확인 필요
    df = df[['SISUL Code', 'NBR(1st).1']]
    df.columns = ['SISUL_CD1', 'NBR_CD1']
    df = df.dropna(how ='any')
    return df


def getStateQuality(seq, yymmdd, wa, wb) :

    df = getResult(seq, yymmdd)

    # Cell SINR avg , 5%
    def q5(x):
        return x.quantile(0.05)

    f = {'SINR1': ['mean', q5], 'RSRP1': ['mean']}
    sqResult = df.groupby('SISUL_CD1').agg(f)
    sqResult['sq'] = sqResult[('SINR1', 'mean')] * wa + (1-wa) * sqResult[('SINR1', 'q5')]

    # Nbr Cell

    def getNbrSq(x) :

        nbrSite = getSiteInfo()
        tmp = list(sqResult.index)

        nbrCell = list(nbrSite.NBR_CD1[nbrSite.SISUL_CD1 == x])

        if len(nbrCell) == 1 :
            nbrSq = sqResult.sq[tmp.index(nbrCell[0])]
        else :
            nbrSq = 99999 # nbrCell 없는 경우

        return nbrSq

    sqResult['nbrSq'] = list(map(lambda i: getNbrSq(i), sqResult.index.to_list()))

    # Global SQ
    # sqResult['gsq'] = sqResult['sq'] * wb + (1 - wb) * sqResult[('nbrSq')]
    sqResult['gsq'] = np.where(sqResult['nbrSq'] == 99999, sqResult['sq'] , sqResult['sq'] * wb + (1 - wb) * sqResult[('nbrSq')])

    sqResult.columns =  ['SINR1_Mean', 'SINR1_Q5', 'RSRP1_Mean', 'sq', 'nbrSq', 'gsq']
    sqResult['SISUL_CD'] = list(sqResult.index)


    return sqResult

