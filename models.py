from unicodedata import name
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, nullable=False, unique=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)


    @classmethod
    def signup(cls, username, first_name, last_name, email, password):

        hashed_password = bcrypt.generate_password_hash(password)
        decoded_hashed_password = hashed_password.decode('utf-8')

        user = User(username = username, 
                    first_name = first_name, 
                    last_name = last_name, 
                    email = email, 
                    password = decoded_hashed_password)

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        users = [user.username for user in User.query.all()]
        if username in users:
            user = User.query.filter(User.username == username).first()
            if bcrypt.check_password_hash(user.password, password):
                return True
        return False


class FavList(db.Model):

    __tablename__ = 'fav_list'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=False)
    state = db.Column(db.String, nullable=False)
    restaurant_id = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))



