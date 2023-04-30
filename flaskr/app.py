from flask import Flask, render_template, request, redirect, url_for, session, flash
from io import BytesIO
from flask_session import Session
from jinja2 import Template
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import datetime
import base64
import requests
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
app = Flask(__name__)
app.secret_key = 'shankh'

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'shankh'
app.config['MYSQL_DB'] = 'user'
mysql = MySQL(app)


class Product():
    def __init__(self, name, category, price, image, description):
        self.name = name
        self.category = category
        self.price = price
        self.image = image
        self.description = description

def translate_text(data,target):
    url = "https://microsoft-translator-text.p.rapidapi.com/translate"
    payload = [{ "Text": data }]
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "cd3e9d0bb3msh83f57bdfb33302ap1c13a9jsnfe59a8c7215f",
        "X-RapidAPI-Host": "microsoft-translator-text.p.rapidapi.com"
    }
    querystring = {"to[0]":target,"api-version":"3.0","from":"en","profanityAction":"NoAction","textType":"plain"}
    response = requests.post(url, json=payload, headers=headers, params=querystring)
    return (response.text)[27:-15]

def insert_profile(first_name,last_name,username,email,password, address, image_data):
   cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
   check=cursor.execute('SELECT * FROM profile WHERE username = (% s) ', (username,))
   report=tuple(cursor.fetchall())
   check_mail=cursor.execute('SELECT * FROM profile WHERE email = (% s) ', (email,))
   report_mail=tuple(cursor.fetchall())
   if (report != ()): 
       return 0
   elif (report_mail != ()): return 2
   else:  
        cursor.execute('create table chat.{} (user_id VARCHAR(100), sender_id VARCHAR(100), message VARCHAR(1000), date DATE, time TIME)'.format(username))
        cursor.execute('create table wishlist.{} (s_no int);'.format(username))
        cursor.execute('INSERT INTO profile VALUES (% s,% s,% s ,% s,% s, % s, % s);', (first_name,last_name,username, email, password, address, image_data))
        mysql.connection.commit()
   cursor.close()
   return(1)

def insert_chat(user_id_1, user_id_2,sender_id, message, date, time):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('USE chat;')
    cursor.execute('INSERT INTO {} VALUES (% s,% s ,% s,% s, % s);'.format(user_id_1), (user_id_2, sender_id, message, date, time))
    mysql.connection.commit()
    cursor.execute('INSERT INTO {} VALUES (% s,% s ,% s,% s, % s);'.format(user_id_2), (user_id_1, sender_id, message, date, time))
    mysql.connection.commit()
    cursor.execute('use user;')
    cursor.close()
    
def product(slug):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('select * from products where slug=(%s)',(slug,))
    rep=tuple(cursor.fetchone())
    return rep

def insert_wishlist(product_id,username):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('use wishlist')
    cursor.execute('insert into {} values (%s);'.format(username),(product_id,))
    mysql.connection.commit()
    rep=tuple(cursor.fetchall())
    cursor.close()
    return rep


@app.route('/')
def hello():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('use user;')
    cursor.execute('SELECT COUNT(*) FROM profile;')
    user_count = cursor.fetchall()
    user_count = user_count[0]['COUNT(*)']
    cursor.execute('use product;')
    cursor.execute('SELECT COUNT(*) FROM products;')
    prod_count = cursor.fetchall()
    prod_count = prod_count[0]['COUNT(*)']
    cursor.execute('select distinct category from products;')
    category_count = len(cursor.fetchall())


    return render_template('index.html',user_count=user_count,prod_count=prod_count,category_count=category_count)

@app.route('/login.html/register', methods = ['GET', 'POST'])
def register_user():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        user_mail = request.form.get("email")
        password = request.form.get("pwd")
        password=generate_password_hash(password, "sha256")
        username = request.form.get("Username")
        address = request.form.get("address")
        image = request.files["img"]
        img_path = '{}'.format(username)
        image.save(img_path)
        with open(img_path, 'rb') as f:
            image_data = f.read()

        check = insert_profile(first_name, last_name, username, user_mail, password, address, image_data)
        if check == 0 : 
            return "<script> alert('Username already exists!') </script>"
        elif check == 2 : 
            return "<script> alert('Email id already registered!') </script>"
        session['username'] = username
        session['Language'] = "en"
        return redirect(url_for('welcome_user'))
    return render_template('login.html')

@app.route('/login.html/login', methods = ['GET', 'POST'])
def user_login():
    if request.method == "POST":
        username = request.form.get("login_username")
        user_pwd = request.form.get("login_pwd")
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        check=cursor.execute('SELECT password FROM profile WHERE username = (% s) ', (username,))
        report=tuple(cursor.fetchall())

        if (report == ()):
            return "<script> alert('Unauthorized User') </script>"
        elif (not (check_password_hash(report[0]['password'],user_pwd))) : 
            return "<script> alert('Incorrect Login ID or Password!') </script>"
        else :
            session['username'] = username
            session['Language'] = "en"
            print(session['username'],"tfyguhgfhjhk")
            return redirect(url_for('welcome_user'))
    return render_template("login.html")


@app.route('/logout')
def logout():
    session['username'] = None
    return redirect('/')


@app.route('/landing_page.html', methods = ['GET', 'POST'])
def welcome_user():
    if not session.get('username'):
        return redirect(url_for('user_login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('use user;')
    cursor.execute('SELECT COUNT(*) FROM profile;')
    user_count = cursor.fetchall()
    user_count = user_count[0]['COUNT(*)']

    cursor.execute('use product;')
    cursor.execute('SELECT COUNT(*) FROM products;')
    prod_count = cursor.fetchall()
    prod_count = prod_count[0]['COUNT(*)']
    cursor.execute('select distinct category from products;')
    category_count = len(cursor.fetchall())
    cursor.execute("use product;")
    cursor.execute('select * from products order by s_no DESC LIMIT 5;')
    newarr = cursor.fetchall()
    prodlist = []
    for row in newarr:
        product = {
            'name': row['name'],
            'description': row['description'],
            'category': row['category'],
            'price': row['price'],
            'image': base64.b64encode(row['image']).decode('utf-8'),
            'id': row['s_no']
        }
        prodlist.append(product)
    # print(Language[0])
    return render_template("landing_page.html", user_count = user_count, prod_count =prod_count,category_count=category_count, newarr=prodlist)

@app.route('/landing_page.html', methods = ['GET', 'POST'])
def go_to_about():
    if not session.get('username'):
        return redirect(url_for('user_login'))
    return render_template("landing_page.html#about")

@app.route('/landing_page.html', methods = ['GET', 'POST'])
def go_to_contact():
    if not session.get('username'):
        return redirect(url_for('user_login'))
    return render_template("landing_page.html#contact")

@app.route('/chatbox.html')
def sessions():
    user_id2 = request.args.get('user_id2')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('USE chat;')
    user_id = session.get('username')
    print(user_id,"kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
    cursor.execute('select * from {} where user_id="{}";'.format(user_id,user_id2))
    report=list(cursor.fetchall())
    cursor.execute("USE user;")
    cursor.execute('select user_img from profile where username = "{}"'.format(user_id2))
    result = cursor.fetchall()
    img_data = result[0]['user_img']
    img_data_b64 = base64.b64encode(img_data).decode('utf-8')
    Language=session['Language']
    if (Language!="en"):
        for i in range(len(report)):
            report[i]["message"]=translate_text(report[i]["message"],Language)
    # print(report)
    # for chat in report:
    #     sender_id = chat['sender_id']
    #     if (sender_id == user_id): direction = "right"
    #     else : direction = "left"
    cursor.execute('USE user;')
    cursor.close()
    return render_template("chat.html", report = report, user_id2=user_id2, user_id=user_id, img_data_b64 = img_data_b64)


# @socketio.on('message')
# def handle_message(message):
#     user_id = session.get('username')
#     print(user_id,"hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
#     now=datetime.datetime.now()
#     date,time=now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")
#     print(date,time)
#     send(message, broadcast=True)
#     insert_chat(user_id,seller_id,user_id,message,date,time)

@app.route("/chatbox.html", methods = ['GET', 'POST'])
def handle_message():
    user_id2 = request.args.get('user_id2')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("USE user;")
    cursor.execute('select user_img from profile where username = "{}"'.format(user_id2))
    result = cursor.fetchall()
    img_data = result[0]['user_img']
    img_data_b64 = base64.b64encode(img_data).decode('utf-8')

    if request.method == "POST" : 
        user_id2 = request.args.get('user_id2')
        user_id = session.get('username')
        message = request.form.get("message")
        now=datetime.datetime.now()
        date,time=now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")
        insert_chat(user_id,user_id2,user_id, message,date,time)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("USE chat;")
        cursor.execute('select * from {} where user_id="{}";'.format(user_id,user_id2))
        report=list(cursor.fetchall())
        print(report,"111111111111111111111111111111111111111111111111124444444444444444444444444444444444")
        Language=session['Language']
        if (Language!="en"):
            for i in range(len(report)):
                report[i]["message"]=translate_text(report[i]["message"],Language)
        # return render_template("chat.html", report=report, user_id2=user_id2, user_id=user_id, img_data_b64= img_data_b64)
        return redirect(url_for("sessions",user_id2=user_id2))
    
    else: return render_template("chat.html", user_id2 = user_id2, img_data_b64=img_data_b64)


@app.route('/chats.html')
def select_chat():
    user_id = session.get('username')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('USE chat;')
    cursor.execute('select distinct user_id from {}'.format(user_id))
    report=cursor.fetchall()
    cursor.execute('Use user;')
    data=[]
    for i in range(len(report)):
        (cursor.execute('Select * from profile where username="{}"'.format(report[i]['user_id'])))
        user =cursor.fetchall()[0]
        user['user_img']=base64.b64encode(user['user_img']).decode('utf-8')
        data.append(user)
    return render_template("chat_app.html",report = data)


@app.route('/profile')
def show_profile():
    user_id = session.get('username')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('USE user;')
    cursor.execute('select * from profile where username = "{}"'.format(user_id))
    data = cursor.fetchall()
    cursor.execute('select user_img from profile where username = "{}"'.format(user_id))
    result = cursor.fetchone()

    products=[]
    cursor.execute('USE product;')
    cursor.execute('select * from products WHERE username="{}"'.format(user_id))
    results=cursor.fetchall()
    for row in results:
        product = {
            'name': row['name'],
            'description': row['description'][:40]+"......",
            'category': row['category'],
            'price': row['price'],
            'image': base64.b64encode(row['image']).decode('utf-8'),
            'id': row['s_no']
        }
        products.append(product)
    if result['user_img'] != None:
        img_data = result['user_img']
        img_data_b64 = base64.b64encode(img_data).decode('utf-8')
    else:
        img_data_b64 = None
    cursor.execute('select * from product.products')
    results=tuple(cursor.fetchall())
    all_products=[]
    for row in results:
        product = {
            'name': row['name'],
            'description': row['description'][:40]+"......",
            'category': row['category'],
            'price': row['price'],
            'image': base64.b64encode(row['image']).decode('utf-8'),
            'id': row['s_no']
        }
        all_products.append(product)
    cursor.execute('select * from wishlist.{} '.format(user_id))
    wishlist = tuple(cursor.fetchall())

    return render_template("profile.html", img_data_b64=img_data_b64, data=data, products=products,wishlist=wishlist,all_products=all_products)


@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    user_id = session.get('username')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('USE user;')
    cursor.execute('select * from profile where username = "{}"'.format(user_id))
    data = cursor.fetchall()
    cursor.execute('select user_img from profile where username = "{}"'.format(user_id))
    result = cursor.fetchone()
    if result['user_img'] != None:
        img_data = result['user_img']
        img_data_b64 = base64.b64encode(img_data).decode('utf-8')
    else:
        img_data_b64 = None
    if request.method == "POST":
        firstname = request.form.get("first")
        lastname = request.form.get("last")
        email = request.form.get("email")
        address = request.form.get("address")
        cursor.execute("UPDATE profile SET firstname=% s, lastname = % s, email = % s ,address = % s where username = '{}';".format(user_id), (firstname, lastname, email, address))
        mysql.connection.commit()
        return redirect(url_for('show_profile'))
    return render_template("profile_edit.html", data=data, img_data_b64=img_data_b64)


@app.route('/products')
def show_products():
    user_id=session['username']
    print(user_id,"huuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu")
    category = request.args.get('category')
    user_id=session['username']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('USE product;')
    if category=="all_categories":
        cursor.execute('select * from products'.format(category))
    else:
        cursor.execute('select * from products where category = "{}"'.format(category))
    results = cursor.fetchall()
    data=[]
    for row in results:
        product = {
            'name': row['name'],
            'description': row['description'][:40]+"......",
            'category': row['category'],
            'price': row['price'],
            'image': base64.b64encode(row['image']).decode('utf-8'),
            'id': row['s_no']
        }
        data.append(product)

    cursor.execute('select * from wishlist.{} '.format(user_id))
    wishlist = tuple(cursor.fetchall())
    return render_template("product_catalogue.html", data = data,wishlist=wishlist,user_id=user_id)

@app.route('/products/wishlist_add', methods=['GET'])
def add_wishlist():
    if not session.get('username'):
        return redirect(url_for('hello'))
    product_id = request.args.get('product_id')
    user_id=session['username']
    print(product_id,user_id)
    insert_wishlist(product_id,user_id)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("use product;")
    cursor.execute("select category from products where s_no = '{}'".format(product_id))
    data = cursor.fetchall()
    return redirect(url_for("show_products", category=data[0]['category']))

@app.route('/products/wishlist_remove', methods=['GET','POST'])
def remove_wishlist():
    if not session.get('username'):
        return redirect(url_for('hello'))
    product_id = request.args.get('product_id')
    user_id=session['username']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("USE wishlist")
    cursor.execute("delete from {} where s_no=(%s);".format(user_id),(product_id,))
    mysql.connection.commit()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("use product;")
    cursor.execute("select category from products where s_no = '{}'".format(product_id))
    data = cursor.fetchall()
    return redirect(url_for("show_products", category=data[0]['category']))

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if not session.get('username'):
        return redirect(url_for('hello'))
    message = ""
    userid = session.get('username')
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        image = request.files['image'].read()
        description = request.form['description']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO product.products (name, username, category, price, image, description) VALUES (%s,% s, %s, %s, %s, %s)", (name, userid ,category, price, image, description))
        mysql.connection.commit()
        return redirect(url_for("show_products", category = category))
    return render_template("product_upload.html")

@app.route('/product_details', methods=['GET', 'POST'])
def prod_details():
    prodID = request.args.get('prodID')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('USE product;')
    cursor.execute('select * from products where s_no = "{}"'.format(prodID))
    data = cursor.fetchall()
    cursor.execute("select image from products where s_no = '{}' ".format(prodID))
    result = cursor.fetchall()
    img_data = result[0]['image']
    img_data_b64 = base64.b64encode(img_data).decode('utf-8')
    # print(data[0]['name'],"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    return render_template("product_description.html", data=data[0], img_data_b64=img_data_b64)

@app.route('/add_contact')
def add_chat_contact():
    seller_id = request.args.get('seller_id')
    user_id = session.get('username')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    now=datetime.datetime.now()
    date,time=now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")
    cursor.execute('USE chat;')
    cursor.execute("INSERT INTO {} VALUES (%s,% s, %s, %s, %s)".format(user_id), (seller_id, user_id ,"Chat Connected",date ,time ))
    cursor.execute("INSERT INTO {} VALUES (%s,% s, %s, %s, %s)".format(seller_id), (user_id, user_id ,"Chat Connected",date ,time ))
    mysql.connection.commit()
    return redirect(url_for('select_chat'))

@app.route('/search_results', methods=['GET', 'POST'])
def search_results():
    if request.method == 'POST':
        user_id=session['username']
        search_query = request.form.get('search_query')
        print(search_query) 
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("USE product")
        cursor.execute("SELECT * FROM products WHERE name LIKE %s", ('%' + search_query + '%',))
        results=cursor.fetchall()
        data=[]
        for row in results:
            product = {
                'name': row['name'],
                'description': row['description'][:40]+"......",
                'category': row['category'],
                'price': row['price'],
                'image': base64.b64encode(row['image']).decode('utf-8'),
                'id': row['s_no']
            }
            data.append(product)
        cursor.execute('select * from wishlist.{} '.format(user_id))
        wishlist = tuple(cursor.fetchall())
        return render_template("product_catalogue.html", data = data,wishlist=wishlist,user_id=user_id)
    else:
        return redirect(url_for('show_products'))
    
@app.route('/profile/remove_prod')
def remove_product():
    prodID = request.args.get('prodID')
    print(prodID,"KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK")
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("USE product")
    cursor.execute("delete from products where s_no={}".format(prodID))
    mysql.connection.commit()
    return redirect(url_for('show_profile'))

@app.route('/profile/Choose_Language', methods=['GET', 'POST'])
def chooseLanguage():
    lang = request.form.get('lang')
    session['Language']=lang
    return redirect(url_for('welcome_user'))

    
if __name__ == "__main__":
    app.run(debug = True, port="5000")
