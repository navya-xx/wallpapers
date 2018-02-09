#!/usr/bin/python
# Created by NavyaJapani (github- navya-xx)
from __future__ import division
import feedparser
import re
import os
import urllib2
# import Image
from HTMLParser import HTMLParser
from PIL import Image, ImageFont, ImageDraw
import textwrap

# import pdb
# pdb.set_trace()

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def text_overlay(imgfile, file_path, title, text):
    font = ImageFont.truetype("/usr/share/fonts/opentype/freefont/FreeSans.otf", 20)
    font_bold = ImageFont.truetype("/usr/share/fonts/opentype/freefont/FreeSansBold.otf", 20)
    im = Image.open(imgfile).convert('RGBA')
    # Get image size
    w,h = im.size
    w_lim = 1920
    r = h/w
    im = im.resize((w_lim,int(r*w_lim)), resample=Image.BICUBIC)
    w,h = im.size
    if text is not None:
        # wrap text
        lines = textwrap.wrap(text, width=100)
        max_width = 0
        _, height = font.getsize(title)
        margin = 20
        for line in lines:
            wl, hl = font.getsize(line)
            if max_width < wl:
                max_width = wl
            height += hl
        
        draw = ImageDraw.Draw(im, 'RGBA')
        cpos_h = 0
        draw.text((w-max_width-margin/2,h-height+cpos_h-margin/2), title, fill=(255,255,255,255), font=font_bold)
        for line in lines:
            wl, hl = font.getsize(line)
            cpos_h += hl
            draw.text((w-max_width-margin/2,h-height+cpos_h-margin/2) ,line, fill=(255,255,255,255), font=font)
    im.save(file_path, 'PNG')

path = os.path.join(os.getcwd(),"wallpapers")
RSS_FEEDS = {'apod':['https://apod.nasa.gov/apod.rss'], 'reddit':['https://www.reddit.com/r/wallpaper/.rss']}
temp_file = os.path.join(path, "temp.jpg")

# f = feedparser.parse('https://apod.nasa.gov/apod.rss')

# pattern_imgurl = re.compile('src=\"([^\"]*)\"')
pattern_img = {'apod':[], 'reddit':[]}
pattern_desc = {'apod':[], 'reddit':[]}
pattern_img['apod'].append(re.compile('\<a\shref=\"([^\"]+)\"[^>]*>\n?<img\ssrc=\"[^\"]+\"[^>]+><\/a>', re.I|re.S|re.M))
pattern_desc['apod'].append(re.compile('Explanation:(.+?)Tomorrow\'s\spicture:', re.S))
pattern_img['reddit'].append(re.compile('<span><a\s*href=\"([^\"]+)\">\[link\]<\/a>', re.I|re.S|re.M))
pattern_desc['reddit'].append(None)

for (category, links) in RSS_FEEDS.iteritems():
    for i,link in enumerate(links):
        feed = feedparser.parse(link)
        for item in feed.entries:
            title = item.title
            print("Saving Image: " + title)
            if category == 'apod':
                web_link = item.link
                html_data = urllib2.urlopen(web_link).read()
                desc = strip_tags(pattern_desc[category][i].findall(html_data)[0])
                desc = re.sub("\n+"," ", desc)
                # print(desc)
                img_link = pattern_img[category][i].findall(html_data)[0]
                img_link = "https://apod.nasa.gov/apod/" + img_link
                print(img_link)
            elif category == 'reddit':
                img_link = pattern_img[category][i].findall(item.content[0].value)[0]
                desc = None
                print(img_link)
            
            if not (img_link[-3:] == "jpg" or img_link[-3:] == "JPG"):
                continue

            img_filename = img_link.split("/")[-1]
            filepath = os.path.join(path, img_filename)[:-4] + ".png"
            if os.path.isfile(filepath):
                continue
            # Download image
            try:
                filedata = urllib2.urlopen(img_link)
                data = filedata.read()
                with open(temp_file, 'w') as fimg:
                    fimg.write(data)
                text_overlay(temp_file, filepath, title, desc)
                # raw_input("Next...")
                print('Image saved!')
            except Exception as e:
                print('Failed to save image')
                print(e)

os.remove(temp_file)
