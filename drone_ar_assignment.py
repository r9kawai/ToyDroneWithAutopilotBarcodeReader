import xlrd
import cv2

class Drone_AR_assignment:
    def __init__(self):
        self.wb = xlrd.open_workbook('ar_assignment.xls')
        self.sheet = self.wb.sheet_by_name('ar_assignment')
        self.list = self.get_list_2d_all(self.sheet)
        self.imglist = []

        for row in self.list:
            print('read img : ', row[2])
            img = cv2.imread(row[2])
            self.imglist.append(img)

    def get_list_2d_all(self, sheet):
        return [sheet.row_values(row) for row in range(sheet.nrows)]

    def ar_to_name(self, code):
        return(self.list[code][1])

    def ar_to_img(self, code):
        img = self.imglist[code]
        return(img)

#eof

