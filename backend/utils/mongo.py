import os
import pymongo
import sys
from dotenv import load_dotenv
from enum import Enum
from datetime import datetime
import google.generativeai as genai
import requests
import json

load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
ocr_key = os.getenv("OCR_API_KEY")


# Fetch environment variables
db_password = os.getenv("DB_PASSWORD")

try:
    client = pymongo.MongoClient(f"mongodb+srv://mahesha:{db_password}@cluster0.4xv3s.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

except pymongo.errors.ConfigurationError:
    print("An Invalid URI host error was received. Is your Atlas host name correct in your connection string?")
    sys.exit(1)

db = client.inventory


# @app.route("/add_food/<collection: str>/<item_name: str>/<quantity: int>/<unit: str>/<expiryDate: str>",methods=['POST'])
def insert_food(collection, item_name, quantity, unit, expiryDate):
    db_collection = db[collection]
    db_collection.insert_one({"name": item_name, "quantity": quantity, "unit": unit, "expiryDate": expiryDate})


# @app.route("/count/<collection: str>/<name: str>",methods=['GET'])
def get_count(collection, item_name):
    results = db[collection].find({"name": item_name})
    amount = 0
    for result in results:
        amount += result["quantity"]
    # print(amount)
    return amount

# @app.route("/delete/<collection: str>/<item_name: str>/<amount: int>",methods=['POST'])
def delete_food1(collection, item_name, amount): #amount = 4
    foods = db[collection].find({"name": item_name}).sort({"expiryDate": 1}).to_list()
    total = 0 # 8
    for food in foods:
        total += food["quantity"]
    removed = 0
    i = 0
    while removed < amount and i < len(foods):
        food = foods[i]
        if food["quantity"] <= amount - removed:
            db[collection].delete_one({"_id": food["_id"]})
            removed += food["quantity"]
            i += 1
        else:
            db[collection].update_one({"_id": food["_id"]}, {"$set": {"quantity": food["quantity"] - (amount - removed)}})
            removed = amount

# @app.route("/inventory",methods=['GET'])
def get_inventory1():
    collections = db.list_collection_names()
    all_documents = {'fridge':[], 'pantry':[]}
    visited = set()
    for collection_name in collections:
        collection = db[collection_name]
        documents = collection.find()
        for document in documents:
            if document["name"] not in visited:
                item_info = {"name": document["name"], "quantity": get_count(collection_name, document["name"]), "unit": document["unit"]}
                all_documents[collection_name].append(item_info)
                visited.add(document["name"])
                # all_documents.append({"name": document["name"], "quantity": get_count(collection_name, document["name"]), "unit": document["unit"]})
                # all_documents.append(   (document["name"], get_count(collection_name, document["name"]), document["unit"])   )
                
    # print(all_documents)
    return all_documents
    


''' 
********************************************************************************
SCANNING AND GEMINI GENERATOR
********************************************************************************
'''

def scan_receipts(img=None):

    url = "https://api.ocr.space/parse/image"
    api_key = ocr_key
    image_path = "receipt2.png"

    with open(image_path, 'rb') as image_file:
        files = {
            'file': image_file
        }
        
        payload = {
            'language': 'eng',
            'isOverlayRequired': 'false',
            'iscreatesearchablepdf': 'false',
            'issearchablepdfhidetextlayer': 'false',
            'isTable': 'true'
        }

        headers = {
            'apikey': api_key
        }
        # Send the image to OCR.space
        response = requests.post(url, headers=headers, data=payload, files=files)
        result = response.json()

        # Print the result
        # print(result['ParsedResults'][0]['ParsedText'])
        res = result['ParsedResults'][0]['ParsedText'].split('\t\r\n')
        return ','.join(res)


def gemini_generator(prompt):
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel("gemini-1.5-pro-latest")
    result = model.generate_content(prompt)
    generated_json = result.text
    clean_json = generated_json.replace("```json", "").replace("```", "").strip()
    ingredients = json.loads(clean_json)
    return ingredients

    # date_str = f"Today's date is {datetime.now().date()}. Message = "

    # if input_form == Forms.STT:
    #     prompt = date_str + text + """: convert this into JSON format. Only output the JSON.

    #     Use this JSON schema:

    #     Food = {"name": str, count": int, "expiry": date}
    #     Return: {"pantry": list[Food], "fridge": list[Food]"""
    # elif input_form == Forms.RECEIPT:
    #     prompt = date_str + text + """: convert this into JSON format. Generalize the food items i.e. make lowercase and ensure spelling is correct and plural. Divide weight by average weight of item to obtain count. Only output the JSON. 

    #     Use this JSON schema:

    #     Food = {"name": str, count": int, "expiry": date}
    #     Return: {"pantry": list[Food], "fridge": list[Food]"""
    # else:
    #     # TODO : UPDATE THE JSON SCHEMA
    #     # ADD BREAKFAST DINNER LUNCH

    #     prompt = date_str + text + """: using these ingredients along with their quantities and units, give me 3 recipes for a dish in the following format e.g. [{“name”: “pasta”, “ingredients”: [“pasta sauce: 5 oz”, “frozen veggies: .2 lbs”, “raviolli: .1 lbs”], “instructions”: [“Boil the pasta”, “Add spices”, ...], “time“: 20 mins}
    #     and for the 
    #     Use this JSON schema:

    #     Food = {"name": str, count": int, "expiry": date}
    #     Return: {"pantry": list[Food], "fridge": list[Food]"""








            

# insert_food("fridge", "eggs", 8, None, "01/10/2024")
# insert_food("fridge", "eggs", 16, None, "01/12/2024")
# get_count("fridge", "eggs")
# insert_food("fridge", "milk", 3, "oz", "03/10/2024")
# insert_food("pantry", "bananas", 4, None, "04/10/2024")
# delete_food("pantry", "bananas", 2)
# delete_food("fridge", "milk", 3)
# delete_food("fridge", "eggs", 20)
# delete_food("fridge", "milk", 3)
# delete_food("pantry", "bananas", 4)
# get_inventory()