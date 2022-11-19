import os
from flask import Flask, request, jsonify
import csv
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import warnings
from pymongo import MongoClient
warnings.filterwarnings('ignore')
pd.set_option('max_colwidth', 1000)
import json
# from flask_cors import CORS, cross_origin
from flask_jwt_extended import create_access_token, set_access_cookies, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required, JWTManager

app = Flask(__name__)
# app.config["JWT_COOKIE_SECURE"] = False
# app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_SECRET_KEY"] = "khdckwkrbkjbckcjbekj21321321" #os.environ.get('JWT_SECRET')  # Change this!
jwt = JWTManager(app)

client = MongoClient("mongodb+srv://root:root@cluster0.pgzm5ma.mongodb.net/?retryWrites=true&w=majority")
db = client.test
db = client.get_database('recommendation')
users = db.get_collection('users')
tokens = db.get_collection('tokens')



books = pd.read_csv('./dataset/Books.csv')
# users = pd.read_csv('./dataset/Users.csv')
ratings = pd.read_csv('./dataset/Ratings.csv')

# print(books.head(5))
# print("Books Data Set : Records {} and Features {}\n".format(books.shape[0],books.shape[1]))

def csv_to_json(csv_file_path):
    data_dict = {}
    arr = []
    with open(csv_file_path, encoding = 'utf-8') as csv_file_handler:
        csv_reader = csv.DictReader(csv_file_handler)
        for rows in csv_reader:
            arr.append(rows)
    return arr[0:100]

@app.route('/books')
# @jwt_required()
def books():
    books = csv_to_json('./dataset/Books.csv')
    return books

@app.route('/liked-books')
@jwt_required()
def liked():
    current_user = get_jwt_identity()
    # print(current_user)
    books = csv_to_json('./dataset/Books.csv')
    user = users.find_one({'email' : current_user})
    res = []
    for b in books:
        print(str(b['ISBN']), user['liked'])
        if str(b['ISBN']) in user['liked']:
            res.appennd(b)
    return res

@app.route('/token', methods=['GET', 'POST'])
def create_token():
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    user = users.find_one({'email':email})
    if email != user['email'] or password != user['password']:
        return jsonify({"msg": "Bad username or password"}), 401
    print('success')
    access_token = create_access_token(identity=email)
    del user['_id'], user['password']
    data ={'access_token':access_token, 'user':user}
    # token = tokens.insert_one({"token":access_token, 'expireAfterSeconds': 30 })
    # response = jsonify({"msg": "login successful"})
    # set_access_cookies(response, access_token)
    
    return jsonify(data)

@app.route('/sign-up', methods=["POST"])
def signup():
    name = request.json.get("name", None)
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    user = users.find_one({'email' : email})
    print(user)
    if not user:
        users.insert_one({"name":name, 'email': email, "password":password,"liked":[]})
        return jsonify({'msg':'success'})
    else:
        return jsonify({'msg': 'Account already exists!'})

@app.route('/like', methods=["POST"])
@jwt_required()
def like():
    id = request.json.get("id", None)
    liked = request.json.get("liked", None)
    current_user = get_jwt_identity()
    user = users.find_one({'email' : current_user})
    if liked and not user['liked']:
        users.update_one({'email' : current_user},{'$set':{ 'liked': [id] }})
    elif liked and id not in user['liked']:
        users.update_one({'email' : current_user},{'$push': { 'liked': id }})
    elif not liked and id in user['liked']:
        arr = user['liked'].remove(id)
        users.update_one({'email' : current_user},{'$set':{ 'liked': arr }})

    user = users.find_one({'email' : current_user})
    del user['_id'], user['password']
    return jsonify({'user' : user }), 200


@app.route('/profile', methods=["GET"])
@jwt_required()
def profile():
	current_user = get_jwt_identity() # Get the identity of the current user
	user = users.find_one({'email' : current_user})
	if user:
		del user['_id'], user['password'] # delete data we don't want to return
		return jsonify({'user' : user }), 200
	else:
		return jsonify({'msg': 'Profile not found'}), 404

@app.route("/logout", methods=["GET"])
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response

@app.route('/users')
def get_users():
    arr = []
    # print(arr)
    if users.find({}):
        for user in users.find({}):
            arr.append({"name": user['name'], "id": str(user['_id'])})
    # return arr
    # if users.find({}):
    #     for name in names_col.find({}).sort("name"):
    #         users.append({"name": name['name'], "id": str(name['_id'])})
    return users.find()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="5000")
#    app.run()


