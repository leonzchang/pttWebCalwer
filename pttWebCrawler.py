import json
import requests
import re
from bs4 import BeautifulSoup
import time
import argparse


class PttWebCrawler:
    def __init__(self, board,  start, end):
        self.board = board
        self.PTT_URL = 'https://www.ptt.cc'
        self.fileName = self.board + '-' + \
            str(start) + '-' + str(end) + '.json'

        start, end = int(start), int(end)

        # crawler to lastest page
        if end == -1:
            end = self.getLastPage()

        self.saveFile('{"articles": [')
        for index in range(0, end-start+1):
            print('Processing index:', str(start+index))
            resp = requests.get(
                url=self.PTT_URL + '/bbs/' + self.board +
                '/index' + str(start+index) + '.html',
                cookies={'over18': '1'}
            ).content.decode('utf-8')

            soup = BeautifulSoup(resp)
            divs = soup.find_all('div', {'class': 'title'})
            for div in divs:
                link = div.find('a')
                # get all the link on single page,exclude deleted article
                if link:
                    # calwer data
                    # get compelete url
                    calwerURL = self.PTT_URL + link.get('href')
                    jsonData = self.calwer(calwerURL)
                    print(jsonData)
                    if div == divs[-1] and index == end-start:
                        self.saveFile(jsonData)
                    else:
                        self.saveFile(jsonData+',')
                time.sleep(0.1)

        self.saveFile(']}')

    def __del__(self):
        print("object deleted")

    def saveFile(self, data):
        with open(self.fileName, 'a', encoding='utf-8') as f:
            f.write(data)

    def getLastPage(self):
        content = requests.get(
            url=self.PTT_URL+'/bbs/' + self.board + '/index.html',
            cookies={'over18': '1'}
        ).content.decode('utf-8')
        first_page = re.search(
            'href="/bbs/' + self.board + '/index(\d+).html">&lsaquo;', content)
        if first_page is None:
            return 1
        return int(first_page.group(1)) + 1

    def calwer(self, link):
        resp = requests.get(url=link, cookies={'over18': '1'})
        article_id = link.split(self.board+'/')[1].split('.html')[0]
        soup = BeautifulSoup(resp.text)
        mainContent = soup.find('div', {'class': 'bbs-screen bbs-content'})
        head = mainContent.find_all('div', {'class': 'article-metaline'})
        pushes = mainContent.find_all('div', {'class': 'push'})

        author = head[0].select(
            'span', {'class': 'article-meta-value'})[1].text
        title = head[1].select('span', {'class': 'article-meta-value'})[1].text
        date = head[2].select('span', {'class': 'article-meta-value'})[1].text
        # find Author ip
        ipInfo = mainContent.find_all('span', {'class': 'f2'})
        ip = re.search(
            '來自: (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}[^0-9])', str(ipInfo))[1]
        content = mainContent.text.split("※ 發信站:")[0]

        # push messages
        p, b, n = 0, 0, 0
        messages = []
        for push in pushes:

            # if not push.find('span', 'push-tag'):
            #     continue
            push_tag = push.find(
                'span', {'class': 'push-tag'}).text.strip(' \t\n\r')
            push_userid = push.find(
                'span', {'class': 'push-userid'}).text.strip(' \t\n\r')
            push_content = push.find(
                'span', {'class': 'push-content'}).text.strip(': \t\n\r')

            push_ipdatetime = push.find(
                'span', 'push-ipdatetime').text.strip(' \t\n\r')
            messages.append({'push_tag': push_tag, 'push_userid': push_userid,
                             'push_content': push_content, 'push_ipdatetime': push_ipdatetime})
            if push_tag == '推':
                p += 1
            elif push_tag == '噓':
                b += 1
            else:
                n += 1

        # count: push number - boo number ; all: all push number
        message_count = {'all': p+b+n, 'count': p -
                         b, 'push': p, 'boo': b, "neutral": n}

        # json data
        data = {
            'board': self.board,
            'article_id': article_id,
            'article_title': title,
            'author': author,
            'date': date,
            'content': content,
            'ip': ip,
            'message_conut': message_count,
            'messages': messages
        }

        return json.dumps(data, sort_keys=True, ensure_ascii=False)


def process_command():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', metavar=('BOARD_NAME'), type=str,
                        required=True, help='enter board name')
    parser.add_argument('-i', metavar=('START_INDEX', 'END_INDEX'),
                        type=int, required=True, nargs=2, help="Start and end index , input -1 to the latest page")

    args = parser.parse_args()
    PttWebCrawler(board=args.b, start=args.i[0], end=args.i[1])

    return parser.parse_args()


if __name__ == '__main__':
    process_command()
