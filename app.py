#import sys
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Articles
from flaskext.mysql import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from pymysql import IntegrityError

mysql = MySQL()

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'flaskapp'
app.config['MYSQL_DATABASE_PORT'] = 3306
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

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
    return render_template('articles.html', articles=Articles)

@app.route('/articles/article/<string:id>')
def article(id):
    return render_template('article.html', id=id)

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

        redirect(url_for('index'))
    return render_template('register.html', form=form)

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
        result = cursor.execute('SELECT * FROM users WHERE username = %s', [username])

        if(result>0):
            # get stored hash
            password = cursor.fetchone()
            app.logger.info(password[3])

            # compare passwords
            if sha256_crypt.verify(password_user, password[3]):
                # passed. 
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                # app.logger.info('PASSWORD NO MATCH')
                error = 'Invalid login'
                return render_template('login.html', error=error)
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.secret_key = "secret123"
    app.run(debug=True)