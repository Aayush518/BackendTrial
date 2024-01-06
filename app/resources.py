from flask_restx import Resource, Namespace
from flask import request, session
from .models import *
from .api_models import user_model, restaurant_model, visit_model
import sqlalchemy_utils 



import sys, os, json
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from jinja2 import StrictUndefined
# from flask import Flask, render_template, redirect, request, flash, session, jsonify, send_from_directory, url_for
# from PIL import Image
# from flask_migrate import Migrate
# from model import *
# from friends import *
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_searchable import search
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy.orm import joinedload
from datetime import datetime







ns = Namespace("api", description="API for Mitho-Mitho website.")
api.add_namespace(ns)



ns.models[user_model.name] = user_model
ns.models[restaurant_model.name] = restaurant_model
ns.models[visit_model.name] = visit_model

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
        """Check if user exists in database, otherwise add user to the database."""
        print("Received POST request to /api/signup")

        signup_email = request.form.get("signup_email")
        signup_password = request.form.get("signup_password")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        city = request.form.get("city")

        # Find the city with the specified name
        city_record = City.query.filter(City.name == city).first()

        if city_record is None:
            return {"error": f"No city found with name '{city}'"}, 404

        city_id = city_record.city_id

        try:
            # Check if user already exists with the provided email
            User.query.filter(User.email == signup_email).one()

        except NoResultFound:
            new_user = User(city_id=city_id,
                            email=signup_email,
                            password=signup_password,
                            first_name=first_name,
                            last_name=last_name)
            db.session.add(new_user)
            db.session.commit()

            # Add the same info to the session for the new user as per the /login route
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
            return {"error": "An account already exists with this email address. Please log in."}, 400
        
@ns.route("/users")
class UserList(Resource):
    @ns.marshal_list_with(user_model)
    def get(self):
        """Show list of users."""
        users = User.query.all()
        return users
@ns.route("/users/<int:user_id>")
class UserProfile(Resource):
    @ns.marshal_with(user_model)
    def get(self, user_id):
        """Show user profile with map and list of visited restaurants."""
        user = db.session.query(User).filter(User.user_id == user_id).one()

        # Get user's breadcrumbs in descending order
        breadcrumbs = db.session.query(Visit).filter(Visit.user_id == user_id).order_by(Visit.visit_id.desc())

        total_breadcrumbs = len(breadcrumbs.all())
        recent_breadcrumbs = breadcrumbs.limit(5).all()

        # Execute the friends query
        friends_query = get_friends_query(user.user_id)
        friends = friends_query.all()
        total_friends = len(friends)

        user_a_id = session["current_user"]["user_id"]
        user_b_id = user.user_id

        # Check connection status between user_a and user_b
        friends, pending_request = is_friends_or_pending(user_a_id, user_b_id)

        return {
            "user": user,
            "total_breadcrumbs": total_breadcrumbs,
            "recent_breadcrumbs": recent_breadcrumbs,
            "total_friends": total_friends,
            "friends": friends,
            "pending_request": pending_request
        }

@ns.route("/users/<int:user_id>/visits.json")
class UserRestaurantVisits(Resource):
    def get(self, user_id):
        """Return info about a user's restaurant visits as JSON."""
        user_visits = db.session.query(Visit).filter(Visit.user_id == user_id).all()

        rest_visits = {}

        for visit in user_visits:
            image_url = visit.restaurant.image_url if visit.restaurant.image_url else "/static/img/restaurant-avatar.png"
            phone = visit.restaurant.phone if visit.restaurant.phone else "Not Available"

            rest_visits[visit.visit_id] = {
                "restaurant": visit.restaurant.name,
                "rest_id": visit.restaurant.restaurant_id,
                "address": visit.restaurant.address,
                "phone": phone,
                "image_url": image_url,
                "latitude": float(visit.restaurant.latitude),
                "longitude": float(visit.restaurant.longitude)
            }

        return jsonify(rest_visits)

@ns.route("/add-friend")
class AddFriend(Resource):
    def post(self):
        """Send a friend request to another user."""
        user_a_id = session["current_user"]["user_id"]
        user_b_id = request.form.get("user_b_id")

        # Check connection status between user_a and user_b
        is_friends, is_pending = is_friends_or_pending(user_a_id, user_b_id)

        if user_a_id == user_b_id:
            return "You cannot add yourself as a friend."
        elif is_friends:
            return "You are already friends."
        elif is_pending:
            return "Your friend request is pending."
        else:
            requested_connection = Connection(user_a_id=user_a_id,
                                              user_b_id=user_b_id,
                                              status="Requested")
            db.session.add(requested_connection)
            db.session.commit()
            print(f"User ID {user_a_id} has sent a friend request to User ID {user_b_id}")
            return "Request Sent"

@ns.route("/accept-friend-request")
class AcceptFriendRequest(Resource):
    def post(self):
        """Accept a friend request from another user."""
        user_b_id = session["current_user"]["user_id"]
        user_a_id = request.form.get("user_a_id")

        # Update the connection status to "Accepted" in the database
        connection = db.session.query(Connection).filter(
            Connection.user_a_id == user_a_id,
            Connection.user_b_id == user_b_id,
            Connection.status == "Requested"
        ).first()

        if connection:
            connection.status = "Accepted"
            db.session.commit()

            # Optionally, you can add logic here to update the sender's friends list as well

            flash("You have accepted the friend request.", "success")
        else:
            flash("Friend request not found.", "danger")

        return redirect("/friends")

@ns.route("/friends")
class FriendsList(Resource):
    def get(self):
        """Show the user's friends and friend requests."""
        user_id = session["current_user"]["user_id"]

        # Get accepted friend connections excluding the current user
        friends = (
            Connection.query
            .join(User, (Connection.user_b_id == User.user_id) | (Connection.user_a_id == User.user_id))
            .filter(
                ((Connection.user_a_id == user_id) | (Connection.user_b_id == user_id)) &
                (Connection.status == 'Accepted') &
                (User.user_id != user_id)
            )
            .with_entities(User)
            .all()
        )

        received_friend_requests, sent_friend_requests = get_friend_requests(user_id)

        return {
            "friends": friends,
            "received_friend_requests": received_friend_requests,
            "sent_friend_requests": sent_friend_requests
        }

@ns.route("/friends/search")
class SearchUsers(Resource):
    def get(self):
        """Search for a user by email and return results."""
        received_friend_requests, sent_friend_requests = get_friend_requests(session["current_user"]["user_id"])
        friends_query = get_friends_query(session["current_user"]["user_id"])
        friends = friends_query.all()

        user_input = request.args.get("q")

        search_results = search(db.session.query(User), user_input).all()

        return {
            "received_friend_requests": received_friend_requests,
            "sent_friend_requests": sent_friend_requests,
            "friends": friends,
            "search_results": search_results
        }

@ns.route("/restaurants")
class RestaurantList(Resource):
    def get(self):
        """Show list of restaurants."""
        restaurants = db.session.query(Restaurant).order_by(Restaurant.name).all()

        return {"restaurants": restaurants}