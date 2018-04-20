## SI507_FinalProject_README
### Section 009 (Jie-wei Wu)
### Siyu Jia
## 

## 1. Overview
The goal of the project is to use python to get data from TripAdvisor and Yelp on Ann Arbor's restaurant information(**Note: 100 restaurants from TripAdvisor and 30 restaurants from Yelp respectively**) and store the data into a database for query and data visualization. There will be 4 graphs including a scatter map built by Plotly for users to interact with, especially to compare ratings.


## 2. Data Source
1) TripAdvisor
TripAdvisor is an America-based website providing hotel and restaurant reviews. This project only focuses on the restaurants in Ann Arbor. I scraped multiple web pages (including restaurant list page and each restaurant's details page) using BeautifulSoup. The information of the top 100 restaurants based on ratings has been cached in a JSON file named "cache_tripa.json".
https://www.tripadvisor.com/RestaurantSearch-g29556-Ann_Arbor_Michigan.html#EATERY_LIST_CONTENT

2) Yelp
Yelp is a platform that provides restaurants' information/reviews. Users can get relevant information by inputting keywords (like a restaurant's name), location, category, price level, etc.
Tool to get the data: Yelp Fusion API, which requires API key.
** API documentation homepage: https://www.yelp.com/developers/documentation/v3
** Search API documentation: https://www.yelp.com/developers/documentation/v3/business_search
The information of 30 restaurants has been cached in a JSON file named "cache_yelp.json".


## 3. Instructions
To successfully run this program, you need to do the following things:
1) IMPORTANT: get a client id and API key from Yelp. You can apply for authentication from Yelp API  using the link below:
     "https://www.yelp.com/developers/v3/manage_app"
2) Create a "secrets.py" file and put your client id and API key into it. The content format is like this:
client_id = ""
api_key = ""
3) Use python3 to run 'SI507F17_finalproject.py'
5) Refer to the requirements.txt file and get all the required modules ready
6) To see the visualized results and launch the predefined graphs, you may also need a Plotly account, here is the link to get started with Plotly:
https://plot.ly/python/getting-started/


## 4. Project Structure
My project consists of two Python files. The main running codes are in "si507_finalproject.py", and the "si507_finalproject_test.py" is created to test if the data access, storage, and processing can work correctly or not.

1) A class "Restaurant" has been defined to facilitate the web scraping function and database creation.
2) A function "get_rest_info(page="")" is defined for crawling and scraping the web pages of TripAdvisor. The returned results is a list of Restaurant instances.
3) A function "get_from_yelp(rest_name)" is defined to get a restaurant's information using Yelp Fusion API based on the restaurant's name.
4) A database named "restaurants" with two tables ("Restaurants" and "Ratings") has been created to present the data gotten from TripAdvisor and Yelp.
5) Four graphs (including a scatter map, a grouped bar chart, a pie chart, and a stacked bar chart) are defined to visualize data.
6) Two JSON files ("cache_tripa.json" and "cache_tripa.json") should be created to cache data. A CSV file will display the information regarding ratings and reviews for 30 restaurants in Ann Arbor.


## 5. Commands
1) tripadvisor <result_number>
   available anytime
   lists a list of restaurants in Ann Arbor based on TripAdvisor's ratings
   valid inputs: an integer no bigger than 30
2) yelp <result_number>
   available anytime
   lists a list of restaurants in Ann Arbor based on Yelp's ratings
   valid inputs: an integer no bigger than 30
3) map
   available only if there is an active result set
   displays the top 30 restaurants on a map
4) rating
   available only if there is an active result set
   displays a grouped bar chart revealing 10 restaurants' ratings
5) price
   available only if there is an active result set
   displays a  pie chart revealing the distribution of the top 100 restaurants' price range
6) review
   available only if there is an active result set
   displays the most-discussed (based on review counts) restaurants
7) exit
   exits the program
8) help
   lists available commands (these instructions)
