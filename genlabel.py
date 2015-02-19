# -*- coding: utf-8 -*-
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import qrcode
from PIL import ImageOps
from PIL import Image
import sys

img_w = 531
img_h = 171

device_id = sys.argv[1]

url = u'http://iolggr.appspot.com/devices/{}'.format(device_id)

def get_qr_matrix(url):
    qr = qrcode.QRCode(version=None, error_correction=qrcode.ERROR_CORRECT_M, border=0)
    qr.add_data(url)
    qr.make(fit=True)
    return qr.get_matrix()

class pixels():
    def __init__(self):
        # self.img = Image.open('./test1.png','r')
        self.img = Image.new('RGB',(img_w,img_h),color=(255,255,255))
        self.w = self.img.size[0]
        self.h = self.img.size[1]
        print '{}x{}'.format(self.w,self.h)
        self.pixels = self.img.load()

    def __getitem__(self,item):
        try:
            return self.pixels[item[0],item[1]][0]
        except:
            print item[0]
            print item[1]
            print self.w
            print self.h
            raise

    def __setitem__(self, key, value):
        try:
            self.pixels[key[0],key[1]] = (value,value,value)
        except:
            print key[0]
            print key[1]
            print self.w
            print self.h
            raise


matrix = get_qr_matrix(url)
m_size = len(matrix)
p = pixels()

scale = 5
offset_x = 270
offset_y = 3

def set_pixel(i_x,i_y,v):
    for x in range(scale):
        for y in range(scale):
            p[i_x*scale + x + offset_x,
              i_y*scale + y + offset_y] = 255 if v is False else 0

for x in range(m_size):
    for y in range(m_size):
        set_pixel(x,y,matrix[x][y])

draw = ImageDraw.Draw(p.img)
font = ImageFont.truetype("helvetica/HelveticaNeueBold.ttf", 15)
small_font = ImageFont.truetype("helvetica/HelveticaNeueBold.ttf", 13)
large_font = ImageFont.truetype("helvetica/HelveticaNeue.ttf", 20)
title_font = ImageFont.truetype("helvetica/HelveticaNeueBold.ttf", 21)

def draw_row(text,offset,font=font):

    txt=Image.new('RGB',(500,20),'white')
    d = ImageDraw.Draw(txt)
    d.text((0, 0),text,(0,0,0),font=font)
    w=txt.rotate(-90,  expand=0)
    p.img.paste( w, (offset,0))


draw_row(' Device: {}'.format(device_id),465)
draw_row(' http://iolggr.appspot.com',200,font=small_font)


def draw_big(text,row,font=large_font):
    draw.text((20,row*20+5),text,(0,0,0),font=font)


draw_big("2 blinks:",0)
draw_big("Needs wifi setup",1)
draw_big("Network: ESP",2)
draw_big("Pass: ESP12345",3)
draw_big("& goto http://192.168.4.1",4,font=small_font)

draw_big("Glowing every 2",5.2)
draw_big("minutes=Working",6.2)

draw_row(" iolggr: temp wifi ",514, font=title_font)

# p.img = p.img.rotate(-90)
p.img.save('./test.jpg',format='jpeg')
# p.img.save('./test.png',format="png")
