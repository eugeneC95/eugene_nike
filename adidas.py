# Adidas sneakerbot based on USA MEN sizes (see size chart for converting)
# Usage: python bot.py [-h] modelnumber size profile
# Author: Henri Cattoire
import argparse
import requests
import time
import sys
import os
import sqlite3
from pathlib import Path
from selenium import webdriver

# Globals
version = 1.2
db = 'profiles.db'
pathto_chromedriver = 'chromedriver' # download here: https://sites.google.com/a/chromium.org/chromedriver/downloads


def add_profile(name):
    connection = sqlite3.connect('profiles_sneakerbot.db')
    c = connection.cursor() # This variable will allows us to execute stuff to the database
# Profile data  
    profile_name = name
    basic_url = input("(basic url, ex. https://www.adidas.be) -> ") 
    # Personal info
    full_name = input("(full name) -> ")
    first, last = full_name.split(' ', 1)
    address = input("(address) -> ")
    full_city = input("(city and postal) -> ")
    city, postal = full_city.split(' ', 1)
    mail = input("(email) -> ")
    # Credit card info 
    card_number = input("(card number) -> ")
    ccv = input("(ccv) -> ")
    expiry_date = input("(expiry date, ex. 01-2020) -> ")
    month, year = expiry_date.split('-', 1)
    # Adding the info to your database file
    tuple = (basic_url, first, last, address, city, postal, mail, card_number, ccv, month, year)
    c.execute('''
    CREATE TABLE {} (basic_url TEXT, first_name TEXT, last_name TEXT, address TEXT, city TEXT, postal TEXT, mail text,
                     card_number TEXT, ccv TEXT, month TEXT, year TEXT); 
    '''.format(profile_name))
    insert_string = "INSERT INTO {} VALUES ".format(profile_name)
    c.execute(insert_string + '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', tuple)

    connection.commit()
    connection.close()
    
def remove_profile(name):
    connection = sqlite3.connect('profiles_sneakerbot.db')
    c = connection.cursor() # This variable will allows us to execute stuff to the database
    c.execute('DROP TABLE {}'.format(name))
    connection.commit()
    connection.close()
    print("Profile ({}) was succesfully deleted.".format(name))

def show_profiles(): 
    connection = sqlite3.connect('profiles_sneakerbot.db')
    c = connection.cursor() # This variable will allows us to execute stuff to the database
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;") # This will select all the tables 
    tables = c.fetchall()
    for table in tables:
      x = 0 
      name = table[x] 
      query = "SELECT * FROM {}".format(name)
      c.execute(query)
      list = c.fetchall()
      list = str(list)
      print("Profile ({}): ".format(name) + list)
    connection.close()

def query_profile(name):
    connection = sqlite3.connect('profiles_sneakerbot.db')
    c = connection.cursor() # This variable will allows us to execute stuff to the database
    
    query = "SELECT * FROM {}".format(name)
    c.execute(query)
    list = c.fetchall()
    values = list[0]
    
    basic_url, first, last, address, city, postal, mail, card_number, ccv, month, year = values
    return basic_url, first, last, address, city, postal, mail, card_number, ccv, month, year


def gen(modelNumber, size, profile): # Function that will generate our url, based on this url: http://www.adidas.be/G48060.html?forceSelSize=G48060_590
    startSize = int(590) # Starting size (7 USA MEN/ 40 EU)  
	
    # Adjusting the number to your size
    yourSize = float(size) - 7
    yourSize = float(yourSize) * 20
    sizeNumber = int(yourSize + startSize)

    b_url = basicUrl(profile)
    url = "{url}/{model}.html?forceSelSize={model}_{size}".format(url = b_url, model = modelNumber, size = sizeNumber)
    return url

def inStock(modelNumber, size, profile): # Function that will check if your size is still in stock
    startSize = int(590) # Starting size (7 USA MEN/40 EU)
    
    # Adjusting the number to your size
    yourSize = float(size) - 7 
    yourSize = float(yourSize) * 20
    sizeNumber = int(yourSize + startSize)
    
    b_url = basicUrl(profile)
    url = "{url}/api/products/{model}/availability".format(url = b_url, model = modelNumber) 
    # Adidas checks the availability of the shoe sizes using an API (found with inspect [network] and reload of the page to see the incoming connections)
    availability = requests.get(url).json() # Getting information about the availability of the shoe sizes from the API (using the created url)
    if availability.get('availability_status') !=  'IN_STOCK': # Statement that checks if the shoe is still in stock
       return "Modelnumber {model} is no longer in stock".format(model = modelNumber)
    else:
       allSizes = availability.get('variation_list') # Putting the needed key (of the dictionary) in a variable
       for value in allSizes: # Loop that check the availability of your size
           if value.get('sku') == "{model}_{size}".format(model = modelNumber, size = sizeNumber): # Compares the value of the 'sku' id to our modelnumber_size and if it is equal, it displays the information about your size
              return value

def basicUrl(profile): # Scrape the url from the queried profile
    basic_url, first, last, address, city, postal, mail, card_number, ccv, month, year = query_profile(profile)
    return basic_url

def addBag(modelNumber, size, profile):
    url = gen(modelNumber, size, profile) # Generate the url using the gen function
    driver = webdriver.Chrome(pathto_chromedriver) # Using chrome to open our webpage
    
    # Adding the shoe to your bag (and going to checkout page)
    driver.get(url)
    button_addToBag = driver.find_element_by_css_selector("button[data-auto-id='add-to-bag'][type='submit']") # Finding the button that says "add to bag" in the html of our page (using specific css selectors)
    button_addToBag.click() # Clicks the "add to bag" button
    time.sleep(4)
    a_viewBag = driver.find_element_by_css_selector("a[data-auto-id='view-bag-desktop']")
    a_viewBag.click() # Clicks the "view bag" button
    time.sleep(2)
    
    autoCheckout(driver, profile)


def autoCheckout(driver, profile): # Function that will automatically check you out (without paypal)
    # Clicks the 'normal' checkout button
    button_checkout = driver.find_element_by_css_selector("button[data-ci-test-id='checkoutBottomButton'][type='submit']") 
    button_checkout.click()     
    time.sleep(2)
    
    basic_url, first, last, address, city, postal, mail, card_number, ccv, month, year = query_profile(profile)
    
    info = []
    info.extend((first, last, address, city, postal, mail, card_number, ccv, month, year))
     
    # Autofilling your information (first page)
    first_name = driver.find_element_by_css_selector("input[id='dwfrm_shipping_shiptoaddress_shippingAddress_firstName'][type='text']")
    first_name.send_keys(info[0]) 
    
    last_name = driver.find_element_by_css_selector("input[id='dwfrm_shipping_shiptoaddress_shippingAddress_lastName'][type='text']")
    last_name.send_keys(info[1]) 
    
    address = driver.find_element_by_css_selector("input[id='dwfrm_shipping_shiptoaddress_shippingAddress_address1'][type='text']")
    address.send_keys(info[2]) 
    
    city = driver.find_element_by_css_selector("input[id='dwfrm_shipping_shiptoaddress_shippingAddress_city'][type='text']")
    city.send_keys(info[3]) 
    
    postal = driver.find_element_by_css_selector("input[id='dwfrm_shipping_shiptoaddress_shippingAddress_postalCode'][type='text']")
    postal.send_keys(info[4]) 
    
    email = driver.find_element_by_css_selector("input[id='dwfrm_shipping_email_emailAddress'][type='email']")   
    email.send_keys(info[5]) 
    
    submit = driver.find_element_by_css_selector("button[name='dwfrm_shipping_submitshiptoaddress'][type='submit']") 
    submit.click()
    time.sleep(2)
    
    # Autofilling your information (second page)
    card_number = driver.find_element_by_css_selector("input[data-ci-test-id='cardNumberField'][type='text']")
    card_number.send_keys(info[6])
    
    m_box = driver.find_element_by_css_selector("div[class='materialize-element-field'][data-default-value='Month']")
    m_box.click()
    your_month = int(info[8])
    data = "div[class='materialize-select-option'][data-value='{}']".format(str(your_month).zfill(2))
    month = driver.find_element_by_css_selector(data)
    month.click()
    
    y_box = driver.find_element_by_css_selector("div[class='materialize-element-field'][data-default-value='Year']")
    y_box.click()
    your_year = int(info[9])
    data = "div[class='materialize-select-option'][data-value='{}']".format(str(your_year))
    year = driver.find_element_by_css_selector(data)
    year.click()
    
    ccv = driver.find_element_by_css_selector("input[id='dwfrm_adyenencrypted_cvc'][type='text']")
    ccv.send_keys(info[7])
    
    div = driver.find_element_by_css_selector("div[data-ci-test-id='paymentSubmitButton']") 
    order = div.find_element_by_css_selector("button[type='submit']") 
    order.click()
    time.sleep(5)
  
def main(): # Main function from which the program will be running

    # Adding arguments to our program
    parser = argparse.ArgumentParser(description='Adidas sneakerbot ({version}) that will add any shoe to your cart, instantly.'.format(version = str(version)))
# Optional arguments
    parser.add_argument('-a', '--add-profile', help='add a profile to the database', metavar='NAME')   
    parser.add_argument('-d', '--delete-profile', help='delete a profile from the database', metavar='NAME') 
    parser.add_argument('-s', '--show-profiles', help='shows all profiles', action='store_true')
# Positional arguments
    parser.add_argument('modelnumber', help='the model number of the sneaker (example: G48060)', nargs='?', const=None)
    parser.add_argument('size', help='your size (based on US MEN sizes)', nargs='?', const=None)
    parser.add_argument('profile', help='name of the profile you want to use to checkout', nargs='?', const=None)
    args = parser.parse_args()
    
    if args.add_profile: 
       add_profile(args.add_profile)
       sys.exit()
    elif args.delete_profile:
       remove_profile(args.delete_profile)
       sys.exit()
    elif args.show_profiles:
       show_profiles()
       sys.exit()
       
    if args.modelnumber == None or args.size == None or args.profile == None:
       parser.print_usage()
       sys.exit()
    
    stock = inStock(args.modelnumber, args.size, args.profile) # Get information about your size
    
    if stock.get('availability_status') == 'IN_STOCK': # Statement that checks if the desired size is still in stock
       addBag(args.modelnumber, args.size, args.profile)
    else: 
       print("The size you asked for isn't in stock anymore. Please try again with a different size.")
       sys.exit()

if __name__ == '__main__':
   main()
