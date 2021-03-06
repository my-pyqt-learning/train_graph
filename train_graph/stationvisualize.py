"""
车站股道占用情况可视化图表。
暂时不考虑单线情况。
"""

import sys
from PyQt5 import QtWidgets,QtCore,QtGui
from PyQt5.QtCore import Qt
from .graph import Graph
from datetime import datetime,timedelta

class StationGraphWidget(QtWidgets.QGraphicsView):
    def __init__(self,station_list,graph,station_name,mainWindow):
        super().__init__()
        self.scene = QtWidgets.QGraphicsScene()
        self.station_name = station_name
        mainWindow.stationVisualSizeChanged.connect(self._repaint)
        self.seconds_per_pix = 15
        self.row_height = 40
        self.down_list = [[], ]
        self.up_list = [[], ]
        self.single_list = [[],]
        self.margins = {
            "left": 60,
            "right": 20,
            "top": 50,
            "bottom": 50
        }
        self.setScene(self.scene)
        self.setAlignment(Qt.AlignLeft|Qt.AlignTop)
        self.graph = graph

        self._doubleLine = True  #按双线铺画
        self._allowMainStay = False  #正线停车准许
        self._sameSplitTime = 0  #单位：分钟
        self._oppositeSplitTime = 0

        self.station_list = station_list
        self._makeList()
        self._initUI()

    def allowMainStay(self):
        return self._allowMainStay

    def setAllowMainStay(self,allow:bool):
        self._allowMainStay = allow

    def doubleLine(self):
        return self._doubleLine

    def setDoubleLine(self,isDouble:bool):
        if isDouble == self._doubleLine:
            return
        self._doubleLine=isDouble
        self._makeList()

    def sameSplitTime(self):
        return self._sameSplitTime

    def setSameSplitTime(self,minute):
        self._sameSplitTime = minute

    def oppositeSplitTime(self):
        return self._oppositeSplitTime

    def setOppositeSplitTime(self,minute):
        self._oppositeSplitTime = minute

    def rePaintGraphAdvanced(self):
        self._makeList()
        self._initUI()

    def _repaint(self,seconds_per_pix:int=-1):
        if seconds_per_pix != -1:
            self.seconds_per_pix = seconds_per_pix
        self._initUI()

    def _makeList(self):
        """
        将数据分别放入list中
        list<dict>
        dict{
            "ddsj":datetime,
            "cfsj":datetime,
            "down":bool,
            "train":Train,
        }
        :return:
        """
        self.down_list = [[],]
        self.up_list = [[],]
        self.single_list = [[],]
        for train_dict in self.station_list:
            train_dict["ddsj"].date().replace(1900,1,1)
            train_dict["cfsj"].date().replace(1900,1,1)
            if train_dict["cfsj"] < train_dict["ddsj"]:
                #跨日处理
                new_dict = {
                    "ddsj":datetime(1900,1,1,0,0,0),
                    "cfsj":train_dict["cfsj"],
                    "down":train_dict["down"],
                    "train":train_dict["train"],
                    "station_name":train_dict["station_name"]
                }
                train_dict["cfsj"] = datetime(1900, 1, 1, 23, 59, 59)
                self.station_list.append(new_dict)

            if self._isPassed(train_dict):
                self._addPassTrain(train_dict)
            else:
                self._addStopTrain(train_dict)

    def _isPassed(self,train_dict):
        if (train_dict["ddsj"]-train_dict["cfsj"]).seconds == 0:
            return True
        else:
            return False

    def _addPassTrain(self,train_dict):
        down = train_dict["down"]
        added = False
        if self._doubleLine:
            #双线铺画
            if down:
                for i,rail in enumerate(self.down_list):
                    if self._isIdle(rail,train_dict):
                        rail.append(train_dict)
                        added = True
                        break
                if not added:
                    new_rail = [train_dict,]
                    self.down_list.append(new_rail)
            else:
                for i,rail in enumerate(self.up_list):
                    if self._isIdle(rail,train_dict):
                        rail.append(train_dict)
                        added = True
                        break
                if not added:
                    new_rail = [train_dict,]
                    self.up_list.append(new_rail)
        else:
            #单线铺画
            for i,rail in enumerate(self.single_list):
                if self._isIdle(rail,train_dict):
                    rail.append(train_dict)
                    added = True
                    break
            if not added:
                new_rail = [train_dict,]
                self.single_list.append(new_rail)

    def _addStopTrain(self,train_dict):
        down = train_dict["down"]
        added = False
        if self._doubleLine:
            #双线铺画
            if down:
                for i, rail in enumerate(self.down_list):
                    if not self._allowMainStay and i == 0:
                        continue
                    if self._isIdle(rail, train_dict):
                        rail.append(train_dict)
                        added = True
                        break
                if not added:
                    new_rail = [train_dict, ]
                    self.down_list.append(new_rail)
            else:
                for i, rail in enumerate(self.up_list):
                    if not self._allowMainStay and i == 0:
                        continue
                    if self._isIdle(rail, train_dict):
                        rail.append(train_dict)
                        added = True
                        break
                if not added:
                    new_rail = [train_dict, ]
                    self.up_list.append(new_rail)
        else:
            #单线铺画
            for i, rail in enumerate(self.single_list):
                if not self._allowMainStay and i == 0:
                    continue
                if self._isIdle(rail, train_dict):
                    rail.append(train_dict)
                    added = True
                    break
            if not added:
                new_rail = [train_dict, ]
                self.single_list.append(new_rail)

    def _isIdle(self,rail:list,new_train):
        ddsj,cfsj = self._occupyTime(new_train)
        for train_dict in rail:
            arrive,depart = self._occupyTime(train_dict)  #已经占用的时间
            if new_train["down"] == train_dict["down"]:
                #同向车次，扣去同向间隔
                dt = timedelta(days=0,seconds=self._sameSplitTime*60)
            else:
                dt = timedelta(days=0, seconds=self._oppositeSplitTime * 60)
            if (ddsj > (arrive-dt) and ddsj < (depart+dt)) or (cfsj > (arrive-dt) and cfsj < (depart+dt)):
                return False
        return True

    def _occupyTime(self,new_train):
        if self._isPassed(new_train):
            ddsj = new_train["ddsj"] - timedelta(days=0,seconds=30)
            cfsj = new_train["cfsj"] + timedelta(days=0,seconds=30)
        else:
            ddsj = new_train["ddsj"]
            cfsj = new_train["cfsj"]
        ddsj.date().replace(1900,1,1)
        cfsj.date().replace(1900,1,1)
        return ddsj,cfsj

    def _initUI(self):
        self.scene.clear()
        gridColor = QtGui.QColor("#00FF00")
        defaultPen = QtGui.QPen(QtGui.QColor("#00FF00"),1)
        boldPen = QtGui.QPen(QtGui.QColor("#00FF00"),2)
        width = 24*3600/self.seconds_per_pix
        down_count = len(self.down_list)
        up_count = len(self.up_list)
        single_count = len(self.single_list)
        if self._doubleLine:
            height = self.row_height*(down_count+up_count)
        else:
            height = self.row_height*(single_count)
        self.scene.setSceneRect(0,0,self.margins["left"]+self.margins["right"]+width,
                                self.margins["top"]+self.margins["bottom"]+height)
        rectItem = self.scene.addRect(self.margins["left"],self.margins["top"],
                                      width,height)
        rectItem.setPen(defaultPen)

        self._initXAxis(width,height,gridColor)
        self._initYAxis(width,defaultPen,boldPen)
        self._addTrains()

    def _initXAxis(self,width,height,gridColor):
        pen_half = QtGui.QPen(gridColor, 1, Qt.DashLine)
        pen_hour = QtGui.QPen(gridColor, 2)
        pen_other = QtGui.QPen(gridColor, 1)

        lineItem = self.scene.addLine(self.margins["left"] - 15, 35, width + self.margins["left"] + 15, 35)
        lineItem.setPen(pen_hour)

        lineItem = self.scene.addLine(self.margins["left"] - 15, self.margins["top"]+height+15,
                                      width + self.margins["left"] + 15, self.margins["top"]+height+15)
        lineItem.setPen(pen_hour)


        for i in range(25):

            x = self.margins["left"] + i * 3600 / self.seconds_per_pix
            hour = i

            textItem1:QtWidgets.QGraphicsTextItem = self.scene.addText(str(hour))
            textItem2: QtWidgets.QGraphicsTextItem = self.scene.addText(str(hour))
            textItem1.setX(x-12)
            textItem1.setDefaultTextColor(gridColor)

            #下时间坐标
            textItem2.setX(x - 12)
            textItem2.setY(self.scene.height()-30)
            textItem2.setDefaultTextColor(gridColor)

            if i == 24:
                break

            # 画小时线，第一个不用画
            if i != 0:
                self.scene.addLine(x,self.margins["top"],x,self.margins["top"] + height,pen_hour)

            for j in range(1,6):
                x += 10*60/self.seconds_per_pix
                if j*10 == 30:
                    self.scene.addLine(x, self.margins["top"], x, self.margins["top"] + height, pen_half)
                else:
                    self.scene.addLine(x, self.margins["top"], x, self.margins["top"] + height, pen_other)

    def _initYAxis(self,width,defaultPen,boldPen):
        if self._doubleLine:
            down_count = len(self.down_list)
            up_count = len(self.up_list)
            for i in range(down_count):
                y = self.margins["top"]+(i+1)*self.row_height
                lineItem = self.scene.addLine(self.margins["left"],self.margins["top"]+(i+1)*self.row_height,
                                              self.margins["left"]+width,self.margins["top"]+(i+1)*self.row_height)
                if i == down_count-1:
                    lineItem.setPen(boldPen)
                else:
                    lineItem.setPen(defaultPen)
                rail_num = 2*down_count - 1 - 2*i
                textItem:QtWidgets.QGraphicsTextItem = self.scene.addText(str(rail_num)if rail_num != 1 else 'Ⅰ')
                textItem.setY(y-self.row_height/2-textItem.boundingRect().height()/2)

            for i in range(up_count):
                y = self.margins["top"]+(i+1)*self.row_height + down_count*self.row_height
                if i != up_count - 1:
                    lineItem = self.scene.addLine(self.margins["left"], y,
                                                  self.margins["left"] + width, y)
                    lineItem.setPen(defaultPen)

                rail_num = 2*i+2
                textItem: QtWidgets.QGraphicsTextItem = self.scene.addText(str(rail_num) if rail_num != 2 else 'Ⅱ')
                textItem.setY(y - self.row_height / 2 - textItem.boundingRect().height() / 2)
        else:
            #单线铺画
            single_count = len(self.single_list)
            for i in range(single_count):
                y = self.margins["top"] + (i + 1) * self.row_height

                lineItem = self.scene.addLine(self.margins["left"], y,
                                              self.margins["left"] + width, y)
                lineItem.setPen(defaultPen)

                rail_num = i+1
                textItem: QtWidgets.QGraphicsTextItem = self.scene.addText(str(rail_num) if rail_num != 1 else 'Ⅰ')
                textItem.setY(y - self.row_height / 2 - textItem.boundingRect().height() / 2)

    def _addTrains(self):
        start_y = self.margins["top"]
        if self._doubleLine:
            for down_rail in reversed(self.down_list):
                for train_dict in down_rail:
                    self._addTrainRect(train_dict,start_y)

                start_y += self.row_height

            for up_rail in self.up_list:
                for train_dict in up_rail:
                    self._addTrainRect(train_dict, start_y)

                start_y += self.row_height
        else:
            for single_rail in self.single_list:
                for train_dict in single_rail:
                    self._addTrainRect(train_dict,start_y)
                start_y += self.row_height

    def _addTrainRect(self,train_dict,start_y):
        ddsj, cfsj = self._occupyTime(train_dict)
        dd_x = self._xValueCount(ddsj)
        cf_x = self._xValueCount(cfsj)
        train = train_dict["train"]
        color = QtGui.QColor(train.color(self.graph))
        width = cf_x - dd_x
        rectItem: QtWidgets.QGraphicsRectItem = self.scene.addRect(dd_x, start_y, width, self.row_height)
        rectItem.setBrush(QtGui.QBrush(color))

        text = f"{train.fullCheci()} {train.stationDownStr(self.station_name,self.graph)} "
        if self._isPassed(train_dict):
            text += f"通过  {train_dict['ddsj'].strftime('%H:%M:%S')}"
        else:
            text += f"停车  {ddsj.strftime('%H:%M:%S')} — {cfsj.strftime('%H:%M:%S')}"
        text += f" {train_dict['station_name']}"
        rectItem.setToolTip(text)

    def _xValueCount(self,time:datetime):
        dt_int = (time-datetime(1900,1,1,0,0,0)).seconds
        dx = dt_int/self.seconds_per_pix
        return dx + self.margins["left"]