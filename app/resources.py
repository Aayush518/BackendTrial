from flask_restx import Resource, Namespace
from flask import request, session
from .models import *
from .api_models import user_model


ns = Namespace("api")

@ns.route("/")
class Index(Resource):
    def get(self):
        """Homepage."""
        return {"message": "Homepage"}


@ns.route("/login")
class Login(Resource):
    @ns.marshal_with(user_model)
    def post(self):
        """Log user in if credentials provided are correct."""
        login_email = request.form.get("login_email")
        login_password = request.form.get("login_password")

        try:
            current_user = User.query.filter(User.email == login_email, User.password == login_password).one()

            # Check if the user is blocked
            if current_user.is_blocked:
                return {"error": "Your account is blocked. Contact an admin for assistance."}, 403

        except NoResultFound:
            return {"error": "The email or password you have entered did not match our records. Please try again."}, 401

        # Get current user's friend requests and number of requests to display in badges
        received_friend_requests, sent_friend_requests = get_friend_requests(current_user.user_id)
        num_received_requests = len(received_friend_requests)
        num_sent_requests = len(sent_friend_requests)
        num_total_requests = num_received_requests + num_sent_requests

        # Use a nested dictionary for session["current_user"] to store more than just user_id
        session["current_user"] = {
            "first_name": current_user.first_name,
            "user_id": current_user.user_id,
            "num_received_requests": num_received_requests,
            "num_sent_requests": num_sent_requests,
            "num_total_requests": num_total_requests
        }

        return {"message": f"Welcome {current_user.first_name}. You have successfully logged in.",
                "user": current_user}


@ns.route("/block_user/<int:user_id>")
class BlockUser(Resource):
    def post(self, user_id):
        user = User.query.get(user_id)

        if user:
            # Update the is_blocked field
            user.is_blocked = True
            db.session.commit()
            return {"message": f'{user.first_name} {user.last_name} has been blocked.'}, 200
        else:
            return {"error": 'User not found'}, 404


@ns.route("/logout")
class Logout(Resource):
    def get(self):
        """Log user out."""
        del session["current_user"]
        return {"message": "Goodbye! You have successfully logged out."}


@ns.route("/signup")
class SignUp(Resource):
    @ns.marshal_with(user_model)
    def post(self):
        """Check if user exists in database, otherwise add user to database."""
        signup_email = request.form.get("signup_email")
        signup_password = request.form.get("signup_password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        city = request.form.get("city")

        city_id = City.query.filter(City.name == city).one().city_id

        try:
            User.query.filter(User.email == signup_email).one()

        except NoResultFound:
            new_user = User(city_id=city_id,
                            email=signup_email,
                            password=signup_password,
                            first_name=first_name,
                            last_name=last_name)
            db.session.add(new_user)
            db.session.commit()

            # Add same info to session for new user as per /login route
            session["current_user"] = {
                "first_name": new_user.first_name,
                "user_id": new_user.user_id,
                "num_received_requests": 0,
                "num_sent_requests": 0,
                "num_total_requests": 0
            }

            return {"message": "You have successfully signed up for an account, and you are now logged in.",
                    "user": new_user}
        else:
            return {"error": "An account already exists with this email address. Please login."}, 400


@ns.route("/users")
class UserList(Resource):
    @ns.marshal_list_with(user_model)
    def get(self):
        """Show list of users."""
        users = User.query.all()
        return users