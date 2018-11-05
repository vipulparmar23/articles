#import sys
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Articles
from flaskext.mysql import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from pymysql import IntegrityError
from functools import wraps
from pymysql.cursors import DictCursor

mysql = MySQL(cursorclass=DictCursor)

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'flaskapp'
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init mysql
mysql.init_app(app)

Articles = Articles()


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    #return render_template('articles.html', articles=Articles)
     # create cursor
    cursor = mysql.connect().cursor()

    # get articles
    result = cursor.execute('SELECT * FROM articles')
    # app.logger.info(result)
    articles = cursor.fetchall()
    # app.logger.info(articles)

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = "No articles found"
        return render_template('articles.html', msg=msg)

    cursor.close()

@app.route('/articles/article/<string:id>', methods=['GET', 'POST'])
def article(id):

    cursor = mysql.connect().cursor()

    result = cursor.execute('SELECT * FROM articles WHERE id=%s',[id])
    article = cursor.fetchone()
    return render_template('article.html', article=article)
    cursor.close()

class RegisterForm(Form):
    name = StringField('Name', [validators.length(
        min=1, max=50)], render_kw={"placeholder": "Name"})
    username = StringField('Username', [validators.length(
        min=4, max=25)], render_kw={"placeholder": "Username"})
    email = StringField('Email', [validators.length(
        min=6, max=50)], render_kw={"placeholder": "Email"})
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message="Passwords do not match")
    ], render_kw={"placeholder": "Password"})
    confirm = PasswordField('Confirm Password', render_kw={
                            "placeholder": "Confirm Password"})

# Register User
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create cursor
        cursor = mysql.connect().cursor()

        # Execute the query
        try:
            cursor.execute("INSERT INTO users(name, username, password, email) VALUES (%s, %s, %s, %s)",
                           (name, username, password, email))
            cursor.connection.commit()
            cursor.close()
            flash('You are now registered and can log in', 'success')
        except IntegrityError:
            flash('The email ID already exists. Try another.', 'danger')

        redirect(url_for('login'))
    return render_template('register.html', form=form)

# Login user
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        # get form fields
        username = request.form['username']
        password_user = request.form['password']

        app.logger.info(password_user)

        # create cursor
        cursor = mysql.connect().cursor()

        # get user by username
        result = cursor.execute(
            'SELECT * FROM users WHERE username = %s', [username])

        if(result > 0):
            # get stored hash
            password = cursor.fetchone()

            app.logger.info(password)

            # compare passwords
            if sha256_crypt.verify(password_user, password['password']):
                # passed.
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                # app.logger.info('PASSWORD NO MATCH')
                error = 'Invalid login'
                return render_template('login.html', error=error)
                cursor.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please log in', 'danger')
            return redirect(url_for('login'))
    return wrap

# To dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # create cursor
    cursor = mysql.connect().cursor()

    # get articles
    result = cursor.execute('SELECT * FROM articles')
    app.logger.info(result)
    articles = cursor.fetchall()
    app.logger.info(articles)

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = "No articles found"
        return render_template('dashboard.html', msg=msg)


    cursor.close()
# article form class
class ArticleForm(Form):
    title = StringField('Title', [validators.length(min=1, max=200)], render_kw={"placeholder":"Title"})
    body = TextAreaField('Body', [validators.length(min=30)], render_kw={"placeholder":"Body"})

# add article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)

    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # create a cursor
        cursor = mysql.connect().cursor()
        # Execute
        cursor.execute('INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)',
                       (title, body, session['username']))

        # Commit to DB
        cursor.connection.commit()
        
        # close connection
        cursor.close()

        flash('Article created', 'success')

        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    
    cursor = mysql.connect().cursor()

    result = cursor.execute("SELECT * FROM articles WHERE id=%s", [id])

    article = cursor.fetchone()
    cursor.close()

    form = ArticleForm(request.form)

    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # create a cursor
        cursor = mysql.connect().cursor()
        # Execute
        cursor.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))

        # Commit to DB
        cursor.connection.commit()
        
        # close connection
        cursor.close()

        flash('Article updated', 'success')

        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)


# Logging user out
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.secret_key = "secret123"
    app.run(debug=True)
