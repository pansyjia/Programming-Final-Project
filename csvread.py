import csv

with open("top30.csv", "r") as csv_file:
    csv_data = csv_file.readlines()[1:11]

# print(csv_data)

for item in csv_data:
    list = item.split(",")
    print(list[0])
    print(list[-2])
    print(list[-1])
