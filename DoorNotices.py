from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
import json
import tkinter as tk
from tkinter import simpledialog

import sys
import os
import time
class DoorNotices:
    def __init__(self):
        self.driver = None       
        self.json_path = os.path.join(os.getcwd(), "notification.json")
        if not os.path.exists(self.json_path):
            # 파일이 없는 경우, 파일을 생성
            with open(self.json_path, 'w') as f:
                # 파일에 초기 내용을 작성하려면 여기에 작성
                f.write("")

    def ask_password(self):
        root = tk.Tk()
        root.withdraw()  # 메인 창 숨기기
        # 화면이 가장 위로 올라오도록 설정
        root.attributes('-topmost', True)
        password = simpledialog.askstring("Password", "Enter password:", show='*')
        root.attributes('-topmost', False)
        return password

    def table_parsing(self, url:str, lecture_room_number:int, col_index:int) -> list:
        # 주소와 강의실번호를 조합하여 방문
        self.driver.get(url + str(lecture_room_number))

        # 방문한 페이지의 html을 가져온다
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # 클래스가 'tbl_type'인 테이블 요소 찾기
        table = soup.find('table', class_='tbl_type')
        
        # 테이블의 번호와 제목을 저장할 리스트
        table_items = []
        # 테이블 속의 공지 제목을 저장할 리스트
        table_title = []
        # 테이블 속의 공지 번호를 저장할 리스트 
        table_numbers = []

        # 테이블의 행을 가져온다
        table_rows = table.find_all('tr')
        # 테이블의 첫 행은 항목이기 때문에 무시
        if len(table_rows) > 1:
            # 테이블의 열을 가져온다
            table_cols = table_rows[1].find_all('td')
            # 테이블의 열이 1개 이상이라면
            if len(table_cols) > 1:
                # 테이블의 각 행별로 반복
                for row in table_rows[1:]:
                    # 테이블의 각 행의 제목을 파싱
                    table_name = row.find_all('td')[col_index].text.strip()  # 공지 제목 위치
                    table_number = row.find_all('td')[0].text.strip()  # 공지 번호
                    table_title.append(table_name)
                    table_numbers.append(table_number)

        # 파싱한 결과를 반환
        table_items.append(table_title)
        table_items.append(table_numbers)
        return table_items


    # DB에서 json을 받아온다
    def get_json(self) -> dict:
        json_data = {}
        # 파일에서 JSON 데이터를 읽어온다고 가정
        try:
            with open(self.json_path, "r", encoding="utf-8") as temp_txt:
                # 파일에서 JSON 데이터를 읽어와 딕셔너리로 변환한다
                json_data = json.load(temp_txt)
        except json.JSONDecodeError:
            return json_data    

        return json_data


    # 유저의 정보가 아예 없는경우 json생성
    def make_json(self, semester:str, lecture_names:list) -> dict:
        # 강의학기, 강의 이름 목록
        # 학기 항목 추가
        data = {
            semester:{}
        }
        
        for lecture in lecture_names:
            temp = {
                lecture:{
                    "과제": 0,
                    "수업활동일지": 0,
                    "팀프로젝트 결과": 0,
                    "공지사항": 0,
                    "강의자료": 0,
                    "알림": 0
                }
            }
            data[semester].update(temp)

        return data

    # 파싱 데이터와 json데이터를 비교하여 달라진게 있으면 알림을 보냄
    def compare_and_notify_changes(self, lecture_notice_list:list, semester:str, lecture:str, menu:str, json_data:dict, color:str):
        found = False
        reset = '\033[0m'
        if len(lecture_notice_list[0]) == 0:
            return json_data, found
        
        if menu == "과제":
            # 파싱한 공지의 개수 - 알림을 보내 공지 개수
            new_notify_count = len(lecture_notice_list[0]) - json_data[semester][lecture][menu]
            for i in range(1, new_notify_count + 1):
                # 알림 처리로직 추가
                print(f"{color}{menu}{reset}: \"{lecture_notice_list[0][-i]}\"")
                found = True
                json_data[semester][lecture][menu] += 1
        elif menu == "공지":
            # 공지에는 공지번호 말고도 "알림"이라는 것이 존재하기 때문에 따로 처리가 필요하다
            alarm_count = 0
            # "알림" 처리
            for i in lecture_notice_list[1]:
                if i == "알림":
                    alarm_count += 1
            # 보내지 않은 "알림"공지를 보낸다
            if alarm_count > json_data[semester][lecture]["알림"]:
                for i in range(alarm_count - json_data[semester][lecture]["알림"]):
                    # 알림 처리로직 추가
                    print(f"{color}{menu}{reset}: \"{lecture_notice_list[0][-i]}\"")
                    found = True
                    json_data[semester][lecture]["알림"] += 1
            
            # 보내지 않은 공지를 보낸다
            notify_count = lecture_notice_list[1][alarm_count] - json_data[semester][lecture][menu]
            if notify_count > 0:
                for i in range(alarm_count, alarm_count + notify_count):
                    # 알림 처리로직 추가
                    print(f"{color}{menu}{reset}: \"{lecture_notice_list[0][-i]}\"")
                    found = True
                    json_data[semester][lecture][menu] += 1

        else:
            new_notify_count = int(lecture_notice_list[1][0]) - json_data[semester][lecture][menu]
            if new_notify_count > 0:
                for i in range(new_notify_count):
                    # 알림 처리로직 추가
                    print(f"{color}{menu}{reset}: \"{lecture_notice_list[0][i]}\"")
                    found = True
                    json_data[semester][lecture][menu] += 1
    
        return json_data, found
        


    def run_door_crawling(self):
        # 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # headless 모드 설정
        chrome_options.add_argument("--log-level=3") # 로그 제거
        self.driver = webdriver.Chrome(options=chrome_options)
        os.system('cls') 
        print('\033[96m'+'Door 접속')
        print('\033[0m',end="")
        # 웹 페이지로 이동
        login_url = "https://door.deu.ac.kr/sso/login.aspx"
        self.driver.get(login_url)
        
        # 아이디와 비밀번호
        print("ID: ", end="")
        id = input()
        pw = self.ask_password()

        # 계정정보 존재 유무 확인
        if len(id) != 0 and len(pw) != 0:
            # 아이디 입력
            id_input = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/form/div[2]/div[1]/div/table/tbody/tr[1]/td[2]/input')))
            id_input.send_keys(id)

            # 비밀번호 입력
            pw_input = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/form/div[2]/div[1]/div/table/tbody/tr[2]/td/input')))
            pw_input.send_keys(pw)
        else:
            print('아이디와 비밀번호 데이터가 없습니다.')
            return

        print('로그인 시도 중...')
        try:
            # 로그인 버튼 클릭
            login_button = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/form/div[2]/div[1]/div/table/tbody/tr[1]/td[3]/a')))
            login_button.click()
            
        except TimeoutException:
            print('로그인 버튼을 찾을 수 없거나 클릭할 수 없습니다.')
            return
        except Exception as e:
            print("로그인 도중 오류가 발생했습니다")
            return
        
        print('로그인 성공!')
        time.sleep(1)
        try:
            # 강의실로 이동
            self.driver.get('http://door.deu.ac.kr/MyPage')

            # 강의 목록을 가져옴
            lecture_list_selector = "#wrap > div.subpageCon > div:nth-child(3) > div:nth-child(3) > table"
            lecture_list = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, lecture_list_selector)))

            # lecture_list를 BeautifulSoup으로 파싱
            soup = BeautifulSoup(lecture_list.get_attribute('outerHTML'), 'html.parser')

            # 강의 목록에서 강의 이름 추출
            lecture_names = []
            lecture_room_numbers = []
            lecture_count = 0
            semester = None

            # 강의 목록이 비어있는 경우에 대한 예외 처리
            lecture_rows = soup.find_all('tr')
            if len(lecture_rows) > 1:  # 강의 목록에 최소 두 개의 행이 존재하는 경우
                # 강의 학기
                semester = lecture_rows[1].find_all('td')[0].text.strip() # 강의 학기
                for row in lecture_rows[1:]:  # 첫 번째 행은 헤더이므로 무시
                    room_number = row.find('a')['href'].split("'")[1]
                    lecture_room_numbers.append(room_number)
                    lecture_name = row.find_all('td')[2].text.strip()  # 세 번째 열이 강의 이름
                    lecture_names.append(lecture_name)
                lecture_count = len(lecture_names)
            else:
                print("강의목록이 비어있습니다.")
                return
            
            # json 관련 처리
            print("이전 공지 데이터를 확인하는 중...")
            json_data = self.get_json()

            # DB에서 json을 받아와 처리
            # json데이터가 존재하는지 확인
            if json_data:
                # json_data에 이번 학기 정보가 존재하는지 확인
                if not semester in json_data:
                    json_data = self.make_json(semester, lecture_names)
            else:
                print("데이터를 새로 생성합니다.")
                json_data = self.make_json(semester, lecture_names)
            
            # 크롤링할 주소와 그 주소에 존재하는 테이블의 제목 위치
            urls = [
                ["http://door.deu.ac.kr/LMS/LectureRoom/CourseHomeworkStudentList/", 2, "과제", "\033[94m"],
                ["http://door.deu.ac.kr/LMS/LectureRoom/CourseOutputs/", 1, "수업활동일지", "\033[92m"],
                ["http://door.deu.ac.kr/LMS/LectureRoom/CourseTeamProjectStudentList/", 1, "팀프로젝트 결과", "\033[95m"],
                ["http://door.deu.ac.kr/BBS/Board/List/CourseNotice?cNo=", 2, "공지사항", "\033[93m"],
                ["http://door.deu.ac.kr/BBS/Board/List/CourseReference?cNo=", 2, "강의자료", "\033[91m"]
            ]
            os.system('cls') 
            # 새로운 공지 확인 시작
            for i in range(2, lecture_count + 2):
                print('\033[96m'+lecture_names[i-2])
                print('\033[0m',end="")
                # 강의 공지가 1개라도 있는지 확인하기 위한 변수
                found = False
                # 강의실 1개 마다 urls에 들어있는 모든 링크를 방문한다
                for url in urls:
                    # 메뉴 이름 저장
                    menu = url[2]
                    # 강의실에서 방문할 링크, 강의실 번호, 제목의 위치를 보내 파싱한다.
                    lecture_notice_list = self.table_parsing(url[0], lecture_room_numbers[i-2], url[1])
                    if found:
                        json_data, temp= self.compare_and_notify_changes(lecture_notice_list, semester, lecture_names[i-2], menu, json_data, url[3])
                    else:
                        json_data, found= self.compare_and_notify_changes(lecture_notice_list, semester, lecture_names[i-2], menu, json_data, url[3])

                if not found:
                    print("새로운 공지가 없습니다!")
                print()

        except TimeoutException:
            print("요소를 찾을 수 없거나 연결 시간이 초과되었습니다.")
            return 
        except Exception as e:
            print("오류가 발생했습니다:%s", e)
            return 
        print('\033[0m',end="")
        with open("notification.json","w",encoding="utf-8") as temp_txt:
            temp_txt.write(json.dumps(json_data))    

        print('\033[96m'+'공지 확인 완료')
        print('\033[0m',end="")
        
        # 프로그램 종료
        sys.exit()

if __name__ == "__main__":
    a = DoorNotices()
    a.run_door_crawling()
    