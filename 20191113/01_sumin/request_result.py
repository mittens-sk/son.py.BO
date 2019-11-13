#!/usr/bin/env python
# coding: utf-8

# In[42]:


import sys
import pandas as pd
import os
from datetime import datetime
import numpy as np


# In[43]:


# Cell별 Nbr Cell 정보
def getSiteInfo() :
    sites = pd.read_csv('site_info.csv', encoding = 'utf-8', header = 1) 
    sites = sites[['SISUL Code', 'NBR(1st).1']]
    sites.columns = ['SISUL_CD1', 'NBR_CD1']
    sites = sites.dropna(how ='any')
    return sites

# Read Result File 
def getResult(seq, yymmdd) :

    resultPrefix = "TEOS_TO_SON_RL_RESULT_"

    nm = resultPrefix + str(yymmdd) + "_[" + str(seq) + "].dat"

    try:
        resultFile = pd.read_csv(nm, sep = '|', header = None)
        print(nm)
        resultFile.columns = ['REQUEST_DATE','SCENARIO_SEQ','REQUEST_SEQ','XPOS','YPOS',
                      'SISUL_CD1','RSRP1','SINR1',
                      'SISUL_CD2','RSRP2','SINR2',
                      'SISUL_CD3','RSRP3','SINR3']

    except FileNotFoundError:
        pass

    return resultFile


# State Quality 계산
def getStateQuality(seq, yymmdd = None, wa = 0.5, wb = 0.5) :

    if yymmdd is None :
         yymmdd = datetime.today().strftime("%Y%m%d")

    path = '/home/tangosvc/code/data/' + yymmdd
    
    os.chdir(path)
    result = getResult(seq, yymmdd)
   
    # Cell SINR avg , 5%
    def q5(x):
        return x.quantile(0.05)

    f = {'SINR1': ['mean', q5], 'RSRP1': ['mean']}
    sqResult = result.groupby('SISUL_CD1').agg(f)
    sqResult['sq'] = sqResult[('SINR1', 'mean')] * wa + (1-wa) * sqResult[('SINR1', 'q5')]

    # Nbr Cell

    def getNbrSq(x) :
       
        os.chdir('/home/tangosvc/code/data')
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


# In[44]:


# Read Request File
def getRequest(seq, yymmdd) :

    requestPrefix = "SON_TO_TEOS_RL_REQUEST_"

    nm = requestPrefix + str(yymmdd) + "_[" + str(seq) + "].dat"

    try:
        rq = pd.read_csv(nm, sep = '|', header = None)
       
        rq.columns = ['REQUEST_DATE', 'SCENARIO_SEQ', 'REQUEST_SEQ', 
                      'START_XPOS', 'END_XPOS', 'START_YPOS', 'END_YPOS', 'SITE_NAME', 'FA_SEQ', 
                      'SISUL_CD', 'DUH_EQUIP_ID', 'PCI', 'XPOS', 'YPOS', 'CELL_NO', 'TOWER_HEIGHT', 
                      'BUILDING_HEIGHT', 'ANTENNA_NM', 'ORIENT', 
                      'E_TILT', 'MTILT']

    except FileNotFoundError:
        pass

    return rq

# get Current State from Request FIle 
def getState(seq, yymmdd = None):
    
    if yymmdd is None :
         yymmdd = datetime.today().strftime("%Y%m%d")

    path = '/home/tangosvc/code/data/' + yymmdd
    os.chdir(path)
    
    state = getRequest(seq, yymmdd)

    # Src E-Tilt
    etilt = state['E_TILT']
    bins = [-8, -6, -4, -2, 0, 1, 5, 9]
    labels = ["s1", "s2", "s3", "s4", "s5", "s6", "s7"]
    cats = pd.cut(etilt, bins, labels=labels, include_lowest=True, right=False)
    state['SRC_STATE'] = cats

    def getNbrState(x):
        
        os.chdir('/home/tangosvc/code/data')
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


def cutStateQuality(df2): 
    
    # sinr1 
    sinr = df2['SINR1_Mean']
    bins = [-999, 0, 5, 10, 15, 20, 25, 99]
#     labels = ["s1", "s2", "s3", "s4", "s5", "s6", "s7"]
#     cats = pd.cut(sinr, bins, labels=labels, include_lowest=True, right=True)
    cats = pd.cut(sinr, bins, include_lowest=True, right=True)

    df2['SINR1_STATE'] = cats
    
    #rsrp
    rsrp = df2['RSRP1_Mean']
    bins = [-999, -110, -100, -90, -80, -70, -60, 999]
#    labels = ["s1", "s2", "s3", "s4", "s5", "s6", "s7"]
#     cats = pd.cut(sinr, bins, labels=labels, include_lowest=True, right=False)
    cats = pd.cut(rsrp, bins, include_lowest=True, right=True)

    df2['RSRP1_STATE'] = cats
    
    df2 = df2[['SISUL_CD', 'SINR1_STATE', 'RSRP1_STATE']]    
    
    return df2
    
    

# update and read request File
def outputDatFile(action = None, curSeq = 12, yymmdd = None, path0 = '/home/tangosvc/code/data/'): 
       
    if yymmdd is None:
        yymmdd = datetime.today().strftime("%Y%m%d")
        
    path = path0 + yymmdd
    os.chdir(path)
    
    output = getRequest(seq = curSeq, yymmdd = yymmdd)
    
    # 임시 결과 
    if action is None :
        action = np.random.randint(-2,2, output.shape[0]) ## getRequest
    
    resultPrefix = "SON_TO_TEOS_RL_REQUEST_"
    
    output['E_TILT'] = pd.DataFrame(action)[0] + output['E_TILT']   
    
    # E-Tilt 가 -8~8 범위를 넘어가는 경우 처리
    
    
    
    
    newSeq = curSeq + 1
    nm = resultPrefix + str(yymmdd) + "_[" + str(newSeq) + "].dat"
              
    output.to_csv(nm, sep = "|", header = False, index = False)                      
    
    ## End
 


# In[45]:


if __name__ == "__main__":
    
    ##임시 
    s = 12               # 현재 seq 필요 
    ymd = '20191018' # None 인 경우 오늘 날짜로 아래 스크립트 실행됨 
    
    # test 
    while s < 25 :
    
        # Get Request File 
        rq = getState(seq = s, yymmdd = ymd)

        # Get Result File , State Quality 계산
        rs = getStateQuality(seq = 12, yymmdd = ymd, wa = 0.5, wb = 0.5) # Result File 은 12로 고정한 상태

        # Model Input
        input1 = rq[['REQUEST_DATE', 'SCENARIO_SEQ', 'REQUEST_SEQ', 'SISUL_CD', 'SRC_STATE', 'NBR_STATE']]
        input2 = cutStateQuality(rs)
        input = pd.merge(input1, input2, how = 'left', left_on = 'SISUL_CD', right_on= 'SISUL_CD')
        print(input)

        # Model 




        # Action 반영 (임시) --> Target Cell 의 Action 만 update 해야함 
        decAct = np.random.randint(-2,2, rq.shape[0]) 
        
        # Save New Request File (함수 내부적으로 seq + 1), File 경로 확인 필요 , 폴더 생성?
        
        outputDatFile(action = decAct, curSeq = s, yymmdd = '20191018')  
        
        s = s + 1
        print(ymd + " / Seq : " + str(s))
        
        # Request Put 
    
    
    # End
    

