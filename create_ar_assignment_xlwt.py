import xlwt

DATA = (
(0,"Apple","img/apple.png",),
(1,"Banana","img/banana.png",),
(2,"Goldfish","img/goldfish.png",),
(3,"Lemon","img/lemon.png",),
(4,"Mushroom","img/mushroom.png",),
(5,"Orange","img/orange.png",),
(6,"Pineapple","img/pineapple.png",),
(7,"Pumpkin","img/pumpkin.png",),
)

wb = xlwt.Workbook()
ws = wb.add_sheet("ar_assignment")
for i, row in enumerate(DATA):
    for j, col in enumerate(row):
        ws.write(i, j, col)
#    ws.col(0).width = max([len(row[0]) for row in DATA])
wb.save("ar_assignment.xls")

