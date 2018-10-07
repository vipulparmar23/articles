from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import Articles
from flaskext.mysql import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt

mysql = MySQL()
# cursor = mysql.get_db.cursor()
# cursor = mysql.connect().cursor()

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
        cursor.execute("INSERT INTO users(name, username, password, email) VALUES (%s, %s, %s, %s)",
                       (name, username, password, email))

        # commit to DB
        cursor.connection.commit()

        # close connection
        cursor.close()

        flash('You are now registered and can log in', 'success')

        redirect(url_for('index'))

    return render_template('register.html', form=form)

if __name__ == '__main__':
    app.secret_key = "secret123"
    app.run(debug=True)
