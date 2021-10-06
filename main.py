from datetime import datetime

from flask import Flask, app,render_template, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask import request 
from flask_mail import Mail
import json
import os
import math

from werkzeug.utils import redirect


with open('config.json','r') as c:
    params = json.load(c)['params']

loacal_server = True    

app = Flask(__name__)
mail = Mail(app)
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.secret_key = 'super-secret-key'

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME  = params["gmail-user"],
    MAIL_PASSWORD  = params["gmail-password"]

)
mail = Mail(app)

if(loacal_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Contact(db.Model):
    sno = db.Column(db.Integer,          primary_key=True)
    name = db.Column(db.String(30),      nullable=False)            #sno, name, email, phone_num, msg
    email = db.Column(db.String(20),     nullable=False)
    phone_num = db.Column(db.String(13), nullable=False)
    msg = db.Column(db.String(120),      nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer,          primary_key=True)
    title = db.Column(db.String(80),      nullable=False)
    tagline = db.Column(db.String(80),   nullable = False)             #sno, title, slug, content, date
    slug = db.Column(db.String(30),     nullable=False)
    content = db.Column(db.String(50), nullable=False)
    
    date = db.Column(db.String(20),      nullable=False)

class About(db.Model):
    sno = db.Column(db.Integer,          primary_key=True)
    title_about = db.Column(db.String(80),      nullable=False)            #sno, title, slug, content, date
    
    content_about = db.Column(db.String(50), nullable=False)
    
    date = db.Column(db.String(20),      nullable=False)





@app.route('/')
def index():
    posts = Posts.query.filter_by().all()[0:params["no_of_posts"]]
    return render_template("index.html", params = params, posts = posts)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page', 1, type=str)
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)    


    

@app.route('/post/<string:post_slug>', methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by (slug = post_slug).first()
    return render_template("post.html", params = params, post = post)


@app.route('/about')
def about_route():
    abouts = About.query.filter_by().all()
    return render_template("about.html", params = params, abouts= abouts)

@app.route('/dashboard', methods = ['GET', 'POST'])
def signin():

    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params = params, posts = posts) 

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username == params['admin_user']  and  userpass == params['admin_password']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params = params, posts = posts)
    
    return render_template("signin.html", params=params)


@app.route('/edit/<string:sno>', methods=['GET', 'POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            
            date = datetime.now()

            if(sno=='0'):
                post = Posts(title = box_title, tagline = tline, slug=slug, content = content,  date = date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.box_title = box_title
                post.tline = tline
                post.slug = slug
                post.content = content
                
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)    
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params = params, post = post)   

@app.route('/delete/<string:sno>', methods=['GET', 'POST']) 
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')    


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')            

@app.route("/uploader" , methods=['GET', 'POST'])
def uploader():
    if "user" in session and session['user']==params['admin_user']:
        if request.method=='POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded successfully!"

                



@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if(request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contact(name = name, email = email, phone_num = phone, msg = message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name, sender = email, recipients = [params['gmail-user']], body = message + "\n" + name + "\n" + phone)
    
    
    return render_template("contact.html", params = params)



if __name__=="__main__":
    app.run(debug=True)

