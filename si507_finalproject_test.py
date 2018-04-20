import unittest
import json
import csv
import sqlite3
from si507_finalproject import *

class TestDatabase(unittest.TestCase):
	def test_restaurants_table(self):
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()

		sql_1 = '''
			SELECT Name
			FROM Restaurants
			WHERE PriceRange = '$'
			ORDER BY Name DESC
		'''

		result1 = cur.execute(sql_1)
		result1_list = result1.fetchall()
		self.assertEqual(len(result1_list), 21)
		self.assertTrue(("The Lunch Room",) in result1_list)

		sql_2 = '''
			SELECT DISTINCT Street
			FROM Restaurants
		'''

		result2 = cur.execute(sql_2)
		result2_list = result2.fetchall()
		self.assertEqual(len(result2_list),99)

		conn.close()

	def test_ratings_table(self):
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()

		sql_1 = '''
	        SELECT Restaurant
			FROM Ratings
		'''

		result1 = cur.execute(sql_1)
		result1_list = result1.fetchall()
		self.assertEqual(len(result1_list), 30)

		sql_2 = '''
		    SELECT TripA_Rating, Yelp_ReviewCount
			FROM Ratings
			WHERE TripA_Rating == Yelp_Rating
		'''

		result2 = cur.execute(sql_2)
		result2_list = result2.fetchall()
		self.assertEqual(len(result2_list), 6)
		for item in result2_list:
			self.assertNotEqual(type(item[0]), str)
			self.assertEqual(type(item[1]), int)

		conn.close()

	def test_joins(self):
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()

		sql = '''
		    SELECT Name
			FROM Restaurants
			    JOIN Ratings
				ON Restaurants.Id = Ratings.RestaurantId
			WHERE PriceRange = '$'
			    AND Yelp_Rating > 4
		'''

		results = cur.execute(sql)
		result_list = results.fetchall()
		self.assertEqual(len(result_list), 2)
		self.assertIn(('NeoPapalis',), result_list)

		conn.close()



class TestGetData(unittest.TestCase):
    def setUp(self):
        self.tripa = open("cache_tripa.json", "r", encoding='utf-8')
        self.yelp = open("cache_yelp.json", "r", encoding='utf-8')
        self.top30 = open("top30.csv", "r")

    def test_tripa_json_exist(self):
        self.assertTrue(self.tripa.read())

    def test_yelp_json_exist(self):
        self.assertTrue(self.yelp.read())

    def test_top30_csv_exist(self):
        self.assertTrue(self.top30.read())

    def tearDown(self):
        self.tripa.close()
        self.yelp.close()
        self.top30.close()


class TestClass(unittest.TestCase):
    def test_restaurant_class(self):
        sample = Restaurant("The Lunch Room", 4.5, "$", "https://www.tripadvisor.com/Restaurant_Review-g29556-d4982890-Reviews-The_Lunch_Room-Ann_Arbor_Michigan.html")
        self.assertEqual(sample.street, "123 Main St.")
        self.assertEqual(sample.rating2, "0")
        self.assertEqual(sample.__str__(), "The Lunch Room: 123 Main St., Ann Arbor, MI(11111)")



class TestWebCrawling(unittest.TestCase):
    def test_get_rest_info(self):
        restaurant_ls = get_rest_info("")
        self.assertEqual(len(restaurant_ls), 30)
        self.assertEqual(restaurant_ls[0].name, "The Lunch Room")
        self.assertEqual(restaurant_ls[1].rating1, "4.5")
        self.assertEqual(restaurant_ls[2].zip, "48104")
        self.assertEqual(restaurant_ls[2].street, "117 W Washington St")


class TestMapping(unittest.TestCase):
    def test_plot_rests_map(self):
        try:
            plot_rests_map()
        except:
            self.fail()



if __name__ == "__main__":
	unittest.main(verbosity=2)
