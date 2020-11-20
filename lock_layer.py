#!/usr/bin/env python3
# -*-coding:utf-8-*-
_header = {
    '说明':
        '''
#-----------------------------------#
#	Orbotech CS Software Group		#
#-----------------------------------#

@File 		: 	lock_layer
@Author		:	River
@Date		:	2020/11/6 14:05
@Sofeware   :   PyCharm
@Purpose	:	料号锁层并写记录到MySQL数据库

#-----------------------------------#
'''
}

# Import standard Python modules

import base64
import os
import platform
import sys
from itertools import chain

import pymysql
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QApplication, QWidget, QHeaderView, QMessageBox

from lock import Ui_Form

if platform.system().lower() == 'windows':
    sys.path.append(r'C:\Python37\Lib\site-packages\cam')
    from cam import incam
elif platform.system().lower() == 'linux':
    sys.path.append(r'/incam/server/site_data/scripts/python/cam')
    import incam


class Mw(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setFixedSize(self.width(), self.height())  # 禁止窗口最大化和禁止窗口拉伸
        self.camdb = 'cam_data'
        self.cam_table = 'cam_job'
        self.conn = pymysql.connect(host="localhost", port=3306, user="root", passwd="root", db=self.camdb,
                                    charset="utf8")

        self.layer_list = []
        self.checkbox = []
        self.widget = []
        self.layer_hasp = {}
        # self.jobname = str(os.environ['JOB'])
        self.jobname = 'k4f02481as'
        self.defind_ui()
        self.source_mysql_data()
        self.defind_table()

    def defind_ui(self):
        # 加载incam图片
        png_path = os.path.dirname(os.path.realpath(__file__)) + '/incam.png'
        ff1 = open(png_path)
        image = ff1.read()
        ff1.close()
        img = QtGui.QPixmap()
        img.loadFromData(base64.b64decode(image))
        self.ui.L1.setPixmap(img)
        icon_path = os.path.dirname(os.path.realpath(__file__)) + '/icp_icon.png'
        ff2 = open(icon_path)
        image = ff2.read()
        ff2.close()
        icon = QtGui.QPixmap()
        icon.loadFromData(base64.b64decode(image))
        self.setWindowIcon(QtGui.QIcon(icon))
        self.ui.L4.setText('> ' + self.jobname + ' <')
        self.ui.B1.clicked.connect(self.update_mysql)
        self.ui.B2.clicked.connect(self.closed)

    def defind_table(self):
        self.ui.tableWidget.setHorizontalHeaderLabels(['上锁', '工作层'])
        # self.layer_list = self.get_work_layer()
        self.layer_list = ['l2', 'l3', 'ss', 'sm']
        self.ui.tableWidget.setRowCount(len(self.layer_list))
        self.ui.tableWidget.setColumnCount(2)
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        for i in range(len(self.layer_list)):
            self.widget.append(QWidget())
            self.checkbox.append(QtWidgets.QCheckBox())
            # self.checkbox[i].setCheckState(QtCore.Qt.Unchecked)
            self.checkbox[i].setText('  ')  # checkbox只能点击check框和旁边的文本才能选中
            hlayout = QtWidgets.QHBoxLayout()
            hlayout.addWidget(self.checkbox[i])
            hlayout.setContentsMargins(0, 0, 0, 0)  # 设置边缘距离 否则会很难看
            hlayout.setAlignment(QtCore.Qt.AlignCenter)
            self.widget[i].setLayout(hlayout)
            name = QtWidgets.QTableWidgetItem(self.layer_list[i])
            name.setTextAlignment(QtCore.Qt.AlignCenter)
            self.ui.tableWidget.setCellWidget(i, 0, self.widget[i])
            self.ui.tableWidget.setItem(i, 1, name)

            if self.layer_list[i] in self.layer_hasp.keys():
                self.checkbox[i].setCheckState(QtCore.Qt.Checked)
                self.widget[i].setStyleSheet("background-color: rgb(255, 255, 0);")
                self.ui.tableWidget.item(i, 1).setBackground(QBrush(QColor(255, 255, 0)))
            else:
                self.checkbox[i].setCheckState(QtCore.Qt.Unchecked)
                self.widget[i].setStyleSheet("background-color: rgb(255, 255, 255);")
                self.ui.tableWidget.item(i, 1).setBackground(QBrush(QColor(255, 255, 255)))

            self.checkbox[i].stateChanged.connect(self.click)

    def click(self):
        for i in range(len(self.layer_list)):
            if self.checkbox[i].isChecked():
                self.widget[i].setStyleSheet("background-color: rgb(255, 255, 0);")
                self.ui.tableWidget.item(i, 1).setBackground(QBrush(QColor(255, 255, 0)))
            else:
                self.widget[i].setStyleSheet("background-color: rgb(255, 255, 255);")
                self.ui.tableWidget.item(i, 1).setBackground(QBrush(QColor(255, 255, 255)))

    def get_work_layer(self):
        board_layer = []
        f = incam.InCAM()
        info = f.DO_INFO('-t matrix -e %s/matrix -d ROW' % self.jobname)
        layer_names = info['gROWname']
        layer_context = info['gROWcontext']

        for i in range(len(layer_names)):
            if layer_context[i] == 'board':
                board_layer.append(layer_names[i])

        return board_layer

    def source_mysql_data(self):
        cur = self.conn.cursor()
        cur.execute("SELECT jobname FROM %s" % self.cam_table)
        data1 = cur.fetchall()
        global mysql_job
        mysql_job = list(chain.from_iterable(data1))

        if self.jobname in mysql_job:
            # print('yes')
            sql = "SELECT lock_layer FROM %s WHERE jobname = '%s'"
            cur.execute(sql % (self.cam_table, self.jobname))
            data2 = cur.fetchall()
            mysql_job_layer = list(chain.from_iterable(data2))
            mysql_job_layers = str(mysql_job_layer[0]).split(';')
            for layer in mysql_job_layers:
                self.layer_hasp[layer] = 1

    def update_mysql(self):
        # print('test')
        new_lock_layers = []
        for i in range(len(self.layer_list)):
            if self.checkbox[i].isChecked():
                new_lock_layers.append(self.layer_list[i])
        new_lock_layer = ';'.join(new_lock_layers)
        cur = self.conn.cursor()
        if self.jobname in mysql_job:
            print(new_lock_layer)
            sql = "UPDATE  %s SET  lock_layer = '%s' WHERE jobname = '%s'"
            cur.execute(sql % (self.cam_table, new_lock_layer, self.jobname))
            self.conn.commit()
        else:
            sql = "INSERT INTO %s (jobname,lock_layer) values ('%s','%s')"
            cur.execute(sql % (self.cam_table, self.jobname, new_lock_layer))
            self.conn.commit()

        self.confirmed()

    def confirmed(self):
        info = QMessageBox.information(self, '提示', '已上锁成功！', QMessageBox.Ok)

    def closed(self):
        self.conn.close()
        QApplication.quit()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '提示', '你确定要退出吗?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            self.conn.close()
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication([])
    mainw = Mw()
    mainw.show()
    app.exec_()
