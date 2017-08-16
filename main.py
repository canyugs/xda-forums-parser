from lxml import html
import datetime
import json
import re
import requests

XDA_FORUMS_URL = 'https://forum.xda-developers.com/'
XDA_TOP_DEVICE_XPATH = '//ul[@class="algoliahomedeviceimages"]/li/a[@class="device-result"]'
XDA_THREAD_ROW_XPATH = '//div[@class="thread-listing"]/div[@class="thread-row"]'

def write_file(filename, dict_data):
    with open(filename, 'w') as f:
        json_data = json.dumps(dict_data, ensure_ascii=False)
        f.write(json_data)
    return json_data


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
    
    tree = get_page_tree(XDA_FORUMS_URL)
    devices_link = tree.xpath(XDA_TOP_DEVICE_XPATH)

    # get top devices name
    print 'Top Devices'
    top_devices = []

    for element in devices_link:
        name = element.get('href').split('/')[-1]
        top_devices.append(name)

    print top_devices

    data = get_all_thread_in_device(top_devices[0])
    data_json = json.dumps(data, ensure_ascii=False)

    print data_json

    write_file(top_devices[0], data)
