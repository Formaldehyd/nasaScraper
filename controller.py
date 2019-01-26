# This class is supposed to controll and sceduale the downloads.

import os
import sys
import datetime
import logging
import time
import mysql.connector
sys.path.append(os.getcwd()) # assuming that all files are in the same directory
import pictureGetter # contains the class day to download and save the picture of one day.


class controller:
    def __init__(self, daysCompleted = 0):

        self.logger = logging.getLogger()
        self.baseURL = 'https://apod.nasa.gov/apod/'
        self.basedir = '~/Desktop/'
        self.firstDate = datetime.date(1995,6,16)
        self.number = daysCompleted
        self.daysCompleted = datetime.timedelta(days = daysCompleted)
        self.cnx = mysql.connector.connect(user='nasa', password='nasa', host='127.0.0.1', database = 'nasa')
        self.cursor = self.cnx.cursor()


    def justAnOtherDay(self):
        try:
            day = pictureGetter.day(number = self.number, date = self.firstDate + self.daysCompleted, basedir = self.basedir, baseurl = self.baseURL, cursor = self.cursor)
        except pictureGetter.DayFailed as err:
            print('day Failed.')
            self.logger.error('Day Failed :{};{}'.format(err, self.firstDate + self.daysCompleted))

    def addDay(self, daysToAdd = 1):
        self.daysCompleted = self.daysCompleted + datetime.timedelta(days = daysToAdd)
        self.cnx.commit()
        self.number = self.number + 1

try:
    with open(os.getcwd() + '/NASA.log', 'w') as file:
        file.write('')
except FileNotFoundError as err:
    pass


logging.basicConfig(filename = os.getcwd() + '/NASA.log')
controller = controller(0)
for i in range(1,15):
    controller.addDay()
    controller.justAnOtherDay()
    time.sleep(10)

