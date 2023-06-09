from flask import Flask, render_template, flash, request, redirect, url_for
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, \
    logout_user, current_user
from webforms import LoginForm, SearchForm, PostForm, UserForm, NamerForm, PasswordForm
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
import uuid
import os

# Create a Flask instance
app = Flask(__name__)
ckeditor = CKEditor(app)
# Add Database
# Old SQLITE DB
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
# New MYSQL DB
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'mysql+pymysql://root:password123@localhost/our_users'
# Secret Key
app.config['SECRET_KEY'] = "my_super_secret_key"
app.config['UPLOAD_FOLDER'] = 'static/images/upload/'
# Initialize Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#Flask_Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# Create Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            # Check the Hash:
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login Successful!")
                return redirect(url_for('dashboard'))
            else:
                flash("Wrong Password - Try Again!")
        else:
            flash("That User Doesn`t Exist - Try Again!")
    return render_template('login.html', form=form)


# Create Logout Page
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You Have Been Logged Out!")
    return redirect(url_for('login'))


# Create Dashboard Page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id
    name_to_update = Users.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.name = request.form['name']
        name_to_update.username = request.form['username']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
        name_to_update.about_author = request.form['about_author']

        if request.files['profile_pic']:
            name_to_update.profile_pic = request.files['profile_pic']
            #Create Uniqe Name for File
            pic_filename = secure_filename(name_to_update.profile_pic.filename)
            pic_name = str(uuid.uuid1()) + '_' + pic_filename
            # Save Image
            saver = request.files['profile_pic']

            name_to_update.profile_pic = pic_name
            try:
                db.session.commit()
                saver.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
                flash('User Updated Successfully!')
                return render_template('dashboard.html',
                                       name_to_update=name_to_update, form=form)
            except:
                flash('Error with Updating!!')
                return render_template('dashboard.html',
                                       name_to_update=name_to_update, form=form)
        else:
            db.session.commit()
            flash('User Updated Successfully!')
            return render_template('dashboard.html',
                                   name_to_update=name_to_update, form=form)
    else:
        return render_template('dashboard.html',
                           name_to_update=name_to_update, form=form, id=id)


# Add Post Page
@app.route('/add-post', methods=['GET', 'POST'])
# @login_required
def add_post():
    form = PostForm()
    # Validate The Form
    if form.validate_on_submit():
        poster = current_user.id
        post = Posts(title=form.title.data, content=form.content.data,
                     poster_id=poster, slug=form.slug.data)
        # Clear The Form
        form.title.data = ''
        form.content.data = ''
        form.slug.data = ''

        # Add Post To Database
        with app.app_context():
            db.session.add(post)
            db.session.commit()

        # Return a Massage
        flash("Blog Post Submitted Successfully!")

    # Redirect to Webpage
    return render_template('add_post.html', form=form)


# Create Blog Page
@app.route('/posts')
def posts():
    # Get all the posts from the database
    posts = Posts.query.order_by(Posts.date_posted.desc())

    # Redirect to Webpage
    return render_template('posts.html', posts=posts)


# View Of The Post
@app.route('/posts/<int:id>')
def post(id):
    # Get the post from the database
    post = Posts.query.get_or_404(id)

    # Redirect to Webpage
    return render_template('post.html', post=post)


# Edit Of The Post
@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    # Get the post from the database
    post = Posts.query.get_or_404(id)
    form = PostForm()

    # Validate The Form
    if form.validate_on_submit():
        # Update Data
        post.title = form.title.data
        post.slug = form.slug.data
        post.content = form.content.data

        # Update Database
        db.session.commit()

        # Return a Massage
        flash("Post Has Been Updated!")

        # Redirect to Webpage
        return redirect(url_for('post', id=post.id))
    if current_user.id == post.poster_id or current_user.id == 6:
        # Fill Out The Form Of Updating
        form.title.data = post.title
        form.slug.data = post.slug
        form.content.data = post.content

        # Redirect to Webpage
        return render_template('edit_post.html', form=form)
    else:
        flash("You Aren`t Authorized To Edit This Post!")
        posts = Posts.query.order_by(Posts.date_posted.desc())
        return render_template('posts.html', posts=posts)


# Delete Of The Post
@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
    # Get the post from the database
    post_to_delete = Posts.query.get_or_404(id)
    id = current_user.id
    if id == post_to_delete.poster.id or id == 6:
        try:
            # Delete From Database
            db.session.delete(post_to_delete)
            db.session.commit()

            # Return a Massage
            flash('Blog Post Was Deleted!')

            # Get all the posts from the database
            posts = Posts.query.order_by(Posts.date_posted.desc())

            # Redirect to Webpage
            return render_template('posts.html', posts=posts)

        except:
            # Return an Error Massage
            flash('Oops! There was a problem with deleting, try again...')

            # Get all the posts from the database
            posts = Posts.query.order_by(Posts.date_posted.desc())

            # Redirect to Webpage
            return render_template('posts.html', posts=posts)
    else:
        # Return a Massage
        flash('You Aren`t Authorized To Delete This Post!')

        # Get all the posts from the database
        posts = Posts.query.order_by(Posts.date_posted.desc())
        return render_template('posts.html', posts=posts)


#Pass to Navbar
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

#Create Search Function
@app.route('/search', methods=['POST'])
def search():
    form = SearchForm()
    posts = Posts.query
    if form.validate_on_submit():
        #Get Data From Submited Form
        post.searched = form.searched.data
        #Query The Database
        posts = posts.filter(Posts.content.like('%' + post.searched + '%'))
        posts = posts.order_by(Posts.title).all()

        return render_template('search.html', form=form, searched=post.searched, posts=posts)


# Add NEW Database Record
@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            # Hash the password
            hashed_pw = generate_password_hash(form.password_hash.data)

            user = Users(username=form.username.data, name=form.name.data, email=form.email.data, favorite_color=form.favorite_color.data, password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.username.data = ''
        form.email.data = ''
        form.favorite_color.data = ''
        form.password_hash.data = ''

        flash("User Added Successfully")
    our_users = Users.query.order_by(Users.date_added)
    return render_template('add_user.html', form=form, name=name,
                           our_users=our_users)


# Update Database Record
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.name = request.form['name']
        name_to_update.username = request.form['username']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
        name_to_update.about_author = request.form['about_author']

        try:
            db.session.commit()
            flash('User Updated Successfully!')
            return render_template('update.html',
                                   name_to_update=name_to_update, form=form)
        except:
            flash('Error with Updating!!')
            return render_template('update.html',
                                   name_to_update=name_to_update, form=form)
    return render_template('update.html',
                           name_to_update=name_to_update, form=form, id=id)


# Delete Database Record
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    if id == current_user.id:
        user_to_delete = Users.query.get_or_404(id)
        name = None
        form = UserForm()
        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash('User Deleted Successfully!')
            our_users = Users.query.order_by(Users.date_added)
            return render_template('add_user.html', form=form, name=name,
                                   our_users=our_users)
        except:
            flash('Error with Deleting!!')
            our_users = Users.query.order_by(Users.date_added)
            return render_template('add_user.html', form=form, name=name,
                                   our_users=our_users)
    else:
        flash('Sorry, you can`t delete this user!')
        return redirect(url_for('dashboard'))


# Create route decorator
@app.route('/')
def index():
    return render_template('index.html')


# Create Admin Page
@app.route('/admin')
@login_required
def admin():
    id = current_user.id
    if id == 6:
        return render_template('admin.html')
    else:
        flash("Sorry, you must be the Admin to access the Admin Page!")
        return redirect(url_for('dashboard'))

# http://127.0.0.1:5000/user/John
@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


# Invalid URL
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


# Internal Server Error
@app.errorhandler(500)
def page_not_found(error):
    return render_template('500.html'), 500


# Create Name Page
@app.route('/name', methods=['GET', 'POST'])
def name():
    name = None
    form = NamerForm()
    # Validate Form
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        flash("Form Submitted Successfully")
    return render_template('name.html', name=name, form=form)


# Create Password Test Page
@app.route('/test_pw', methods=['GET', 'POST'])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()

    # Validate Form
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        form.email.data = ''
        form.password_hash.data = ''

        # Lookup user by email
        pw_to_check = Users.query.filter_by(email=email).first()

        # Check hash password
        passed = check_password_hash(pw_to_check.password_hash, password)

    return render_template('test_pw.html', email=email, password=password,
                           form=form, pw_to_check=pw_to_check, passed=passed)


# Create Blog Post Model
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    # author = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    slug = db.Column(db.String(255))
    # Foreign Key to Users
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))


# Create User Model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    favorite_color = db.Column(db.String(120))
    about_author = db.Column(db.Text(500), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    profile_pic = db.Column(db.String(120), nullable=True)
    # Make password
    password_hash = db.Column(db.String(128))
    # User Can Have Many Posts(One-To-Many)
    posts = db.relationship('Posts', backref='poster')

    @property
    def password(self):
        raise AttributeError('password is not readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<Name %r>' % self.name


if __name__ == '__main__':
    app.run(debug=True)
