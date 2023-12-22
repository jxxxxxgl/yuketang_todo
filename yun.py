from datetime import timedelta
import datetime
import requests,sys
import time,base64,json
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By

CourseUrl=""
SCKEY = ""
options = Options()
# options.add_argument("--headless")
# options.add_argument('--disable-gpu')
options.add_experimental_option("excludeSwitches",["enable-logging"])
options.add_argument('-ignore-certificate-errors')
options.add_argument('-ignore -ssl-errors')
service = Service("chromedriver.exe")
driver = webdriver.Chrome(service=service,options = options)

driver.implicitly_wait(10)

# 解决特征识别.因为服务器识别到的selenium的特征。使用该两行代码更改了特征，即可以顺利通过识别
script = 'Object.defineProperty(navigator, "webdriver", {get: () => false,});'
driver.execute_script(script)


course_list = [] # 所有课程列标
classRoomUrlList = [] # 课程链接

headers = {
    'Host': 'changjiang.yuketang.cn',
    'Cookie': '自己的Cookie',
    'Sec-Ch-Ua-Mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
    'Xt-Agent': 'web',
    'Accept': 'application/json, text/plain, */*',
    'Xtbz': 'ykt',
    'University-Id': '0',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://changjiang.yuketang.cn/v2/web/index?date=1683377919531&newWeb=1',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
}

def login(username , password,command):
    baseurl = 'https://changjiang.yuketang.cn/web?next=/v2/web/index&type=3'
    driver.get(baseurl)
    time.sleep(3)

    # 账号密码登录
    driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[2]/div[1]/img').click()
    driver.find_element(By.XPATH,
                        '/html/body/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[1]/div[1]/div[1]/input').send_keys(
        username)
    driver.find_element(By.XPATH,
                        '/html/body/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]/div[1]/div/input').send_keys(
        password)
    driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[2]/div[2]/div[2]/div[5]').click()

    time.sleep(10)

    # 切换到验证码的 iframe 中
    iframe = driver.find_element(By.XPATH, "//iframe[@class='tcaptcha-iframe']")
    driver.switch_to.frame(iframe)

    # 绕过滑块（识别滑块坐标，并滑动滑块）
    hua_img_block = driver.find_element(By.ID,'slideBlock')
    distance = 215 # 201 px
    action = ActionChains(driver)
    action.click_and_hold(hua_img_block).perform() # 点击初始滑块位置并保持不释放
    action.drag_and_drop_by_offset(hua_img_block,distance,0).perform()
    time.sleep(10)

    # getUserInfo()
    # getCourseInfo()
    # 切换回到上层 iframe
    driver.switch_to.parent_frame()
    # # 强制等待 10 秒，进入登入界面
    time.sleep(5)
    if command == '1':
        auto_ppt_play(CourseUrl)
    elif command == '2':
        getUpdateCourse()
'''
获取个人信息
'''
def getUserInfo():
    url = 'https://changjiang.yuketang.cn/v2/api/web/userinfo'
    response = requests.get(url=url,headers=headers)

    user_id = json.loads(response.text)["data"][0]["user_id"]
    user_name = json.loads(response.text)["data"][0]["name"]
    nowtime = (datetime.datetime.now())
    sys.stdout.write("用户"  + user_name + "在" + str(nowtime) + "执行了脚本")
    '''
    鉴权
    '''
'''
获取课程Url
'''
def getCourseInfo():
    classRoomRequestUrl = 'https://changjiang.yuketang.cn/v2/api/web/courses/list?identity=2'
    classRoomBaseUrl = 'https://changjiang.yuketang.cn/v2/web/studentLog/'


    classroom_id_response = requests.get(url=classRoomRequestUrl , headers=headers)
    course_list = []
    for ins in json.loads(classroom_id_response.text)["data"]["list"]:
        course_list.append({
            "course_name": ins["course"]["name"],
            "classroom_id": ins["classroom_id"],
            "course_sign": ins["university_course_series_id"],
            "course_id": ins["course"]["id"]
        })


    for course in course_list:
        classroomid = course['classroom_id']
        classRoomUrl = classRoomBaseUrl + str(classroomid)
        classRoomUrlList.append(classRoomUrl)
'''
筛选符合条件json
'''
def filter_by(json , **kwargs):
    params = kwargs
    for key in params:
        if json.get(key) != params[key]:
            return False
    return True
'''
获取有更新的课程
'''
def getUpdateCourse():
    # 截止作业提醒数组
    todo_course = []

    for classRoomUrl in classRoomUrlList:
        driver.get(classRoomUrl)
        todo_course_only = []

        classroom_id=classRoomUrl.split("/")[-1]

        '''
        课程列表
        '''
        course_list_web = driver.find_elements(By.CLASS_NAME,'activity__wrap el-tooltip')
        for course in course_list_web:
            try:
                deadLine = course.find_element(By.CLASS_NAME,'beforeBorder blue')
                deadLine_time_day = deadLine.text.split("\"")[3].split("/")[0]
                deadLine_time_day_clock = deadLine.text.split("\"")[3].split("/")[1]
                deadLine_time = deadLine_time_day + deadLine_time_day_clock

                # 根据课程房间号 获取 课程信息
                course_name = list(filter(lambda x: filter_by(x, classroom_id=classroom_id), course_list))['course_name']
                h2Tag = course.find_element(By.TAG_NAME,'h2').txt


                '''
                判断时间， 如果小于等于1天，就提醒
                '''
                nowtime = str(datetime.datetime.now()).split(" ")[0] +'/' + str(datetime.datetime.now()).split(" ")[1]
                nowtime = datetime.strptime(nowtime, '%Y-%m-%d/%H:%M')
                deadLine_time_datetime = datetime.strptime(deadLine_time, '%Y-%m-%d/%H:%M')

                delta = deadLine_time_datetime - nowtime
                if delta < timedelta(days=1):
                    print("时间差小于一天")
                    '''
                    进行提醒
                    '''
                    reminder = '课程名字 \n' +'\n' + course_name + '\n'+ '课时' + h2Tag + '截止时间' + '\n'+deadLine_time
                    send_messsage(reminder)
                else:
                    print("时间差大于或等于一天")
            except Exception:
                print('无法找到')
                pass
def send_messsage(message):
    url = ("https://sctapi.ftqq.com/{}.send").format(SCKEY)
    params = {
        "text": "雨课堂消息提醒",
        "desp": message,
    }

    response = requests.post(url, json=params)
    print(response.text)
'''
自动翻ppt
'''
def auto_ppt_play(CourseUrl):
    if CourseUrl == "":
        for classRoomUrl in classRoomUrlList:
            driver.get(classRoomUrl)
            content_box = driver.find_elements(By.CLASS_NAME,'content-box')
            content_box_num = content_box.count()
            for i in range(1, content_box_num + 1):
                time.sleep(3)
                xpath = (
                    "/html/body/div[4]/div[2]/div/div[1]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div/section[{}]/div/div[2]/section").format(
                    i)
            try:
                driver.find_element(By.XPATH, xpath).click()
                time.sleep(3)
                try:
                    driver.find_element(By.CLASS_NAME,
                                        "ppt_img_box").click()
                    time.sleep(1)
                    # 执行js，让滚轮向下滚动
                    img_list = driver.find_elements(By.CLASS_NAME, "thumbImg-container")
                    for i in img_list:
                        i.click()
                        time.sleep(10)
                    driver.forward(CourseUrl)
                    driver.refresh()
                except Exception:
                    print("无")
                    driver.back()
                    driver.refresh()
                driver.forward(CourseUrl)
                driver.refresh()
            except Exception:
                print("下一步：\n")
                driver.forward(CourseUrl)
                driver.refresh()

    else:
        driver.get(CourseUrl)
        time.sleep(5)
        content_box = driver.find_elements(By.CLASS_NAME, 'content-box')
        content_box_num = len(content_box)
        for i in range(1, content_box_num + 1):
            time.sleep(3)
            xpath = (
                "/html/body/div[4]/div[2]/div/div[1]/div[2]/div[2]/div[2]/div[2]/div[2]/div[1]/div/section[{}]/div/div[2]/section").format(
                i)
            try:
                driver.find_element(By.XPATH, xpath).click()
                time.sleep(3)
                try:
                    driver.find_element(By.CLASS_NAME,
                                        "ppt_img_box").click()
                    time.sleep(1)
                    # 执行js，让滚轮向下滚动
                    img_list = driver.find_elements(By.CLASS_NAME, "thumbImg-container")
                    for i in img_list:
                        i.click()
                        time.sleep(10)
                    driver.get(CourseUrl)
                    driver.refresh()
                except Exception:
                    print("无")
                    driver.back()
                    driver.refresh()
                driver.get(CourseUrl)
                driver.refresh()
            except Exception:
                print("下一步：\n")
                driver.get(CourseUrl)
                driver.refresh()
        driver.close()

'''
自动签到
'''
def sign_online_class():
    pass


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description='请输入账号密码：')
    parser.add_argument('-U', '--username',required=True , help='雨课堂账号')
    parser.add_argument('-P', '--password',required=True, help='雨课堂密码')
    parser.add_argument('-M', '--model', default='1',required=True ,help='雨课堂操作 1 -> PPT自动浏览 ； 2 -> 执行雨课堂作业提醒功能')
    parser.add_argument('-C', '--curl', help='PPT网址')
    args = parser.parse_args()
    username = args.username
    password = args.password
    command = args.model
    curl = args.curl
    if curl == "":
        CourseUrl = ""
    else:
        CourseUrl = curl
        print(CourseUrl)
    login(username,password,command)
