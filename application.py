import pymongo
from pymongo.operations import InsertOne
from flask_session import Session
from flask import Flask, render_template, redirect, request, session, jsonify
from datetime import datetime

# # Instantiate Flask object named app
app = Flask(__name__)

# # Configure sessions
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem" 
Session(app)


client = pymongo.MongoClient("mongodb://localhost:27017/")
db=client["testDB"]
collection=db["shirts12"]   
user_collection=db["users"]
purchase_collection=db["purchases"]
if len(list(collection.find()))==0:
  
   mylist=[  
   { "id":1, "qty":1,  "team":"Argentina","price":100,"image":"argentina.png" },
   { "id":2, "qty":1,  "team":"Belgium","price":100,"image":"belgium.png" },
   {  "id":3, "qty":1 ,"team": "Boca Juniors","price":60,"image":"bj.jpg"},
   {  "id":4, "qty":1 , "team": "Brazil","price":70,"image":"brasil.jpg"},
   {  "id":5, "qty":1 , "team": "Columbia","price":110,"image":"colombia.jpg"},
   {  "id":6, "qty":1, "team": "Corinthians","price":80,"image":"cor.png"},
   { "id":7, "qty":1 , "team": "Costa Rica","price":90,"image":"costarica.jpg"},
   {  "id":8, "qty":1 , "team": "Croatia","price":150,"image":"croacia.jpg"},
   {"id":9,  "qty": 1, "team": "Egypt","price":120,"image":"egypt.jpg"},
   { "id":10, "qty":1 , "team": "Germany","price":130,"image":"germany.png"},
   {  "id":11, "qty":1,  "team": "Manchester United","price":180,"image":"mu.png"},
   {  "id":12, "qty":1 , "team": "Milan","price":200,"image":"mil.png"},

   ]
   collection.insert_many(mylist)

cart_collection=db["cart"]

@app.route("/")
def index():
    shirts = list(collection.find())
    shirtsLen = len(shirts)
    
    # Initialize variables
    shoppingCart = []
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    if 'user' in session:
        shoppingCart = list(cart_collection.aggregate([{"$group":{"_id":"$team","image":{"$first":"$image"},"price":{"$first":"$price"},"id":{"$first":"$id"},"quantity":{"$sum":"$qty"},"subTotal":{"$sum":"$subTotal"}}}]))
        shopLen = len(shoppingCart)
        for i in range(shopLen):
            total += shoppingCart[i]["subTotal"]
            totItems += shoppingCart[i]["quantity"]
        shirt_coll = list(collection.find().sort("team"))
        shirtsLen = len(shirt_coll)
        return render_template ("index.html", shoppingCart=shoppingCart, shirts=shirt_coll, shopLen=shopLen, shirtsLen=shirtsLen, total=total, totItems=totItems, display=display, session=session )
    return render_template ( "index.html", shirts=shirts, shoppingCart=shoppingCart, shirtsLen=shirtsLen, shopLen=shopLen, total=total, totItems=totItems, display=display)


@app.route("/buy/")
def buy():
    # Initialize shopping cart variables
    shoppingCart = []
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    qty = int(request.args.get('quantity'))
    if session:
        # Store id of the selected shirt
        id = int(request.args.get('id'))
        # Select info of selected shirt from database
        goods = list(collection.find({"id":id}))
        # Extract values from selected shirt record
        # Check if shirt is on sale to determine price

    
        price = goods[0]["price"]
        team = goods[0]["team"]
        image = goods[0]["image"]
        subTotal = qty * price
        # Insert selected shirt into shopping cart
        cart_collection.insert_one({"id":id,"price":price,"team":team,"image":image,"qty":qty,"subTotal":subTotal})
        shoppingCart = list(cart_collection.aggregate([{"$group":{"_id":"$team","image":{"$first":"$image"},"price":{"$first":"$price"},"id":{"$first":"$id"},"quantity":{"$sum":"$qty"},"subTotal":{"$sum":"$subTotal"}}}]))
       
        shopLen = len(shoppingCart)
        # Rebuild shopping cart
        for i in range(shopLen):
            total += shoppingCart[i]["subTotal"]
            totItems += shoppingCart[i]["quantity"]
        # Select all shirts for home page view
        shirts = list(collection.find().sort("team"))
        shirtsLen = len(shirts)
        # Go back to home page
        return render_template ("index.html", shoppingCart=shoppingCart, shirts=shirts, shopLen=shopLen, shirtsLen=shirtsLen, total=total, totItems=totItems, display=display, session=session )


@app.route("/update/")
def update():
    # Initialize shopping cart variables
    shoppingCart = []
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    qty = int(request.args.get('quantity'))
    if session:
        # Store id of the selected shirt
        id = int(request.args.get('id'))
        cart_collection.delete_many({"id":id})
        
        # Select info of selected shirt from database
        goods=collection.find({"id":id})
        
        # Extract values from selected shirt record
        # Check if shirt is on sale to determine price
   
        
        price = goods[0]["price"]
        team = goods[0]["team"]
        image = goods[0]["image"]
        subTotal = qty * price
        # Insert selected shirt into shopping cart
        cart_collection.insert_one({"id":id,"team":team,"price":price,"subTotal":subTotal,"image":image,"qty":qty})
        
        shoppingCart = list(cart_collection.aggregate([{"$group":{"_id":"$team","image":{"$first":"$image"},"price":{"$first":"$price"},"id":{"$first":"$id"},"quantity":{"$sum":"$qty"},"subTotal":{"$sum":"$subTotal"}}}]))
       
        shopLen = len(shoppingCart)
        # Rebuild shopping cart
        for i in range(shopLen):
            total += shoppingCart[i]["subTotal"]
            totItems += shoppingCart[i]["quantity"]
        # Go back to cart page
        return render_template ("cart.html", shoppingCart=shoppingCart, shopLen=shopLen, total=total, totItems=totItems, display=display, session=session )



  

@app.route("/checkout/")
def checkout():
    order=cart_collection.find()
    
    # Update purchase history of current customer
    for item in order:
         purchase_collection.insert_one({"uid":session["uid"],"id":item["_id"],"team":item["team"],"image":item["image"],"quantity":item["qty"],"date":session["time"]})
        
    # Clear shopping cart
    
    cart_collection.delete_many({})
    shoppingCart = []
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    # Redirect to home page
    return redirect('/')


@app.route("/remove/", methods=["GET"])
def remove():
    # Get the id of shirt selected to be removed
    out = int(request.args.get("id"))
    # Remove shirt from shopping cart
    cart_collection.delete_many({"id":out})
    
    # Initialize shopping cart variables
    totItems, total, display = 0, 0, 0
    # Rebuild shopping cart
    shoppingCart = list(cart_collection.aggregate([{"$group":{"_id":"$team","image":{"$first":"$image"},"price":{"$first":"$price"},"id":{"$first":"$id"},"quantity":{"$sum":"$qty"},"subTotal":{"$sum":"$subTotal"}}}]))
       
   
    shopLen = len(shoppingCart)
    for i in range(shopLen):
        total += shoppingCart[i]["subTotal"]
        totItems += shoppingCart[i]["quantity"]
    # Turn on "remove success" flag
    display = 1
    # Render shopping cart
    return render_template ("cart.html", shoppingCart=shoppingCart, shopLen=shopLen, total=total, totItems=totItems, display=display, session=session )


@app.route("/login/", methods=["GET"])
def login():
    return render_template("login.html")


@app.route("/new/", methods=["GET"])
def new():
    # Render log in page
    return render_template("new.html")


@app.route("/logged/", methods=["POST"] )
def logged():
    # Get log in info from log in form
    user = request.form["username"].lower()
    pwd = request.form["password"]
    
    # Make sure form input is not blank and re-render log in page if blank
    if user == "" or pwd == "":
        return render_template ( "login.html" )
    # Find out if info in form matches a record in user database
    query ={"username":user,"password":pwd} 
    rows = list(user_collection.find ( query ))

    # If username and password match a record in database, set session variables
    if len(rows) == 1:
        session['user'] = user
        session['time'] = datetime.now( )
        session['uid'] = rows[0]["_id"]
    # Redirect to Home Page
    if 'user' in session:
        return redirect ( "/" )
    # If username is not in the database return the log in page
    return render_template ( "login.html", msg="Wrong username or password." )


@app.route("/history/")
def history():
    # Initialize shopping cart variables
    shoppingCart = []
    shopLen = len(shoppingCart)
    totItems, total, display = 0, 0, 0
    # Retrieve all shirts ever bought by current user
    myShirts=list(purchase_collection.find({"uid":session["uid"]}))
    
    myShirtsLen = len(myShirts)
    # Render table with shopping history of current user
    return render_template("history.html", shoppingCart=shoppingCart, shopLen=shopLen, total=total, totItems=totItems, display=display, session=session, myShirts=myShirts, myShirtsLen=myShirtsLen)

@app.route("/show/", methods=["GET"])
def show():
    # Render log in page
   shoppingCart = list(cart_collection.aggregate([{"$group":{"_id":"$team","image":{"$first":"$image"},"price":{"$first":"$price"},"id":{"$first":"$id"},"quantity":{"$sum":"$qty"},"subTotal":{"$sum":"$subTotal"}}}]))
       
   total=0
   totItems=0
   display=0
   shopLen = len(shoppingCart)
   for i in range(shopLen):
        total += shoppingCart[i]["subTotal"]
        totItems += shoppingCart[i]["quantity"]
    # Turn on "remove success" flag
    
   return render_template ("cart.html", shoppingCart=shoppingCart, shopLen=shopLen, total=total, totItems=totItems, display=display, session=session )
   

@app.route("/logout/")
def logout():
    # clear shopping cart
    cart_collection.delete_many({})
    
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")


@app.route("/register/", methods=["POST"] )
def registration():
    # Get info from form
    username = request.form["username"]
    password = request.form["password"]
    confirm = request.form["confirm"]
    fname = request.form["fname"]
    lname = request.form["lname"]
    email = request.form["email"]
    # See if username already in the database
    rows = list(user_collection.find({"username":username}))
    # If username already exists, alert user
    if len( rows ) > 0:
        return render_template ( "new.html", msg="Username already exists!" )
    # If new user, upload his/her info into the users database
    new = user_collection.insert_one({"username":username,"password":password,"fname":fname,"lname":lname,"email":email})
    # Render login template
    return render_template ( "login.html" )









if __name__ == "__main__":
    app.run(debug=True)
