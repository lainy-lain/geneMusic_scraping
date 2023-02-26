from selenium import webdriver
from bs4 import BeautifulSoup
import re
import time
import random

# chromedriver.exe의 경로 입력해야함
driver = webdriver.Chrome('D:\webcrawling\chromedriver.exe')

def mySleep():
    # 웹 스크래핑 방지 우회를 위해 sleep
    ranVal = random.uniform(0.5, 1.4)
    time.sleep(ranVal)

MONTHTOP_MAXPAGE = 5           # 1~4
YEARTOP_MAXPAGE = 3            # 1~2
MAX_CATEGORY = 2               # 0~1
list_year = ['2021', '2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012']
list_songID = []
list_albumID = []


# 2022년 10월 월간 TOP200 Chart Link
url_format = "https://www.genie.co.kr/chart/top200?ditc=M&ymd=20221001&hh=22&rtm=N&pg={}"

for page in range(1, MONTHTOP_MAXPAGE): 
    url = url_format.format(page) #format함수 이용해 스크래핑할 url 생성(완성)
    driver.get(url)
    chart = driver.page_source
    soup = BeautifulSoup(chart, 'html.parser') #해당 URL의 html을 읽어옴
    
    # 해당 HTML에서, 곡 ID만 읽어오기 위해서 selector 이용
    selector = "#body-content > div.newest-list > div > table > tbody > tr.list"
    raw_data = soup.select(selector)
    for tag in raw_data:
        sid = tag.get('songid')
        list_songID.append(sid)
        # 월간 TOP 200에는 중복되는 곡이 없으므로 중복 처리를 하지 않았지만, 뒤에서는 중복 처리를 해 주어야 한다.
    
    # 해당 HTML에서, 앨범 ID만 읽어오기 위해서 selector 이용
    selector = "#body-content > div.newest-list > div > table > tbody > tr.list > td.info > a.albumtitle.ellipsis"
    raw_data = soup.select(selector)
    for tag in raw_data:
        string = tag.get('onclick')
        aid = re.sub(r'[^0-9]', '', string) #onclick = '' 부분에서, 숫자가 아닌 부분은 전부 지워서 album id만 남게 한다.
        list_albumID.append(aid)
        


# 시대별 인기차트 TOP100 Link
url_format = "https://www.genie.co.kr/chart/musicHistory?year={}&category={}&pg={}"

for year in list_year:
    for category in range(0, MAX_CATEGORY):
        for page in range(1, YEARTOP_MAXPAGE):
            url = url_format.format(year, category, page)
            driver.get(url)
            chart = driver.page_source
            soup = BeautifulSoup(chart, 'html.parser')
            
            # songid list와 albumid list는 인덱스의 pair가 맞아야 하므로, 중복으로 sid를 넣지 않으면 aid도 넣지 않아야 한다.
            dupIndexList = []
            index = 0
            
            # 해당 HTML에서 곡 ID 읽어오기 위해 selector 사용
            selector = "#body-content > div.songlist-box > div.music-list-wrap > table > tbody > tr.list"
            raw_data = soup.select(selector)
            for tag in raw_data:
                sid = tag.get('songid')
                if sid in list_songID: #이미 리스트에 존재하는 곡인 경우
                    dupIndexList.append(index)
                else:
                    list_songID.append(sid)
                index += 1
            
            # index값 초기화
            index = 0
            
            # 해당 HTML에서 앨범 ID 읽어오기 위해 selector 사용
            selector = "#body-content > div.songlist-box > div.music-list-wrap > table > tbody > tr.list > td.info > a.albumtitle.ellipsis"
            raw_data = soup.select(selector)
            for tag in raw_data:
                if index in dupIndexList: #해당 앨범과 대응하는 곡이 중복이라 추가되지 않았으면, 앨범 정보도 추가하지 않는다.
                    index += 1
                    continue
                string = tag.get('onclick')
                aid = re.sub(r'[^0-9]', '', string)
                list_albumID.append(aid)
                index += 1



songURL_format = "https://www.genie.co.kr/detail/songInfo?xgnm={}"
albumURL_format = "https://www.genie.co.kr/detail/albumInfo?axnm={}"

list_selector = ["#body-content > div.song-main-infos > div.info-zone > h2",
                 "#body-content > div.song-main-infos > div.info-zone > ul > li:nth-child(1) > span.value > a",
                 "#body-content > div.song-main-infos > div.info-zone > ul > li:nth-child(6) > span.value",
                 "#body-content > div.song-main-infos > div.info-zone > ul > li:nth-child(5) > span.value",
                 "#body-content > div.song-main-infos > div.info-zone > ul > li:nth-child(7) > span.value",
                 "#body-content > div.song-main-infos > div.aside-zone.daily-chart > div.total > div:nth-child(2) > p",
                 "#emLikeCount",
                 "#body-content > div.song-main-infos > div.info-zone > ul > li:nth-child(3) > span.value",
                 "#body-content > div.song-main-infos > div.info-zone > ul > li:nth-child(4) > span.value",
                ]

list_selector_album = ["#body-content > div.album-detail-infos > div.info-zone > ul > li:nth-child(5) > span.value",
                       "#body-content > div.album-detail-infos > div.info-zone > ul > li:nth-child(4) > span.value",
                       "#body-content > div.album-detail-infos > div.info-zone > ul > li:nth-child(3) > span.value",
                      ]

songInfo = [] #곡의 정보를 list형태로 저장하기 위한 list
albumInfo = [] # (앨범)데이터 임시 저장소, 나중에 songInfo와 합병시킴

# album id로부터 앨범의 발매시점, 기획사, 발매사 정보를 얻는다
for id in list_albumID:
    url = albumURL_format.format(id)
    driver.get(url)
    chart = driver.page_source
    soup = BeautifulSoup(chart, 'html.parser')
    
    tmpList = []
    for selector in list_selector_album:
        raw_data = soup.select(selector)
        if len(raw_data) == 0: # raw data 정보가 없는 경우(empty)
            tmpList.append("")
        for tag in raw_data:
            tmpList.append( tag.get_text().strip() )
    
    albumInfo.append(tmpList)
    mySleep()

# song id로부터 곡의 정보들을 얻는다
sid_cnt = 0 # 해당 곡의 앨범 정보 알기 위해서..
for id in list_songID:
    url = songURL_format.format(id)
    driver.get(url)
    chart = driver.page_source
    soup = BeautifulSoup(chart, 'html.parser')
    
    tmpList = []

    for i in range(7):
        raw_data = soup.select(list_selector[i])
        if len(raw_data) == 0: # raw data 정보가 없는 경우(empty)
            tmpList.append("")
        for tag in raw_data:
            string = tag.get_text()
            if string[0:3] == '19금':
                string = string[3:]
            tmpList.append( string.strip() )
            
    tmpList = tmpList + albumInfo[sid_cnt] #songInfo에 albumInfo 병합시키기 위해서
    
    is_time_correct = False
    raw_data = soup.select(list_selector[-1])
    if len(raw_data) == 0: 
        is_time_correct = True
    else:
        for tag in raw_data:
            if len(tag.get_text()) == 0 or tag.get_text()[0].isdigit():
                 is_time_correct = True
                
    if is_time_correct:
        for i in range(7, 9):
            raw_data = soup.select(list_selector[i])
            if len(raw_data) == 0: # raw data 정보가 없는 경우(empty)
                tmpList.append("")
            for tag in raw_data:
                tmpList.append( tag.get_text().strip() )
    else:
        selector_abnormal = ["#body-content > div.song-main-infos > div.info-zone > ul > li:nth-child(4)",
                              "#body-content > div.song-main-infos > div.info-zone > ul > li:nth-child(5)"
                            ]
        for selector in selector_abnormal:
            raw_data = soup.select(selector)
            if len(raw_data) == 0: # raw data 정보가 없는 경우(empty)
                tmpList.append("")
            for tag in raw_data:
                tmpList.append( tag.get_text().strip() )

    songInfo.append(tmpList)
    sid_cnt += 1
    mySleep()
    
    
# 곡 명, 스트리밍 수, 좋아요 수 --> ,를 ''로 바꾸어 주자
# 가수, 작곡가, 작사가, 편곡자, 기획사, 발매사 --> ,를 & 로 바꾸어 주자.


f = open("./newData.csv", "w", encoding='UTF8')

tup = "곡 명, 아티스트, 작곡가, 작사가, 편곡자, 스트리밍 수, 좋아요 수, 발매시점, 기획사, 발매사, 장르, 재생시간\n"
f.write(tup)

# 작사가 재생시간 오류 제거위한 정규표현식
p = re.compile('\d+:\d+')

for row in songInfo:
    index = 1
    for col in row:
        if index == 4: #작사가에 재생시간이 나타나는 오류 제거
            m = p.match(col)
            if m:
                col = ''            
        if index == 1: #19금 제거
            if col[0:3] == '19금':
                col = col[3:].strip()
            
        if index in (1, 6, 7):
            col = col.replace(',', '') 
        elif index in (2, 3, 4, 5, 9, 10):
            col = col.replace(',', ' & ')
        
        if index == 12:
            col += "\n"
        else:
            col += ", "
            
        f.write(col)
        index += 1
        
f.close()

