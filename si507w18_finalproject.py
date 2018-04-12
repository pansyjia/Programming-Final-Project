## 507 Final Project

#TripAdvisor
import requests
import webbrowser
import secrets
import sqlite3
import json
import csv
# import plotly.plotly as py
from bs4 import BeautifulSoup

CLIENT_ID = secrets.client_id
API_KEY = secrets.api_key

# ---------- Class Object -----
class Restaurant():
    def __init__(self, name, rating1="0", reviews="0", price="0", url=None):
        self.name = name
        self.rating1 = rating1
        self.reviews = reviews
        self.price = price
        self.url = url

        self.rating2 = "0"
        self.street = "123 Main St."
        self.city = "Ann Arbor"
        self.state = "MI"
        self.zip = "11111"
        self.lat = 0
        self.lng = 0

    def __str__(self):
        rest_str = "{}: {}, {}, {}({})".format(self.name, self.street, self.city, self.state, self.zip)
        return rest_str


# ---------- Caching ----------
CACHE_TRIPA = "cache_tripa.json"
CACHE_YELP = "cache_yelp.json"

try:
    cache_tripa_file = open(CACHE_TRIPA, "r")
    cache_tripa_contents = cache_tripa_file.read()
    TRIPA_DICTION = json.loads(cache_tripa_contents)
    cache_tripa_file.close()
except:
    TRIPA_DICTION = {}

def get_unique_key(url):
    return url



try:
    cache_yelp_file = open(CACHE_YELP, "r")
    cache_yelp_contents = cache_yelp_file.read()
    YELP_DICTION = json.loads(cache_yelp_contents)
    cache_yelp_file.close()
except:
    YELP_DICTION = {}

def params_unique_combination(baseurl, params):
    alphabetized_keys = sorted(params.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params[k]))
    return baseurl + "_".join(res)


def make_request_using_cache_crawl(url):
    unique_ident = get_unique_key(url)

    if unique_ident in TRIPA_DICTION:
        print("Fetching cached data...")
        return TRIPA_DICTION[unique_ident]
    else:
        # make the request and cache the new data
        print("Making a request for new data...")
        resp = requests.get(url)
        TRIPA_DICTION[unique_ident] = resp.text # only store the html
        dumped_json_cache_crawl = json.dumps(TRIPA_DICTION)
        fw = open(CACHE_TRIPA,"w")
        fw.write(dumped_json_cache_crawl)
        fw.close() # Close the open file
        return TRIPA_DICTION[unique_ident]




# # ---------- TripAdvisor Web Scraping & Crawling ----------

def get_rest_info():
    baseurl = "https://www.tripadvisor.com/Restaurants-g29556-Ann_Arbor_Michigan.html#EATERY_OVERVIEW_BOX"
    page_text = make_request_using_cache_crawl(baseurl)
    page_soup = BeautifulSoup(page_text, "html.parser")

    crawling_list = page_soup.find_all(class_="listing")[:10]
    rest_list = [] #a list to store the instances of Restaurant
    for rest in crawling_list:
        try:
            rest_name = rest.find(class_="property_title").text.replace("\n", "")
            rest_rating = rest.find(class_="ui_bubble_rating")["alt"].replace(" of 5 bubbles", "")
            rest_reviews = rest.find(class_="reviewCount").text.replace(" reviews \n", "")
            rest_price = rest.find(class_="item price").string
            detail_url = "https://www.tripadvisor.com" + rest.find("a")["href"]

            restaurant_ins = Restaurant(rest_name, rest_rating, rest_reviews, rest_price, detail_url)

            #scrape details
            details_page_text = make_request_using_cache_crawl(detail_url)
            details_page_soup = BeautifulSoup(details_page_text, "html.parser")
            street_info = details_page_soup.find(class_ = "street-address").text
            zip_info = details_page_soup.find(class_ = "locality").text.split(", ")[1][3:8]

            restaurant_ins.street = street_info
            restaurant_ins.zip = zip_info

            rest_list.append(restaurant_ins)
        except:
            print("Fail to creat instance list. ")
            continue


    return rest_list


# # ---------- Yelp API ----------
def get_from_yelp(rest_name):
    base_url = "https://api.yelp.com/v3/businesses/search"
    headers = {'Authorization': f"Bearer {API_KEY}"}
    parameters = {}
    parameters["term"] = rest_name
    parameters["location"] = "ann arbor"
    parameters["limit"] = 1
    unique_id = params_unique_combination(base_url, parameters)
    if unique_id in YELP_DICTION:
        print("Fetching cached yelp data...")
        return YELP_DICTION[unique_id]
    else:
        print("Making a yelp request for new data...")
        response = requests.get(base_url, params=parameters, headers=headers)
        resp_dict = json.loads(response.text)
        write_file = open(CACHE_YELP, 'w')
        write_file.write(json.dumps(resp_dict))
        write_file.close()
        return resp_dict


# use the names of the top 10 restaurants in TripAdvisor to
top_ten = get_rest_info()[:10]
yelp_list = []
for rest in top_ten :
    yelp_info = get_from_yelp(rest.name)["businesses"][0]
    yelp_list.append((yelp_info["name"], yelp_info["rating"], yelp_info["review_count"], yelp_info["coordinates"]["latitude"], yelp_info["coordinates"]["longitude"]))

with open('top_ten.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerows(yelp_list)



# ---------- Database ----------
DBNAME = "restaurants.db"
RESTJSON = "cache_tripa.json"
CSVFILE = "top_ten.csv"

def init_db_tables():
    # Create db
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the database.")

    # Drop tables if they exist
    statement = '''
        DROP TABLE IF EXISTS 'Restaurants';
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
        DROP TABLE IF EXISTS 'Ratings';
    '''
    cur.execute(statement)
    conn.commit()

    # -- Create tables: Bars --
    rest_statement = '''
        CREATE TABLE 'Restaurants' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'Name' TEXT NOT NULL,
            'Rating' TEXT,
            'ReviewCount' TEXT,
            'PriceRange' TEXT,
            'PageURL' TEXT,
            'Street' TEXT,
            'City' TEXT,
            'State' TEXT,
            'Zipcode' TEXT

        );
    '''
    try:
        cur.execute(rest_statement)
    except:
        print("Fail to create table.")
    conn.commit()


    rating_statement = '''
        CREATE TABLE 'Ratings' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'Name' TEXT,
            'RestaurantId' INTEGER,
            'TripAdvisor' TEXT NOT NULL,
            'Yelp' TEXT NOT NULL,
            'Lat' INTEGER,
            'Lon' INTEGER
        );
    '''
    try:
        cur.execute(rating_statement)
    except:
        print("Fail to create table.")
    conn.commit()




def insert_json(FILENAME):
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the initial database.")

    # read data from JSON
    json_file = open(FILENAME, 'r')
    json_data = json_file.read()
    json_dict = json.loads(json_data)

    for row in json_dict:
        insert_statement = '''
            INSERT OR IGNORE INTO "Restaurants"
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        values = (None, row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])

        cur.execute(insert_statement, values)
        conn.commit()



# insert file data into the db
def insert_csv(FNAME):
    # connect to the db
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the database")

    #read data from csv
    with open(FNAME, 'r') as csv_file:
        csv_data = csv.reader(csv_file)

        for row in csv_data:
            insert_statement = '''
                INSERT OR IGNORE INTO "Ratings"
                VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            values = (None, row[0], None, None, row[1], row[3], row[4])

            cur.execute(insert_statement, values)
            conn.commit()
            # conn.close()


# create database & insert data
init_db_tables()
insert_json(RESTJSON)
insert_csv(CSVFILE)
