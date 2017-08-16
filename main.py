# -*- coding: utf-8 -*-

from lxml import html
import datetime
import json
import os
import re
import requests

XDA_FORUMS_URL = 'https://forum.xda-developers.com/'
XDA_TOP_DEVICE_FILENAME = 'top_devices'
XDA_TOP_DEVICE_XPATH = '//ul[@class="algoliahomedeviceimages"]/li/a[@class="device-result"]'
XDA_THREAD_ROW_XPATH = '//div[@class="thread-listing"]/div[@class="thread-row"]'


def write_file(filename, dict_data):
    with open(filename, 'w') as f:
        json_data = json.dump(dict_data, f)
    return json_data


def get_top_device():
    tree = get_page_tree(XDA_FORUMS_URL)
    devices_link = tree.xpath(XDA_TOP_DEVICE_XPATH)

    # get top devices name
    top_devices = []

    for element in devices_link:
        name = element.get('href').split('/')[-1]
        top_devices.append(name)

    devices_josn = json.dumps(top_devices)
    write_file(XDA_TOP_DEVICE_FILENAME, devices_josn)

    return top_devices


def read_top_device_from_file():
    path = os.path.join(os.path.curdir, XDA_TOP_DEVICE_FILENAME)

    # TODO why load data twice ?
    with open(path) as f:
        data = f.read()
    data_string = json.loads(data)
    data_list = json.loads(data_string)
    return data_list

def get_page_tree(url):
    page = requests.get(url)
    return html.fromstring(page.content)


def get_thread_data(thread_tree):
    thread = {}
    # get thread elements and setup thread dict
    icon, title, latest_post, counter = thread_tree.getchildren()

    # 0. id
    post_id = icon.get('id').split('_')[-1]

    # 1. title
    TITLE_XPATH = '*[@class="thread-title-cell"]/*[@class="threadTitle threadTitleUnread"]'

    thread['title'] = title.xpath(TITLE_XPATH)[0].text
    thread['link'] = title.base.strip('/') + title.xpath(TITLE_XPATH)[0].get('href')

    # 2. latest time 
    date = latest_post.xpath('a')[0].text

    if date == 'Today':
        date = str(datetime.date.today().strftime('%d %B %Y'))
    elif date == 'Yesterday':
        day = datetime.date.today() - datetime.timedelta(days=1)
        date = str(day.strftime('%d %B %Y'))

        thread['latest_post_time']  = date

    #3. replies and views
    count_strings = counter.text_content()
    result = re.findall(r'.*Replies: (?P<replies>\d.*)\r\n.*Views: (?P<views>\d.*)\r\n.*', count_strings)
    thread['replies'], thread['views'] = result[0]

    # 4. get time of created thread #2 time
    print 'get thread @ ' + thread['link']
    
    if thread['replies'] != 0:
        post_page = get_page_tree(thread['link'])
        try:
            second_post = post_page.xpath('//div[@class="postbit-wrapper "]')[2]
            timestamp = second_post.xpath('//div[@class="post-head-container"]/div[@class="post-head post-head-right"]/span[@class="time"]')[0]
            thread['#2_created_time'] = timestamp.text
        except IndexError:
            print 'No #2 post'
    else:
        thread['#2_created_time'] = 'None'

    return post_id, thread


def get_all_thread_in_device(device_name_in_fourm_link):
    device_threads = {} 
    # 1. go to development forum
    target_url = XDA_FORUMS_URL + device_name_in_fourm_link + '/development'
    tree = get_page_tree(target_url)
    print target_url

    # 2. get threads
    thread_list = tree.xpath(XDA_THREAD_ROW_XPATH) 

    # 3. get each thread data
    for thd in thread_list:
        post_id, thread = get_thread_data(thd)
        # setup one post
        device_threads[post_id] = thread

    return device_threads


if __name__ == '__main__':
    top_devices = read_top_device_from_file()
    print 'Top Devices: ', top_devices

    # Change index here for different device to test
    target_device = top_devices[1]
    print 'Target: ', target_device
    
    data = get_all_thread_in_device(target_device)
    print 'Result:'
    print data

    # 
    write_file(target_device, data)
