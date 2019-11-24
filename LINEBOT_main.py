from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    ConfirmTemplate, TemplateSendMessage, MessageAction, ButtonsTemplate, PostbackAction,
    URIAction, PostbackEvent
)
import os

import requests
from urllib.request import urlopen
#import bs4  
#import beautifulsoup4
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
from time import gmtime, strftime
from datetime import timedelta

app = Flask(__name__)
LINE_CHANNEL_ACCESS_TOKEN = 'c3gPIFeP9GW9c9QdRvkZMyJ1knIOgiotqiCZNIMpb+hPyZU4RJGUj5tKwr2NUg5OMnIiGqMeiekgQYUMhNeFLX2fcNI+syakjA8hUABuq6tNSMwG75vOQg8kydz2lBoj4S42Mfq7St+/TpyAccG1QQdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'dc5c9c794a63c1e74ac414ddbe74de2e'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler      = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route('/')
def index():
    return "Welcome to Line Bot!"

@app.route("/callback", methods = ['POST'])
def callback():
    signature = request.headers['X-LINE-Signature'] #
    
    # If as_text is set to True the return value will be a decoded unicode string.
    body = request.get_data(as_text = True)
    #app.logger.info("Request body: " + body)
    #print(body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)    
    return 'OK'

'''
@handler.default()
def default(event):
    print("Captured mesg:", event)
'''

@handler.add(MessageEvent, message = TextMessage)
def handle_message(event):
    _id = event.source.user_id
    profile = line_bot_api.get_profile(_id)    
    UserName = profile.display_name
    keyWord = ['Taipei','New Taipei']
    
    mesg = TextSendMessage(text = event.message.text)
    
    if 'Heartbeat' == mesg.text :
        buttons_template = ButtonsTemplate(
            text ='Hi {} ! Please select the location where you want to query.'.format(str(UserName)), 
            actions=[
                PostbackAction(label='Taipei', data = 'HB_Taipei', text='Please wait while your report(Taipei) is being queried.'), 
                PostbackAction(label='New Taipei part A', data = 'HB_NewTaipei_A', text='Please wait while your report(New Taipei part A) is being queried'),
                PostbackAction(label='New Taipei part B', data = 'HB_NewTaipei_B', text='Please wait while your report(New Taipei part B) is being queried'),
                PostbackAction(label='New Taipei part C', data = 'HB_NewTaipei_C', text='Please wait while your report(New Taipei part C) is being queried')             
            ])    
                                           
        template_mesg = TemplateSendMessage(alt_text = 'the Menu button', template = buttons_template)
        line_bot_api.reply_message(event.reply_token, template_mesg)

    if 'Outlier' == mesg.text :
        replyTXT = "Hi {} ! It is under construction.".format(str(UserName))
        mesg = TextSendMessage(text = replyTXT)
        line_bot_api.reply_message(event.reply_token, mesg) 
    #print("Look at here!A==================\n")
    #print(event)  

@handler.add(PostbackEvent)
def handle_postback(event):
    if isinstance(event, PostbackEvent):
        _id = event.source.user_id
        backdata = event.postback.data
        #print("Look at here!B==================>" + str(backdata))
        if backdata == 'HB_Taipei':        
            queryMesg = creat_mesg('Taipei')
            line_bot_api.push_message(_id,TextSendMessage(text = queryMesg))
        
        if backdata == 'HB_NewTaipei_A':
            queryMesg = creat_mesg('NewTaipei_A')
            line_bot_api.push_message(_id,TextSendMessage(text = queryMesg))

        if backdata == 'HB_NewTaipei_B':
            queryMesg = creat_mesg('NewTaipei_B')
            line_bot_api.push_message(_id,TextSendMessage(text = queryMesg))

        if backdata == 'HB_NewTaipei_C':
            queryMesg = creat_mesg('NewTaipei_C')
            line_bot_api.push_message(_id,TextSendMessage(text = queryMesg))

def creatURL(idN, t):
    string = "http://ec2-54-175-179-28.compute-1.amazonaws.com/get_thinktron_data.php?device_id={}&year_month={}".format(idN,t)
    return string    

def query_data(arg1):
    r = requests.get(arg1) # URL path
    soup = BeautifulSoup(r.text,'lxml')
    a = list(soup.find_all('p'))

    # Split the list through the regular expression
    d = re.split('\s+|,|<br/>|<p>|</p>',str(a))

    # Remove the '' element from the list
    d = list(filter(lambda zz: zz != '', d)) 

    # Remove the '=' element from the list
    d = list(filter(lambda zz: zz != '=', d))

    # Remove the '[' & ']' element from the list
    try:
        d.remove(']')
        d.remove('[')
    except:
        pass
    
    return d

def calculateOFFtime_light(d):
    
    if ("No" in d) & ("results" in d):
        outputStr = "Offline over 1 month"

    else:    
    # Create a dataframe from the URL by data crawling
        colName=['id', 'time', 'weather', 'air','acceleration','cleavage','incline','field1','field2','field3']
        _Num = 0
        _df  = pd.DataFrame(columns=colName)
        df   = pd.DataFrame(columns=colName)

        for ii in range(0,len(d)):    
            while colName[_Num] in d[ii]:
                _lst = d[ii + 1]
                _lst = _lst.strip(',')

                if _lst == '' or (_lst in colName):
                    _lst = None       

                _df[colName[_Num]] = [_lst] # Put the list into the dataframe
                if _Num < (len(colName)-1):
                    _Num += 1
                else:
                    df = df.append(_df, ignore_index=True)
                    _Num = 0 

        # Convert argument to a numeric type(float64 or int64)
        #numericCol = ['roll', 'pitch', 'yaw','field1','field2','field3']
        #for ii in numericCol:
        #    df[ii] = pd.to_numeric(df[ii])

        # Convert the format of date
        dates = df.time
        df.index = pd.to_datetime(dates.astype(str), format='%Y%m%d%H%M%S')
        df.index.name = 'time'
        del df['time']

        # Check dataframe format
        # df.info()

        # Query the latest time stamp
        lastestTimeStr = df.index[-1]

        # Release the memory
        del df

        # Calculate the offline time
        localTimeStamp = pd.to_datetime(strftime("%Y%m%d%H%M%S"), format="%Y%m%d%H%M%S")
        deltaT = localTimeStamp - lastestTimeStr
        alrTimeIntv = timedelta(minutes = 15)

        if deltaT > alrTimeIntv:

            deltaDay = deltaT.days
            deltaHr  = deltaT.seconds // 3600
            deltaMin = (deltaT.seconds % 3600) // 60
            deltaSec = deltaT.seconds % 60

            outputStr = "Offline time: {} day, {} hr".format(deltaDay,deltaHr)
        else:
            outputStr = "Online"            
    return outputStr

def creat_mesg(location):
    mesg = ""
    idNumDict = []
    queryDate = strftime("%Y%m%d")
    quertMonth = strftime("%Y%m")
    #now = strftime("%Y%m%d%H%M")

    if (location.lower() == "newtaipei_a"):
        idNumDict  = [{'name':'馥記山莊','id':'2015'}, # 0
                      {'name':'秀岡第一','id':'3015'}, # 1
                      {'name':'老爺山莊','id':'2011'}, # 2
                      {'name':'老爺山莊','id':'1007'}, # 3                      
                      {'name':'台北小城','id':'3001'}, # 5                      
                      {'name':'薇多綠雅','id':'3028'}] # 7
    elif (location.lower() == "newtaipei_b"):
        idNumDict =  [{'name':'秀岡陽光','id':'3029'}, # 6
                      {'name':'達觀鎮B6','id':'3022'}, # 8
                      {'name':'花園點二','id':'2005'}, # 9 
                      {'name':'花園點二','id':'1005'}, # 10
                      {'name':'達觀鎮A1','id':'3019'}, # 11
                      {'name':'圓富華城','id':'3021'}, # 12             
                      {'name':'淺水灣莊','id':'3023'}, # 13   
                      {'name':'詩畫大樓','id':'3016'}, # 14
                      {'name':'伯爵晶鑽','id':'3025'}, # 15
                      {'name':'花園點一','id':'2009'}, # 16 
                      {'name':'勘農別墅','id':'2010'}] # 17
    elif (location.lower() == "newtaipei_c"):
        idNumDict =  [{'name':'怡園社區','id':'3014'}, # 4
                      {'name':'勘農別墅','id':'1008'}, # 18                      
                      {'name':'國家別墅','id':'3017'}, # 19
                      {'name':'台北山城','id':'3024'}, # 20
                      {'name':'歡喜居易','id':'3013'}, # 21
                      {'name':'伯爵一期','id':'3020'}, # 22
                      {'name':'迎旭山莊','id':'3018'}, # 23
                      {'name':'水蓮山莊','id':'2022'}, # 24
                      {'name':'新雪梨  ','id':'3030'}, # 25
                      {'name':'伯爵幼兒','id':'3032'}] # 26                      
    elif (location.lower() == "taipei"):
        idNumDict  = [{'name':'政大自強','id':'2007'}, # 1
                      {'name':'政大山頂','id':'2001'}, # 2
                      {'name':'政大山頂','id':'1001'}, # 3
                      {'name':'中山北七','id':'2008'}, # 4
                      {'name':'中山北七','id':'1003'}, # 5
                      {'name':'公訓新牆','id':'2003'}, # 6
                      {'name':'公訓舊牆','id':'2002'}, # 7
                      {'name':'公訓舊牆','id':'1002'}, # 8
                      {'name':'松德院北','id':'2021'}, # 9
                      {'name':'松德院北','id':'6001'}, # 10
                      {'name':'松德院北','id':'8001'}, # 11
                      {'name':'松德院南','id':'2020'}, # 12             
                      {'name':'松德院南','id':'6002'}, # 13
                      {'name':'永春高中','id':'2023'}, # 14
                      {'name':'世界山莊','id':'3031'}] # 15
        
    else:
        print("No such name.")

    for ii in range(0, len(idNumDict)):       
        URLstr = creatURL(str(idNumDict[ii]["id"]),queryDate) # Format in (id_Num, yyyymm)
        # print("Look at here:" + URLstr)
        qD = query_data(URLstr)

        if ("No" in qD) & ("results" in qD):
            print("{} Offline over 1 day".format(idNumDict[ii]["id"]))
            URLstr = creatURL(str(idNumDict[ii]["id"]),quertMonth)
            qD = query_data(URLstr)    

        writingStr = calculateOFFtime_light(qD)

        if not (writingStr == "Online"):
            mesg += "{} {} \n".format(idNumDict[ii]["name"],idNumDict[ii]["id"])            
            mesg += "{}\n".format(writingStr)
            mesg += " \n"

        print(str(idNumDict[ii]["id"]) + "  Done.")
    return mesg

if __name__ == "__main__":
    portNum = int(os.environ.get('PORT', 5000))
    app.run(debug = False, host = '0.0.0.0', port = portNum)
