#!/usr/bin/python
# Created by NavyaJapani (github- navya-xx)
"""
Wallpaper saver
1. Parse image from RSS feed
2. Add entry to json list, update list ever month to remove old wallpapers
3. Save wallpapers to specific folder
"""
from __future__ import division
import feedparser
import re
import json
import os, sys
import urllib2
from HTMLParser import HTMLParser
from PIL import Image, ImageFont, ImageDraw
import textwrap
from datetime import datetime

#import pdb; pdb.set_trace();

DATE_FORMAT = "%d.%m.%y %H:%M:%S"
DATE_DIFF = 30
MIN_IMAGE_WIDTH = 1920
MIN_SIZE_MB = 0.5

path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])),"wallpapers")
RSS_FEEDS = {   'apod'  :['https://apod.nasa.gov/apod.rss'], 
                'reddit':[
                            'https://www.reddit.com/r/wallpaper/.rss',
                            'https://www.reddit.com/r/MinimalWallpaper/.rss', 
                            'https://www.reddit.com/r/EarthPorn/.rss'
                        ]
            }
temp_file = os.path.join(path, "temp.jpg")
JSON_FILE = os.path.join(path, "list.json")

def flush_json(jfile):
    try:
        data = json.load(open(jfile))
    except:
        print("failed to open JSON file")
        return []
    present = datetime.now()
    for item in data:
        import_date = datetime.strptime(item['import_date'], DATE_FORMAT)
        time_diff = (present - import_date).days
        if time_diff > DATE_DIFF:
            file_name = item['filename']
            os.remove(file_name)
            data.remove(item)
    return data

# Extract data
global json_data
json_data = flush_json(JSON_FILE) 

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

def save_json(data, jfile):
    with open(jfile, 'w') as jf:
        json.dump(data, jf)

def add_to_json(entry):
    json_data.insert(0, entry)
    return data

def check_json(filepath):
    for item in json_data:
        if item['filename'] == filepath:
            return True
    return False

def text_overlay(imgfile, file_path, title, text):
    font = ImageFont.truetype("/usr/share/fonts/opentype/freefont/FreeSans.otf", 20)
    font_bold = ImageFont.truetype("/usr/share/fonts/opentype/freefont/FreeSansBold.otf", 20)
    if os.stat(imgfile).st_size/1024/1024 < MIN_SIZE_MB:
        print("Image size is too small.")
        return
    im = Image.open(imgfile).convert('RGBA')
    # Get image size
    w,h = im.size
    if w < MIN_IMAGE_WIDTH:
        print("Image is too small. Skipping!")
        return
    w_lim = MIN_IMAGE_WIDTH
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
    add_to_json({'filename':file_path, 'import_date':datetime.now().strftime(DATE_FORMAT)})

# pattern_imgurl = re.compile('src=\"([^\"]*)\"')
pattern_img = {'apod':[], 'reddit':[]}
pattern_desc = {'apod':[], 'reddit':[]}
pattern_img['apod'].append(re.compile('\<a\shref=\"([^\"]+)\"[^>]*>\n?<img\ssrc=\"[^\"]+\"[^>]+><\/a>', re.I|re.S|re.M))
pattern_desc['apod'].append(re.compile('Explanation:(.+?)Tomorrow\'s\spicture:', re.S))
pattern_img['reddit'].append(re.compile('<span><a\s*href=\"([^\"]+)\">\[link\]<\/a>', re.I|re.S|re.M))
pattern_desc['reddit'].append(None)


for (category, links) in RSS_FEEDS.iteritems():
    for i,link in enumerate(links):
        print("-------------------------------\nExtracting images from %s\n---------------------------" % link)
        feed = feedparser.parse(link)
        for item in feed.entries:
            title = item.title
            print("\nSaving Image: " + title)
            if category == 'apod':
                web_link = item.link
                html_data = urllib2.urlopen(web_link).read()
                desc = strip_tags(pattern_desc[category][0].findall(html_data)[0])
                desc = re.sub("\n+"," ", desc)
                # print(desc)
                img_link = pattern_img[category][0].findall(html_data)[0]
                img_link = "https://apod.nasa.gov/apod/" + img_link
                print(img_link)
            elif category == 'reddit':
                img_link = pattern_img[category][0].findall(item.content[0].value)[0]
                desc = None
                print(img_link)
            
            if not (img_link[-3:] == "jpg" or img_link[-3:] == "JPG" or img_link[-3:] == "png" or img_link[-3:] == "PNG"):
                print("Image type not supported!")
                continue

            img_filename = img_link.split("/")[-1]
            filepath = os.path.join(path, img_filename)[:-4] + ".png"
            
            # Check is file already exist
            #if os.path.isfile(filepath):
            #    continue
            if check_json(filepath):
                print("Already exist!")
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
save_json(json_data, JSON_FILE)
os.remove(temp_file)


