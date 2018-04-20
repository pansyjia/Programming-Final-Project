## 507 Final Project
## Siyu Jia
## Section 009

import requests
import webbrowser
import secrets
import sqlite3
import json
import csv
import plotly.plotly as py
import plotly.graph_objs as go
from bs4 import BeautifulSoup

# import Yelp Fusion API keys
CLIENT_ID = secrets.client_id
API_KEY = secrets.api_key

# ---------- Class Object ----------
class Restaurant():
    def __init__(self, name, rating1="0", price="0", url=None):
        self.name = name
        self.rating1 = rating1
        self.price = price
        self.url = url

        self.category = ""
        self.reviews = "0"
        self.rating2 = "0"
        self.street = "123 Main St."
        self.city = "Ann Arbor"
        self.state = "MI"
        self.zip = "11111"
        self.lat = "0"
        self.lng = "0"

    def __str__(self):
        rest_str = "{}: {}, {}, {}({})".format(self.name, self.street, self.city, self.state, self.zip)
        return rest_str


# ---------- Caching Setup----------
CACHE_TRIPA = "cache_tripa.json"
CACHE_YELP = "cache_yelp.json"


# web scraping and crawling setup
try:
    cache_tripa_file = open(CACHE_TRIPA, "r")
    cache_tripa_contents = cache_tripa_file.read()
    TRIPA_DICTION = json.loads(cache_tripa_contents)
    cache_tripa_file.close()
except:
    TRIPA_DICTION = {}

def get_unique_key(url):
    return url

def make_request_using_cache_crawl(url):
    unique_ident = get_unique_key(url)

    if unique_ident in TRIPA_DICTION:
        # print("Fetching cached data...")
        return TRIPA_DICTION[unique_ident]
    else:
        # make the request and cache the new data
        # print("Craling for new data...")
        resp = requests.get(url)
        TRIPA_DICTION[unique_ident] = resp.text # only store the html
        dumped_json_cache_crawl = json.dumps(TRIPA_DICTION)
        fw = open(CACHE_TRIPA,"w")
        fw.write(dumped_json_cache_crawl)
        fw.close() # Close the open file
        return TRIPA_DICTION[unique_ident]


# API caching setup
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



# ---------- TripAdvisor Web Scraping & Crawling ----------
def get_rest_info(page=""):
    baseurl = "https://www.tripadvisor.com/RestaurantSearch-g29556-{}-Ann_Arbor_Michigan.html#EATERY_LIST_CONTENTS".format(page)
    page_text = make_request_using_cache_crawl(baseurl)
    page_soup = BeautifulSoup(page_text, "html.parser")

    crawling_list = page_soup.find_all(class_="listing")
    rest_list = [] #a list to store the instances of Restaurant
    for rest in crawling_list:
        try:
            rest_name = rest.find(class_="property_title").text.replace("\n", "")
            rest_rating = rest.find(class_="ui_bubble_rating")["alt"].replace(" of 5 bubbles", "")
            rest_price = rest.find(class_="item price").string
            detail_url = "https://www.tripadvisor.com" + rest.find("a")["href"]

            restaurant_ins = Restaurant(rest_name, rest_rating, rest_price, detail_url)

            #scrape details
            details_page_text = make_request_using_cache_crawl(detail_url)
            details_page_soup = BeautifulSoup(details_page_text, "html.parser")
            street_info = details_page_soup.find(class_ = "street-address").text
            zip_info = details_page_soup.find(class_ = "locality").text.split(", ")[1][3:8]
            rest_reviews = details_page_soup.find(property = "count").text.replace(",", "")

            restaurant_ins.street = street_info
            restaurant_ins.zip = zip_info
            restaurant_ins.reviews = rest_reviews
            # restaurant_ins.lat = lat
            # restaurant_ins.lon = lon

            rest_list.append(restaurant_ins)
        except:
            # print("Fail to creat instance list. ")
            continue


    return rest_list


# ------------ Yelp API ----------------
def get_from_yelp(rest_name):
    base_url = "https://api.yelp.com/v3/businesses/search"
    headers = {'Authorization': f"Bearer {API_KEY}"}
    parameters = {}
    parameters["term"] = rest_name
    parameters["location"] = "ann arbor"
    parameters["limit"] = 1
    unique_id = params_unique_combination(base_url, parameters)
    if unique_id in YELP_DICTION:
        # print("Fetching cached yelp data...")
        return YELP_DICTION[unique_id]
    else:
        # print("Making a yelp request for new data...")
        response = requests.get(base_url, params=parameters, headers=headers)
        YELP_DICTION[unique_id] = json.loads(response.text)
        write_file = open(CACHE_YELP, "w+")
        write_file.write(json.dumps(YELP_DICTION))
        write_file.close()
        return YELP_DICTION[unique_id]


# use the names of the top 30 restaurants in TripAdvisor to
top30 = get_rest_info("")
yelp_list = []
yelp_list.append(("Restaurant", "Category", "TripA_Rating", "TripA_ReviewCount", "Yelp_Rating", "Yelp_ReviewCount", "Phone", "Latitude", "longitude"))
for rest in top30:
    yelp_info = get_from_yelp(rest.name)["businesses"][0]
    yelp_list.append((rest.name, yelp_info["categories"][0]["title"], rest.rating1, rest.reviews, yelp_info["rating"], yelp_info["review_count"], yelp_info["phone"], yelp_info["coordinates"]["latitude"], yelp_info["coordinates"]["longitude"]))

with open("top30.csv", "w", newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerows(yelp_list)



# -------------- Create Database ---------------
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
            'Categories' TEXT,
            'TripA_Rating' INTEGER,
            'TripA_ReviewCount' INTEGER,
            'Yelp_Rating' INTEGER,
            'Yelp_ReviewCount' INTEGER,
            "Phone" TEXT,
            "Latitude" INTEGER,
            "longitude" INTEGER
        );
    '''
    try:
        cur.execute(rating_statement)
    except:
        print("Fail to create table.")
    conn.commit()
    conn.close()


# insert data into restaurants table
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


    restaurants = get_rest_info("")+get_rest_info("oa60")+get_rest_info("oa90")+get_rest_info("oa120")[:10]

    for rest in restaurants:
        insert_statement = '''
            INSERT INTO "Restaurants"
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        values = (None, rest.name, rest.price, rest.url, rest.street, rest.city, rest.state, rest.zip)

        cur.execute(insert_statement, values)
        conn.commit()
        # conn.close()



# insert csv file data into rating table
def insert_csv(FNAME):
    # connect to the db
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect to the database")

    #read data from csv
    with open(FNAME, "r") as csv_file:
        csv_data = csv.reader(csv_file)

        next(csv_data)

        for row in csv_data:
            insert_statement = '''
                INSERT INTO "Ratings"
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            values = (None, row[0], None, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])

            cur.execute(insert_statement, values)
            conn.commit()
            # conn.close()


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




#------------ Plotly: scatter map ----------------
def plot_rests_map():
    try:
        with open("top30.csv", "r") as csv_file:
            csv_data = csv.reader(csv_file)
            next(csv_data)

            #store data in lat, lon, and text lists
            lat_vals = []
            lon_vals = []
            text_vals = []

            for row in csv_data:
                lat_vals.append(row[7])
                lon_vals.append(row[8])
                text_vals.append((row[0], get_from_yelp(row[0])["businesses"][0]["categories"][0]["title"]))
    except:
        print("Fail to read top 30 geographical data.")
        pass


    # create data object
    data = [dict(
              type = 'scattergeo',
              locationmode = 'USA-states',
              lon = lon_vals,
              lat = lat_vals,
              text = text_vals,
              mode = 'markers',
              marker = dict(
                   size = 20,
                   symbol = 'star',
                   color = 'red'
        ))]

    # scaling and centering the map
    min_lat = 10000
    max_lat = -10000
    min_lon = 10000
    max_lon = -10000

    for str_v in lat_vals:
        v = float(str_v)
        if v < min_lat:
            min_lat = v
        if v > max_lat:
            max_lat = v
    for str_v in lon_vals:
        v = float(str_v)
        if v < min_lon:
            min_lon = v
        if v > max_lon:
            max_lon = v

    # fix padding problem
    max_range = max(abs(max_lat - min_lat), abs(max_lon - min_lon))
    padding = max_range * .10
    lat_axis = [min_lat - padding, max_lat + padding]
    lon_axis = [min_lon - padding, max_lon + padding]

    center_lat = (max_lat+min_lat) / 2
    center_lon = (max_lon+min_lon) / 2

    # create the layout object
    layout = dict(
                title = 'Top 30 Restaurants in Ann Arbor',
                geo = dict(
                     scope='usa',
                     projection=dict( type='albers usa' ),
                     showland = True,
                     landcolor = "rgb(250, 250, 250)",
                     subunitcolor = "rgb(100, 217, 217)",
                     countrycolor = "rgb(217, 100, 217)",
                     lataxis = {'range': lat_axis},
                     lonaxis = {'range': lon_axis},
                     center= {'lat': center_lat, 'lon': center_lon },
                     countrywidth = 3,
                     subunitwidth = 3
                ),
    )

    fig = dict(data=data, layout=layout)
    py.plot(fig, validate=False, filename='Ann Arbor - top30 restaurants')



#-------------- bar chart --------------
def plot_rating():
    try:
        with open("top30.csv", "r") as csv_file:
            csv_data = csv_file.readlines()[1:11]

            #store data in lists
            rest_name = []
            tripa_rating = []
            yelp_rating = []

            for row in csv_data:
                data_list = row.split(",")
                rest_name.append(data_list[0])
                tripa_rating.append(data_list[2])
                yelp_rating.append(data_list[4])
    except:
        print("Fail to read top 10 rating data.")
        pass


    TripA = go.Bar(
                x=rest_name,
                y=tripa_rating,
                text=tripa_rating,
                textposition = 'auto',
                marker=dict(
                    color='rgb(49,130,189)',
                    line=dict(
                        color='rgb(49,130,189)',
                        width=1.5),
                ),
                opacity=0.6,
                name = 'TripAdvisor'
            )

    Yelp = go.Bar(
                x=rest_name,
                y=yelp_rating,
                text=yelp_rating,
                textposition = 'auto',
                marker=dict(
                    color='rgb(204,204,204)',
                    line=dict(
                        color='rgb(204,204,204)',
                        width=1.5),
                ),
                opacity=0.6,
                name = 'Yelp'
            )

    data = [TripA,Yelp]

    py.plot(data, filename='grouped-bar-direct-labels')



#-------------- pie chart --------------
def plot_price():
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect db with pie chart. ")

    statement = '''
        SELECT PriceRange, COUNT(*)
        FROM Restaurants
        GROUP BY PriceRange
        ORDER BY COUNT(*)
    '''

    cur = cur.execute(statement)
    labels = []
    values = []
    for row in cur:
        labels.append(row[0])
        values.append(row[1])

    trace = go.Pie(labels=labels, values=values)

    py.plot([trace], filename='basic_pie_chart')



#-------------- stacked bar chart --------------
def plot_review():
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect db with bar chart. ")

    statement = '''
        SELECT Restaurant, TripA_ReviewCount, Yelp_ReviewCount
        FROM Ratings
        WHERE TripA_ReviewCount > 800 OR Yelp_ReviewCount > 800
    '''

    cur = cur.execute(statement)

    x = []
    y1 = []
    y2 = []
    for row in cur:
        x.append(row[0])
        y1.append(int(row[1]))
        y2.append(int(row[2]))

    trace1 = go.Bar(
        x=x, y=y1, name='TripAdvisor'
    )

    trace2 = go.Bar(
        x=x, y=y2, name='Yelp'
    )

    data = [trace1, trace2]
    layout = go.Layout(barmode='stack')

    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='stacked-bar')



#------------ interactions -------------
# get input
def prompt():
    user_input = input("Please enter your command or enter 'help' for options:  ")
    return user_input.lower()


# define commands
def help_command():

    help_instruction = '''
    tripadvisor <result_number>
        available anytime
        lists a list of restaurants in Ann Arbor based on TripAdvisor's ratings
        valid inputs: an integer no bigger than 30
    yelp <result_number>
        available anytime
        lists a list of restaurants in Ann Arbor based on Yelp's ratings
        valid inputs: an integer no bigger than 30
    map
        available only if there is an active result set
        displays the top 30 restaurants on a map
    rating
        available only if there is an active result set
        displays a grouped bar chart revealing 10 restaurants' ratings
    price
        available only if there is an active result set
        displays a  pie chart revealing the distribution of the top 100 restaurants' price range
    review
        available only if there is an active result set
        displays the most-discussed (based on review counts) restaurants
    exit
        exits the program
    help
        lists available commands (these instructions)
    '''

    print(help_instruction)


def tripa_command(number):
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect db. ")

    statement = "SELECT r1.Restaurant, r1.Categories, r1.TripA_Rating, r2.Street, r1.Phone "
    statement += "FROM Ratings as r1 "
    statement += "JOIN Restaurants as r2 ON r1.RestaurantId = r2.Id "
    statement += "GROUP BY r1.Restaurant "
    statement += "ORDER BY r1.TripA_Rating DESC "
    statement += "LIMIT {} ".format(number)

    results = []
    rows = cur.execute(statement).fetchall()
    for row in rows:
        results.append(row)
    conn.commit()

    return results


def yelp_command(number):
    try:
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
    except:
        print("Fail to connect db. ")

    statement = "SELECT r1.Restaurant, r1.Categories, r1.Yelp_Rating, r2.Street, r1.Phone "
    statement += "FROM Ratings as r1 "
    statement += "JOIN Restaurants as r2 ON r1.RestaurantId = r2.Id "
    statement += "GROUP BY r1.Restaurant "
    statement += "ORDER BY r1.Yelp_Rating DESC "
    statement += "LIMIT {} ".format(number)

    results = []
    rows = cur.execute(statement).fetchall()
    for row in rows:
        results.append(row)
    conn.commit()

    return results


def plot_map_command():
    return plot_rests_map()

def plot_price_command():
    return plot_price()

def plot_rating_command():
    return plot_rating()

def plot_review_command():
    return plot_review()


def str_output(str_result):
    if len(str_result) > 12:
        formatted_output = str_result[:12] + "..."
    else:
        formatted_output = str_result
    return formatted_output


# handle user input
def interact_prompt():
    user_input = input("Hi! Welcome to Ann Arbor Restaurants Guide. Please enter your command or enter 'help' for options:  ")

    while "exit" not in user_input:
        if user_input == "help":
            help_command()
        elif "tripadvisor" in user_input:
            if len(user_input) <= 12:
                print("Invalid input.\n")
            elif int(user_input.split()[-1]) > 30:
                print("Invalid input.\n")
            else:
                try:
                    result_set=tripa_command(int(user_input.split()[-1]))
                    row_format = "{0:2} {1:15} {2:15} {3:15} {4:15} {5:15}"
                    index = 1
                    for row in result_set:
                        print(row_format.format(index, str_output(row[0]), str_output(row[1]), row[2], str_output(row[3]), str_output(row[4])))
                        index += 1
                except:
                    print("tripa error. ")
        elif "yelp" in user_input:
            if len(user_input) <= 5:
                print("Invalid input.\n")
            elif int(user_input.split()[-1]) > 30:
                print("Invalid input.\n")
            else:
                try:
                    result_set = yelp_command(int(user_input.split()[-1]))
                    row_format = "{0:2} {1:15} {2:15} {3:15} {4:15} {5:15}"
                    index = 1
                    for row in result_set:
                        print(row_format.format(index, str_output(row[0]), str_output(row[1]), row[2], str_output(row[3]), str_output(row[4])))
                        index += 1
                except:
                    print("yelp error. ")
        elif "map" in user_input:
            try:
                plot_map_command()
            except:
                print("plot map error.")
                pass
        elif "rating" in user_input:
            try:
                plot_rating_command()
            except:
                print("plot rating error.")
                pass
        elif "price" in user_input:
            try:
                plot_price_command()
            except:
                print("plot price error.")
                pass
        elif "review" in user_input:
            try:
                plot_review_command()
            except:
                print("plot review error.")
                pass

        user_input = prompt()

    print("Bye! Bon Appetit! ")


# ---------------------------------------------
if __name__=="__main__":
    init_db_tables()
    insert_data()
    insert_csv(CSVFILE)
    update_tables()
    interact_prompt()
