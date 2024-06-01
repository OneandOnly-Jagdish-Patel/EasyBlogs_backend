from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
import bcrypt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = "Cant show right now for security reason"


app.config['MONGO_URI'] = 'Database link here'
mongo = PyMongo(app)


# Routes
@app.route('/')
def index():
    return render_template('blogmanage.html')

#Xavier worked on this!!!!
@app.route('/blog')
def blog():
    posts = mongo.db.posts.find().limit(10)
    return render_template('blog.html', posts=posts)

#Dev worked on this!!!!
@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'username': request.form['username']})

        if existing_user is None:
            hash_pass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'username': request.form['username'], 'password': hash_pass})
            session['username'] = request.form['username']
            flash('You were successfully registered')
            return redirect(url_for('index'))
        
        flash('That username already exists!')
        return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        login_user = users.find_one({'username': request.form['username']})

        if login_user:
            if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['username'] = request.form['username']
                flash('Logged in successfully')
                return redirect(url_for('index'))

        flash('Invalid username/password combination')
        return redirect(url_for('login'))

    return render_template('login.html')

#Need to fix something here-----------------------
@app.route('/logout')
def logout():
    session.clear()
    flash('You are logged out now!!!')
    return redirect(url_for('index'))
#------------------------------------

@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'username' in session:
        users = mongo.db.users
        if request.method == 'POST':
            users.update_one({'username': session['username']}, {'$set': {'username': request.form['username']}})
            flash('Profile successfully updated')
            return redirect(url_for('account'))
        
        user = users.find_one({'username': session['username']})
        return render_template('account.html', user=user)
    
    return redirect(url_for('login'))

def send_email_notification(post_id):
    users = mongo.db.users
    post = mongo.db.posts.find_one({'_id': post_id})
    
    msg = MIMEMultipart()
    msg['From'] = "Sender"
    msg['To'] = post['email']
    msg['Subject'] = 'New Blog Post Notification'
    body = f"Hi,\n\nA new blog post titled '{post['title']}' has been published.\n\nYou can read it here: \n\nRegards,\nYour Website Team"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP("server name here", "port here") as server:
            server.starttls()
            server.login("Username", "Password")
            server.sendmail("sender", post['email'], msg.as_string())
        print("Email notification sent successfully")
    except Exception as e:
        print("Error sending email notification:", str(e))


@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        posts = mongo.db.posts.find({'author': session['username']})
        return render_template('dashboard.html', posts=posts)
    
    flash('You need to login first')
    return redirect(url_for('login'))


@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'username' in session:
        if request.method == 'POST':
            posts = mongo.db.posts
            posts.insert_one({'title': request.form['title'], 'content': request.form['content'], 'author': session['username']})
            flash('Your post is created successfully')
            return redirect(url_for('dashboard'))

        return render_template('create_post.html')

    flash('You need to login first')
    return redirect(url_for('login'))


@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'username' in session:
        posts = mongo.db.posts
        post = posts.find_one({'_id': post_id})
        
        if post['author'] == session['username']:
            if request.method == 'POST':
                posts.update_one({'_id': post_id}, {'$set': {'title': request.form['title'], 'content': request.form['content']}})
                flash('Post updated successfully')
                return redirect(url_for('dashboard'))

            return render_template('edit_post.html', post=post)

        flash('You are not authorized to edit this post')
        return redirect(url_for('dashboard'))

    flash('You need to login first')
    return redirect(url_for('login'))


@app.route('/delete_post/<post_id>')
def delete_post(post_id):
    if 'username' in session:
        posts = mongo.db.posts
        post = posts.find_one({'_id': post_id})
        
        if post['author'] == session['username']:
            posts.delete_one({'_id': post_id})
            flash('Post deleted successfully')
            return redirect(url_for('dashboard'))

        flash('You are not authorized to delete this post')
        return redirect(url_for('dashboard'))

    flash('You need to login first')
    return redirect(url_for('login'))


@app.route('/my_posts')
def my_posts():
    if 'username' in session:
        posts = mongo.db.posts.find({'author': session['username']})
        return render_template('my_posts.html', posts=posts)
    
    flash('You need to login first')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
