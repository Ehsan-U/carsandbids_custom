from ast import arg
from concurrent.futures import ThreadPoolExecutor
import queue
import time
from urllib.parse import parse_qsl, urljoin
from scrapy.selector import Selector
import selenium
from seleniumwire.utils import decode 
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver
from selenium.webdriver.common.proxy import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from rich.console import Console
import random
import json
from openpyxl import Workbook
from openpyxl.styles.fonts import Font
from openpyxl.styles import PatternFill
import string
import threading
import argparse
from bs4 import BeautifulSoup



class Cars():
    def __init__(self,url):
        self.base = url
        self.not_required = ['seller','body style','seller type','drivetrain']
        self.current_listings = queue.Queue()
        self.newcars = set()
        # self.current_listings = set()
        self.con = Console()
        self.once = True
        self.counter = 0
        self.page_count = 1
        self.offset = 0
        self.ch_options = Options()
        self.ch_options.add_argument("--headless")
        self.ch_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36")
        self.proxy_pool = ['http://yuuvqogr-rotate:9h2mhn3nphde@p.webshare.io:80/','http://bimxecpq-rotate:c1nqqly3v05y@p.webshare.io:80/','http://hjdkysch-rotate:iwfapn45qbcm@p.webshare.io:80/']
        self.proxy = random.choice(self.proxy_pool)
        self.wireoptions = {
        "proxy":{
        "http":f"{self.proxy}",
        "https":f"{self.proxy}"
        }
        }

    # def parse(self,response):
    #     soup = BeautifulSoup(response,'html.parser')
    #     links = soup.find_all("a",attrs={"class":"hero"})
    #     for link in links:
    #         # if len(link['class']) == 1:
    #         url = urljoin(self.base,str(link['href']))
    #         print(url)
    #         self.newcars.add(url)
    #         self.current_listings.put(url)

    # extracting urls for current listings
    def new_cars(self,url):
        driver = webdriver.Chrome(executable_path="/home/lubuntu/custom_car/chromedriver",options=self.ch_options,seleniumwire_options=self.wireoptions)
        driver.request_interceptor = self.interceptor
        try:
            driver.get(url)
            element = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CLASS_NAME,"paginator")))
            # element = WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn btn-lg btn-primary with-paging')))
        except Exception:
            driver.close()
            self.new_cars(url)
        else:
            try:
                for req in driver.requests:
                    if "/v2/autos/auctions?limit" in req.url:
                        body = req.response.body
                        data = decode(body,req.response.headers.get("Content-Encoding","identity"))
                        resp = json.loads(data)
                        count = resp.get("count")
                        self.total = resp.get("total")
                        for i in range(count):
                            key = resp['auctions'][i].get("id")
                            value = resp['auctions'][i].get("title").replace(" ","-")
                            car = f"https://carsandbids.com/auctions/{key}/{value}" 
                            self.current_listings.put(car)
                            # self.current_listings.add(car)
                        self.con.print(f"Total urls >>[bold] {self.total}", f"Loaded urls >> [bold] {self.current_listings.qsize()}")
            except Exception:
                driver.close()
                self.new_cars(url)
    def interceptor(self,request):
        text_string = "/v2/autos/auctions?limit"
        if text_string in request.url:
            request.url = request.url.replace("limit=12","limit=100")

    # parsing each car page
    def get_page(self,lock,url):
        driver = webdriver.Chrome(executable_path="/home/lubuntu/custom_car/chromedriver",options=self.ch_options,seleniumwire_options=self.wireoptions)
        driver.get(url)
        data = {}
        # p = sync_playwright().start()
        # browser = p.chromium.launch(headless=True)
        # page = browser.new_page()
        try:
            element = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CLASS_NAME,"quick-facts")))
        except Exception:
            # print('retrying')
            driver.close()
            self.get_page(lock,url)
        else:
            resp = driver.page_source
            driver.close()
            # resp = page.content()
            sel = Selector(text=resp)
            year = sel.xpath("//div[@class='auction-title']/h1/text()").get()[:4]
            raw_title = sel.xpath("//div[@class='auction-title']/h1/text()").get()
            raw_subtitle = sel.xpath("//div[@class='d-md-flex justify-content-between flex-wrap']/h2/text()").get()
            if sel.xpath("//div[@class='d-md-flex justify-content-between flex-wrap']//h2/span").get():
                no_reserver = "True"
            else:
                no_reserver = "False"
            source = url
            price = sel.xpath("//span[@class='value']/span[@class='bid-value']/text()").get()
            main_image = sel.xpath("//div[@class='preload-wrap main loaded']/img/@src").get()
            images = ",".join(sel.xpath("//div[@class='preload-wrap  loaded']/img/@src").getall())
            if "kilometers" in sel.xpath("//div[@class='detail-wrapper']").get().lower():
                kilometers = "True"
            else:
                kilometers = "False"
            dt_tags = sel.xpath("//div[@class='quick-facts']//dt")
            dd_tags = sel.xpath("//div[@class='quick-facts']//dd")
            for dt,dd in zip(dt_tags,dd_tags):
                if dd.xpath(".//a"):
                    with lock:
                        not_required = self.not_required
                    if not dt.xpath(".//text()").get().lower() in not_required:
                        data[dt.xpath(".//text()").get()] = dd.xpath(".//a/text()").get()
                else:
                    if not dt.xpath(".//text()").get().lower() in not_required:
                        if dt.xpath(".//text()").get() == "Mileage":
                            raw_miles = dd.xpath(".//text()").get()
                            if "TMU" in raw_miles:
                                tmu = "True"
                            else:
                                tmu = "False"
                            Mileage = ''
                            miles_characters = list(dd.xpath(".//text()").get())
                            for c in miles_characters:
                                if c.isdigit():
                                    Mileage +=c
                            data["Mileage"] = Mileage
                        else:
                            data[dt.xpath(".//text()").get()] = dd.xpath(".//text()").get()
            data['Year'] = year
            data['URL'] = source
            data["Raw_Title"] = raw_title
            data["Raw_Subtitle"] = raw_subtitle
            data["Raw_Mileage"] = raw_miles
            data["Price"] = price
            data["Source"] = url
            data["TMU"] = tmu
            data["No_Reserve"] = no_reserver
            data["Kilometers"] = kilometers
            data["Main-Image"] = main_image
            data["Images"] = images
            self.save_to_excel(data,lock)

    # extracting urls for past listings
    def past_cars(self,url):
        driver = webdriver.Chrome(executable_path="/home/lubuntu/custom_car/chromedriver",options=self.ch_options,seleniumwire_options=self.wireoptions)
        driver.request_interceptor = self.pastinterceptor
        try:
            driver.get(url)
            element = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CLASS_NAME,"paginator")))
            # element = WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn btn-lg btn-primary with-paging')))
        except Exception:
            driver.close()
            self.new_cars(url)
        else:
            try:
                for req in driver.requests:
                    if "/v2/autos/auctions?limit" in req.url:
                        body = req.response.body
                        data = decode(body,req.response.headers.get("Content-Encoding","identity"))
                        resp = json.loads(data)
                        count = resp.get("count")
                        self.total = resp.get("total")
                        for i in range(count):
                            key = resp['auctions'][i].get("id")
                            value = resp['auctions'][i].get("title").replace(" ","-")
                            car = f"https://carsandbids.com/auctions/{key}/{value}" 
                            self.current_listings.put(car)
                            # self.current_listings.add(car)
                            self.con.print(f"Total urls >>[bold] {self.total}", f"Loaded urls >> [bold] {self.current_listings.qsize()}")
            except Exception:
                driver.close()
                self.new_cars(url)
    def pastinterceptor(self,request):
        text_string = "/v2/autos/auctions?limit"
        if text_string in request.url:
            request.url = request.url.replace("limit=50&status=closed&",f"limit=100&status=closed&offset={self.offset}&")
            self.offset+=50

    def save_to_excel(self,data,lock):
        with lock:
            if self.once:
                self.once = False
                self.wb = Workbook()
                self.wb.active.title = "Cars"
                self.Cars = self.wb.active
                keys = list(data.keys())
                values = list(data.values())
                self.Cars.append(keys)
                self.Cars.append(values)
                letters = list(string.ascii_uppercase)[:len(keys)]
                for letter in letters:
                    self.Cars[f"{letter}1"].font = Font(bold=True)
            else:
                values = list(data.values())
                self.Cars.append(values)

    def run_new(self,lock,load=True):
        if load:
            self.new_cars("https://carsandbids.com/")
        threads = []
        qsize = self.current_listings.qsize()
        while not self.current_listings.empty():
            self.counter+=1
            url = self.current_listings.get()
            # self.con.print(f"Thread Started >> {url}")
            t = threading.Thread(target=self.get_page,args=(lock,url))
            t.daemon = True
            threads.append(t)
            t.start()
            if self.counter%10 == 0:
                break
        for t in threads:
            t.join()
        self.con.print(f"[bold green]Processed Items [cyan]{self.counter}:[bold green] Remaining Items [cyan]{self.current_listings.qsize()}")
        if self.current_listings.empty():
            self.wb.save("Cars.xlsx")
            self.con.print("[+] File Saved")
        else:
            if self.counter==100:
                self.run_new(lock,True)
            else:
                self.run_new(lock,False)
    
    def run_past(self,lock,load=True):
        if load:
            self.past_cars("https://carsandbids.com/past-auctions/")
        threads = []
        qsize = self.current_listings.qsize()
        while not self.current_listings.empty():
            self.counter+=1
            url = self.current_listings.get()
            # self.con.print(f"Thread Started >> {url}")
            t = threading.Thread(target=self.get_page,args=(lock,url))
            t.daemon = True
            threads.append(t)
            t.start()
            if self.counter%10 == 0:
                break
        for t in threads:
            t.join()
        self.con.print(f"[bold green]Processed Items [cyan]{self.counter}:[bold green] Remaining Items [cyan]{self.total-self.counter}")
        if self.current_listings.empty() and self.counter >= self.total:
            self.wb.save("Cars.xlsx")
            self.con.print("[+] File Saved")
        else:
            if self.counter==100:
                self.run_past(lock,True)
            else:
                self.run_past(lock,False)
    def argss(self):
        args = argparse.ArgumentParser()
        args.add_argument('-m','--mode',dest='mode',help="give 'new' for current listings\n'past' for old listings")
        values = args.parse_args()
        value = vars(values)
        return value
lock = threading.Lock()
c = Cars("https://carsandbids.com")
args = c.argss()
if args.get("mode") == "past":
    c.con.print("[+ bold ] Staring crawler for past listings..")
    c.run_past(lock)
else:
    c.con.print("[default][bold] Staring crawler for current listings..")
    c.run_new(lock)
