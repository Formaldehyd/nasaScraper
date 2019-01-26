import logging
import urllib.response
import urllib.error
import bs4
import datetime
import os
import hashlib
import mysql.connector



class DayFailed(Exception):
    """an exception to terminate work on the current day, should be caught either in the day itself or in the main code."""


class day:
    # For every day I want to create a class that holds and collects the information
    # then i want to write this information to the database and dump the picture to the NAS

    def __init__(self, date, cursor, number, basedir, baseurl):
        self.cursor = cursor
        self.number = number
        self.logger = logging.getLogger() # the root logger
        self.date = date # date must be a datetime object from wich I'll form the url
        self.basedir = basedir
        self.baseURL = baseurl
        self.url = None
        self.html = None
        self.soup = None
        self.title = None
        self.explanation = None
        self.artist = None # im not sure how i can extract these. Mabye later.
        self.pictureLink = None
        self.pictureType = None
        self.picture = None
        self.pictureDir = None
        self.nonce = '' # an empty string to alter the hash in case there is a file colission. No very efficient solution, but will do the job
        self.query = ("INSERT INTO metadata "
            "(id, year, month, day, title, artist, explanation, filename) VALUES "
            "({} {} {} {} {} {} {} {});")




        self.formURL()
        self.openURL()
        self.readHTML()
        self.downloadPicture()
        self.savePicture()
        self.writeDatabase()

    def readHTML(self):
        self.soup = bs4.BeautifulSoup(self.html,features='lxml')

        self.title = self.soup.title.string.split(' - ')[1]
        while self.title[-1] == ' ':
            self.title = self.title[:-1]

        #if not ('Explanation:' in self.soup.text and 'Copyright:' in self.soup.text):
        # selecting the photografer: Every page has the strinc 'Copyright:'. However in some pages it is followed with a newline
        # charakter and in some pages directly with the information
        #selecting the Explanation is a little difficult.
        # newer versions of the page have a paragraph starting with 'Explanation:'.
        # actually most of the images seem to use this version, therefor I'll implement this as a main test and if this does not work I'll just save all text

        for paragraph in self.soup.find_all('p'):
            if 'Copyright: ' in paragraph.text:
                self.artist = paragraph.text.split('Copyright: ')[1]
            elif 'Credit: ' in paragraph.text:
                self.artist = paragraph.text.split('Credit: ')[1]

            if 'Explanation: ' in paragraph.text:
                self.explanation = paragraph.text.split('Explanation: ')[1]

        if (self.explanation is None or self.artist is None):
            self.explanation = self.soup.text.split('Explanation: ')[1]
            self.logger.error('Explanation or Copyright not found: {}, {}'.format(str(self.date.year)+'-'+str(self.date.month)+'-'+str(self.date.day) ,self.url))
            #raise DayFailed # for now i dont want to kill the day


        for link in self.soup.find_all('a'):
            print(link.get('href'))
            if '.jpg' in link.get('href'):
                self.pictureLink = self.baseURL + link.get('href')
                self.pictureType = 'jpg'
                break

            elif '.gif' in link.get('href'):
                print('true')
                self.pictureLink = self.baseURL + link.get('href')
                self.pictureType = 'gif'
                break

        if self.pictureLink is None:
            self.logger.error('Unknown picture type and link!')
            raise DayFailed



    def downloadPicture(self):
        if self.pictureLink is None: # should never happen
            self.logger.error('No Picture link provided')
            raise DayFailed
        try:
            with urllib.request.urlopen(self.pictureLink) as response:
                self.picture = response.read()
        except urllib.error.URLError as err:
            self.logger.error("Hm. Shouldn't have happened. SAD: {}; {}".format(self.pictureLink, err))
            raise DayFailed


    def savePicture(self):
        # For now I'll save the pictures on the filesystem. I'll take the basedir, and disribute the pictures in subfolders by month.
        # The filename will be the hash of the picturs title and a timestamp. Should be unique

        if not os.path.exists(self.basedir + str(self.date.month) + '/'): # ensures the directory exists
            os.makedirs(self.basedir + str(self.date.month) + '/')

        while os.path.isfile(self.basedir + str(self.date.month) + '/' + hashlib.md5((self.nonce + self.title).encode('utf-8')).hexdigest()+self.pictureType):
            # collission, an other file with this name already exists:
            self.nonce = self.nonce + 'a'

        else:
            with open(self.basedir + str(self.date.month) + '/' + hashlib.md5((self.nonce + self.title).encode('utf-8')).hexdigest(), 'wb') as file:
                self.pictureDir = str(self.date.month) + '/' + hashlib.md5((self.nonce + self.title).encode('utf-8')).hexdigest()#+self.pictureType
                file.write(self.picture)


    def writeDatabase(self):
        # for now I dont want to create a Database, since I first have to move the DAtabase
        # Ill just write the information to a formatted file
        #with open(self.basedir + '/information/' + str(self.date)+'.txt','w') as file:
        #    file.write(self.title)
        #    file.write('<++>'+self.artist)
        #    file.write('<++>'+self.explanation) 
        data = [str(self.number), str(self.date.year), str(self.date.month), str(self.date.day)]
        if self.title:
            data.append(self.title)
        else:
            data.append('None')
        if self.artist:
            data.append(self.artist)
        else:
            data.append('None')
        if self.explanation:
            data.append(self.explanation)
        else:
            data.append('None')
        data.append(hashlib.md5((self.nonce + self.title).encode('utf-8')).hexdigest())

        self.cursor.execute(self.query.format(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7]))
        self.cursor.commit()

    def openURL(self):
        # read in the response and store the pure html.
        try:
            with urllib.request.urlopen(self.url) as response:
                self.html = response.read()

        except urllib.error.HTTPError as err:
            # httperro is derived from urlerror, this catch is for if i want more specific handling of httperrors
            self.logger.error('HTTPError; date {}; url {}; {}'.format(str(self.date.year)+'-'+str(self.date.month)+'-'+str(self.date.day), self.url, err))
            raise DayFailed

        except urllib.error.URLError as err:
            self.logger.error('URLError; date {}; {}'.format(str(self.date.year)+'-'+str(self.date.month)+'-'+str(self.date.day), err))
            raise DayFailed



    def formURL(self):
        l = [self.baseURL]
        l.append('ap') # for some reason the url is more than just the base url with the date. 

        if self.date.year % 100 < 10:
            l.append('0')
            l.append( str(self.date.year % 100))
        else:
            l.append( str(self.date.year % 100))

        if self.date.month < 10:
            l.append('0')
            l.append(str(self.date.month))
        else:
            l.append(str(self.date.month))

        if self.date.day < 10:
            l.append('0')
            l.append(str(self.date.day))
        else:
            l.append(str(self.date.day))

        l.append('.html')
        self.url = ''.join(l)
