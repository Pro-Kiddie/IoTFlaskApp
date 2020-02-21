from flask import current_app
from flask_iot_app import db, loginManager
from datetime import datetime
from flask_login import UserMixin # Your User Class Can inherits from this class to get all LoginManager's necessary methods (e.g. is_authenticated()) for it to work 
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer # Generates a secret URL with expiration time for resetting password. Can attach a payload (e.g. user id) with the URL and get it back when the URL is received 


# Create each Table in the database as a Class
# Essentially the Models in MVC (Model-View-Controller) to transfer data between webpage, server, database
class User(db.Model, UserMixin): # Superclass from SQLALchemy
    # Columns as class variable
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(30), unique=True, nullable=False)
    # Contains the path to user's profile picture
    image_file = db.Column(db.String(20), nullable=False, default="default.jpg")
    # Password will be stored in hash of fixed length. 60 because bcrypt library produce a hash of 59 or 60 unicode characters
    password = db.Column(db.String(60), nullable=False)
    # One-to-Many relationship
    # It is not a column , hence will not see in database
    # It is an query performed by SQLAlchemy on Post table with each user to get all posts posted by each
    # backref is a feature to allow queries on Post table to get access to the corresponding user
    posts = db.relationship('Post', backref='author', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config["SECRET_KEY"], expires_sec) # Needs an secret key to generate the secret URL which expires within seconds specified
        return s.dumps({"user_id" : self.id}).decode("utf-8") # {"user_id" : self.id} is the payload that will be returned when the secret URL is received
        # The secret URL serialized as bytes must dump as string. 

    @staticmethod 
    def verify_reset_token(token):
        s = Serializer(current_app.config["SECRET_KEY"]) # Loads the same secret key to decrypt the token
        try:
            user_id = s.loads(token)["user_id"] # "user_id" is the payload
        except: # token could be invalid or expired which will throw exception when trying to loads()
            return None 
        return User.query.get(user_id) # Return the user object for resetting its password if valid token

    def __repr__(self):
        return "User('{}', '{}', '{}')".format(self.name, self.email, self.image_file)
    

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # Pass in function pointer as it will be called when it is created in database
    content = db.Column(db.Text, nullable=False)
    # This is how you specify a foreign key in an SQLAlchemy Table class
    # "user.id" all small case as it is actually referencing the actual table.column in database
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return "Post('{}', '{}')".format(self.title, self.date_posted)

# Test the database in cmd:
# from flask_controller import db, User, Post

# CREATE TABLE
# db.create_all() # site.db will be created

# INSERT
# user1 = User(email="anlin@gmail.com", name="Anlin", password="password")
# db.session.add(user1)
# db.session.commit()

# SELECT
# User.query.all() # returns a list of of all Users!
# User.query.first() # Methods inherited from SQLAlchemy.Model 
# User.query.filter_by(name='Anlin').all()
# user = User.query.filter_by(name='Anlin').first()
# user.id, user.name, user.email
# User.query.get(1) # Get user by primary key
# Post.query.order_by(Post.date_posted.desc()).all() # Get all posts with date descending

# UPDATE
# user.image_file = "default.jpg" # Update row's column
# db.session.delete(user) # Delete user

# SECONDARY_KEY + BACKREF
# post1 = Post(title="Blog 1", content="First Post", user_id=1)
# db.session.add(post1)
# db.session.commit()
# user1.posts # Access all user1's posts. Thanks to secondary_key + BACKREF 
# post = Post.query.first()
# post.author # BACKREF to Gives the user object!

# DELETE TABLE
# db.drop_all()

# PAGINATION
# For tables that have many rows and you want to display them all, but separate them into pages, SQLAlchemy provides pagenate()
# posts = Post.query.paginate(per_page=5)
# dir(posts) # to see all class variables and methods
# posts.page # current page we are currently on
# for post in posts.items: # look through the posts in this page
# posts.total # returns the total number of rows
# for page_num in posts.iter_pages() # returns the different page numbers. However, it will include None value for hiding the pages behind certain page. E.g. 5

# How to use paginate in flask app
# @app.route("/")
# def home():
#     page = requests.args.get('page', 1, type=int) # Get request parameter, default is 1 and type must be int
#     posts = Post.query.paginate(page=page, per_page=5)
#     return render_template('home.html', posts=posts)

# http://<server>?page=2


# LoginManager needs to know how to load a user from the database to carry out necessary operatons like login/logout user
@loginManager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))






