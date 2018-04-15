## 507 Final Project

#TripAdvisor
import requests
import webbrowser
import secrets
import sqlite3
import json
import csv
# import plotly.plotly as py
# import plotly.graph_objs as go
from bs4 import BeautifulSoup

CLIENT_ID = secrets.client_id
API_KEY = secrets.api_key

# ---------- Class Object -----
class Restaurant():
    def __init__(self, name, rating1="0", reviews="0", price="0", url=None, lat="0", lon="0"):
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
        self.lat = lat
        self.lng = lon

    def __str__(self):
        rest_str = "{}: {}, {}, {}({})".format(self.name, self.street, self.city, self.state, self.zip)
        return rest_str


# ---------- Caching ----------
CACHE_TRIPA = "cache_tripa.json"
CACHE_YELP = "cache_yelp.txt"

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
        print("Craling for new data...")
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

    crawling_list = page_soup.find_all(class_="listing")
    rest_list = [] #a list to store the instances of Restaurant
    for rest in crawling_list:
        try:
            rest_name = rest.find(class_="property_title").text.replace("\n", "")
            rest_rating = rest.find(class_="ui_bubble_rating")["alt"].replace(" of 5 bubbles", "")
            rest_reviews = rest.find(class_="reviewCount").text.replace(" reviews \n", "")
            rest_price = rest.find(class_="item price").string
            detail_url = "https://www.tripadvisor.com" + rest.find("a")["href"]

            restaurant_ins = Restaurant(rest_name, rest_rating, rest_price, detail_url)

            #scrape details
            details_page_text = make_request_using_cache_crawl(detail_url)
            details_page_soup = BeautifulSoup(details_page_text, "html.parser")
            street_info = details_page_soup.find(class_ = "street-address").text
            zip_info = details_page_soup.find(class_ = "locality").text.split(", ")[1][3:8]
            rest_reviews = details_page_soup.find(property = "count").text
            # lat = details_page_soup.find(class_ = "prv_map").find('img')['src'][-9:]
            # lon = details_page_soup.find(class_ = "prv_map").find('img')['src'][-18:-10]

            restaurant_ins.street = street_info
            restaurant_ins.zip = zip_info
            restaurant_ins.reviews = rest_reviews
            # restaurant_ins.lat = lat
            # restaurant_ins.lon = lon

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
        yelp_json_list = [] ## a list of dict, write into a txt
        response = requests.get(base_url, params=parameters, headers=headers)
        resp_dict = json.loads(response.text)
        yelp_json_list.append(resp_dict)
        write_file = open(CACHE_YELP, 'w+')
        write_file.write(json.dumps(yelp_json_list))
        write_file.close()
        return resp_dict


# use the names of the top 30 restaurants in TripAdvisor to
top30 = get_rest_info()[:30]
yelp_list = []
yelp_list.append(("Restaurant", "TripA_Rating", "TripA_ReviewCount", "Yelp_Rating", "Yelp_ReviewCount", "Phone", "Transaction"))
for rest in top30 :
    yelp_info = get_from_yelp(rest.name)["businesses"][0]
    yelp_list.append((yelp_info["name"], rest.rating1, rest.reviews, yelp_info["rating"], yelp_info["review_count"], yelp_info["phone"], yelp_info["transactions"]))

with open('top30.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerows(yelp_list)



# ---------- Database ----------
DBNAME = "restaurants.db"
RESTJSON = "cache_tripa.json"
CSVFILE = "top30.csv"

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
            'Restaurant' TEXT,
            'RestaurantId' INTEGER,
            'TripA_Rating' INTEGER,
            'TripA_ReviewCount' TEXT,
            'Yelp_Rating' INTEGER,
            'Yelp_ReviewCount' INTEGER,
            "Phone" TEXT,
            "Transaction" TEXT
        );
    '''
    try:
        cur.execute(rating_statement)
    except:
        print("Fail to create table.")
    conn.commit()




def insert_data():
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the initial database.")

    # # read data from JSON
    # json_file = open(FILENAME, 'r')
    # json_data = json_file.read()
    # json_dict = json.loads(json_data)

    restaurants = get_rest_info()[:100]

    for rest in restaurants:
        insert_statement = '''
            INSERT INTO "Restaurants"
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        values = (None, rest.name, rest.price, rest.url, rest.street, rest.city, rest.state, rest.zip)

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

        next(csv_data)

        for row in csv_data:
            insert_statement = '''
                INSERT INTO "Ratings"
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            values = (None, row[0], None, row[1], row[2], row[3], row[4], row[5], row[6])

            cur.execute(insert_statement, values)
            conn.commit()



#join tables and insert foreign keys
def update_tables():
    # connect to the db
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the database")

    # set keys
    update_restaurantid = '''
        UPDATE Ratings
        SET (RestaurantId) = (SELECT t.Id FROM Restaurants AS t WHERE Ratings.Restaurant = t.Name)
    '''

    cur.execute(update_restaurantid)
    conn.commit()

# _________________________________________________
# def plot_restaurants(rest_list):
#     rest_list =
#
#     lat_vals = []
#     lon_vals = []
#     text_vals = []
#
#     #store data in lat, lon, and text lists
#     for rest in rest_list:
#         google_places_api = secrets.google_places_key
#         google_places_url = "https://maps.googleapis.com/maps/api/place/textsearch/json?query={}&tyepe={}&key={}".format(site.name, site.type, google_places_api)
#
#         google_results = make_request_using_cache(url = google_places_url)
#         google_results_dict = json.loads(google_results)
#         # if len(google_results) != 0 and site.name != None:
#         try:
#             site_lat = google_results_dict["results"][0]["geometry"]["location"]["lat"]
#             site_lon = google_results_dict["results"][0]["geometry"]["location"]["lng"]
#
#             lat_vals.append(site_lat)
#             lon_vals.append(site_lon)
#             text_vals.append(site.name)
#         except:
#             print("No result.")
#
#         # create data object
#         data = [dict(
#               type = 'scattergeo',
#               locationmode = 'USA-states',
#               lon = lon_vals,
#               lat = lat_vals,
#               text = text_vals,
#               mode = 'markers',
#               marker = dict(
#                    size = 20,
#                    symbol = 'star',
#                    color = 'red'
#             ))]
#
#         # scaling and centering the map
#         min_lat = 10000
#         max_lat = -10000
#         min_lon = 10000
#         max_lon = -10000
#
#         for str_v in lat_vals:
#             v = float(str_v)
#             if v < min_lat:
#                 min_lat = v
#             if v > max_lat:
#                 max_lat = v
#         for str_v in lon_vals:
#             v = float(str_v)
#             if v < min_lon:
#                 min_lon = v
#             if v > max_lon:
#                 max_lon = v
#
#         # fix padding problem
#         max_range = max(abs(max_lat - min_lat), abs(max_lon - min_lon))
#         padding = max_range * .10
#         lat_axis = [min_lat - padding, max_lat + padding]
#         lon_axis = [min_lon - padding, max_lon + padding]
#
#         center_lat = (max_lat+min_lat) / 2
#         center_lon = (max_lon+min_lon) / 2
#
#         # create the layout object
#         layout = dict(
#                 title = 'National Sites in ' + state_abbr.upper(),
#                 geo = dict(
#                      scope='usa',
#                      projection=dict( type='albers usa' ),
#                      showland = True,
#                      landcolor = "rgb(250, 250, 250)",
#                      subunitcolor = "rgb(100, 217, 217)",
#                      countrycolor = "rgb(217, 100, 217)",
#                      lataxis = {'range': lat_axis},
#                      lonaxis = {'range': lon_axis},
#                      center= {'lat': center_lat, 'lon': center_lon },
#                      countrywidth = 3,
#                      subunitwidth = 3
#                  ),
#         )
#
#         fig = dict(data=data, layout=layout)
#         py.plot(fig, validate=False, filename='usa - national_sites')


#--------------bar chart--------------
# x = ['Product A', 'Product B', 'Product C']
# y = [20, 14, 23]
# y2 = [16,12,27]
#
# trace1 = go.Bar(
#     x=x,
#     y=y,
#     text=y,
#     textposition = 'auto',
#     marker=dict(
#         color='rgb(158,202,225)',
#         line=dict(
#             color='rgb(8,48,107)',
#             width=1.5),
#         ),
#     opacity=0.6
# )
#
# trace2 = go.Bar(
#     x=x,
#     y=y2,
#     text=y2,
#     textposition = 'auto',
#     marker=dict(
#         color='rgb(58,200,225)',
#         line=dict(
#             color='rgb(8,48,107)',
#             width=1.5),
#         ),
#     opacity=0.6
# )
#
# data = [trace1,trace2]
#
# py.plot(data, filename='grouped-bar-direct-labels')


# create database & insert data
init_db_tables()
insert_data()
insert_csv(CSVFILE)
update_tables()
