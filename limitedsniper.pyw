import sys
import re
import time
import roblopy
import PyQt5
import threading
import requests
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic

app = QApplication(sys.argv)
hat_icon = QIcon(QPixmap("ic-hat-white.png"))
face_icon = QIcon(QPixmap("ic-face-white.png"))
gear_icon = QIcon(QPixmap("ic-gear-white.png"))
wrench_icon = QIcon(QPixmap("wrench.png"))
script_icon = QIcon(QPixmap("script.png"))
boat_icon = QIcon(QPixmap("DBIcon.ico"))
loggedin = False
client = roblopy.RobloxApiClient()
class LMainWindow(QMainWindow):
    def highlightGreen(self,item,rap,aid):
        sellers = None
        try:
            sellers = client.getSellers(aid)['data']['Resellers']
        except:
            return None
        prices = []
        for seller in sellers:
            prices.append(seller['Price'])
        if len(prices) > 0:
            lowest = min(prices)
            if lowest < rap:
                g = (255 * ((rap - lowest)/rap)) * 3.5
                item[0].setBackground(QColor(38,g,38))
    def keyPressEvent(self,qKeyEvent):
        if qKeyEvent.key() == Qt.Key_Return: 
            searchterm = self.searchbar.text()
            catalogresults = client.catalogSearch(keyword = searchterm, category = 2,freq=3,sort=0,currency=1,notforsale=False,pagenumber=1)
            catalogresults +=client.catalogSearch(keyword = searchterm, category = 2,freq=3,sort=0,currency=1,notforsale=False,pagenumber=2)
            threads = []
            values = []
            for result in catalogresults:
                length = len(values)
                values.append([0])
                threads.append(threading.Thread(target = client.getRAP,args = (result['AssetId'],values[length])))
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            window.limitedlist.clear()
            for ind, result in enumerate(catalogresults):
                icon = None
                if result['AssetTypeID'] in [8,41,42,43,44,45,46]:
                    icon = hat_icon
                elif result['AssetTypeID'] == 19:
                    icon = gear_icon
                elif result['AssetTypeID'] == 18:
                    icon = face_icon
                else:
                    icon = hat_icon
                item = QListWidgetItem(icon,"{} | {} R$".format(result['Name'],values[ind][0]))
                item.setToolTip(str(result['AssetId']))
                thr = threading.Thread(target=self.highlightGreen,args=([item],values[ind][0],str(result['AssetId'])))
                self.limitedlist.addItem(item)
                thr.start()
        else:
            super().keyPressEvent(qKeyEvent)

    def itemDbClick(self,item):
        tx= item.text()
        aid = item.toolTip()
        firstbar = tx.find('| ')
        rap = tx[firstbar+2:tx.find(' R$'):]
        name=tx[:tx.find(' |'):]
        sellers = [0]
        thumbnail = ['']
        def gsellers(aid,ref):
            ref[0] = client.getSellers(aid)
        def thumb(aid,ref):
            url = "https://www.roblox.com/Thumbs/Asset.ashx?width=110&height=110&assetId={}".format(aid)
            ref[0] = requests.get(url).content
        sellerthread = threading.Thread(target=gsellers,args=(aid,sellers))
        ththread = threading.Thread(target=thumb,args=(aid,thumbnail))
        sellerthread.start()
        ththread.start()
        sellerthread.join()
        ththread.join()
        try:
            sellers = sellers[0]
            thumbnail = thumbnail[0]
            if 'data' not in sellers.keys() or not sellers['data']:
                return None
            prices = []
            for seller in sellers['data']['Resellers']:
                prices.append(seller['Price'])
            lowest = min(prices)
            self.lowestprice.setText(str(lowest))
            self.rap.setText(str(rap))
            self.hatname.setText(name)
            js=client.s.get("https://api.roblox.com/currency/balance").json()
            self.balance.setText(str(js['robux']))
            with open('temp.jpg','wb') as thumbnailf:
                thumbnailf.write(thumbnail)
            pix = QPixmap()
            pix.loadFromData(thumbnail)
            self.hatthumb.setPixmap(pix)
            self.hatthumb.setToolTip("{} {}".format(aid,lowest))
        except Exception as e:
            print(type(e),e)

    def sniep(self):
        try:
            info = self.hatthumb.toolTip()
            if not info:
                return None
            infol = info.split(' ')
            aid = infol[0]
            desiredprice=infol[1]
            r=client.snipeLimited(aid,int(desiredprice))
            js=r.json()
            if js['statusCode'] == '500':
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setMinimumSize(300,200)
                msg.setWindowIcon(wrench_icon)
                msg.about(self,"Insufficient Funds","Not Enough ROBUX")
            return r
        except Exception as e:
            print(type(e),e)
        
    def __init__(self):
        super(LMainWindow, self).__init__()
        uic.loadUi('mainwindow.ui', self)
        self.style().SH_ToolTip_WakeUpDelay = 1
        self.hatname.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored)
        self.limitedlist.itemDoubleClicked.connect(self.itemDbClick)
        self.snipebutton.clicked.connect(self.sniep)
        self.setWindowIcon(boat_icon)
        self.show()

class LoginWindow(QMainWindow):
    def logIn(self):
        r = client.logIn(self.username.text(),self.password.text())
        if r.url == "https://www.roblox.com/home?nl=true":
            loggedin = True
            self.close()
        else:
            msg=QMessageBox()
            msg.about(self,"Incorrent Credentials","Your username and password are not valid.")
    def __init__(self):
        super(LoginWindow, self).__init__()
        uic.loadUi('loginprompt.ui', self)
        self.loginButton.clicked.connect(self.logIn)
        self.password.setEchoMode(QLineEdit.Password)
        self.setWindowIcon(script_icon)
        self.show()

window = LMainWindow()
login = LoginWindow()
sys.exit(app.exec_())
