import pickle
import matplotlib.pyplot as plt 
import numpy as np 
import matplotlib.dates as mdates
from bs4 import BeautifulSoup
import os

# This is old now, the way we dump now has changed so would have to modify it accordingly.
# TODO: Nishant
def getData(dumpfile):
    with open(dumpfile, 'rb') as handle:
        data_cure_fit = pickle.load(handle)
    for i in range(len(data_cure_fit)):
        sample_data = data_cure_fit[i]
        soup=BeautifulSoup(sample_data[0])
        elements = soup.findAll(attrs = {"style": "padding-left: 20px; width: 55%"})
        assert(len(elements) >= 2)
    i = -1
    total_sales = []
    for i in range(len(data_cure_fit)):
        sample_data = data_cure_fit[i]
        soup=BeautifulSoup(sample_data[0])
        elements = soup.findAll(attrs = {"style": "padding-left: 20px; width: 55%"})
        item_list = []
        for item in elements[1:]:
            item_name = item.text.strip()
            attrs = item.fetchNextSiblings()
            ind_price = attrs[0].text
            quantity = attrs[1].text
            total_price = attrs[2].text
            item_list.append([item_name, ind_price, quantity, total_price])
        attributes_of_sale = {}
        elements_of_total_bill = soup.findAll("td", attrs = {"style": "padding-left: 20px; width: 85%"})
        for element in elements_of_total_bill:
            attributes_of_sale[element.text] = element.fetchNextSiblings()[0].text
        attributes_of_sale["item_list"] = item_list
        attributes_of_sale["date"] = sample_data[-1]
        attributes_of_sale["subject"] = sample_data[-2]
        attributes_of_sale["snippet"] = sample_data[-3]
        total_sales.append(attributes_of_sale)
    num_orders = []
    cumulative = 0
    for a in total_sales:
        # num_orders.append([int(a['subject'].split(" ")[-1]), datetime.datetime.strptime(a['date'], "%a, %d %b %Y %H:%M:%S %z").date()])
        # num_orders.append([float(a['Total Payable']), datetime.datetime.strptime(a['date'], "%a, %d %b %Y %H:%M:%S %z").date()])
        cumulative += float(a['Total Payable'])
        num_orders.append([cumulative, datetime.datetime.strptime(a['date'], "%a, %d %b %Y %H:%M:%S %z").date()])
    total_sales.reverse()
    num_orders = []
    cumulative = 0
    for a in total_sales:
        # num_orders.append([int(a['subject'].split(" ")[-1]), datetime.datetime.strptime(a['date'], "%a, %d %b %Y %H:%M:%S %z").date()])
        # num_orders.append([float(a['Total Payable']), datetime.datetime.strptime(a['date'], "%a, %d %b %Y %H:%M:%S %z").date()])
        cumulative += float(a['Total Payable'])
        num_orders.append([cumulative, datetime.datetime.strptime(a['date'], "%a, %d %b %Y %H:%M:%S %z").strftime("%Y%m%d")])
    num_orders = np.array(num_orders)
    x = num_orders[:,1]
    y = num_orders[:,0]
    uniqueValues, indicesList = np.unique(x, return_index=True)
    x_uni = np.array(x[indicesList], dtype=float)
    y_uni = np.array(y[indicesList], dtype=float)
    return x_uni, y_uni

getData("")