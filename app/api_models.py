from flask_restx import fields
from .extensions import api
from .models import *

# Define the User model
user_model = api.model("User", {
    "user_id": fields.Integer,
    "city_id": fields.Integer,
    "email": fields.String,
    "password": fields.String,
    "first_name": fields.String,
    "last_name": fields.String,
    "isAdmin": fields.Boolean,
    "is_blocked": fields.Boolean
})

# Define the Restaurant model
restaurant_model = api.model("Restaurant", {
    "restaurant_id": fields.Integer,
    "city_id": fields.Integer,
    "name": fields.String,
    "address": fields.String,
    "phone": fields.String,
    "image_url": fields.String,
    "latitude": fields.Float,
    "longitude": fields.Float,
    "search_vector": fields.String,
    "city": fields.String,
    "categories": fields.List(fields.String(attribute="name")),  # Adjusted the field name to match the model
    "users": fields.List(fields.String(attribute="email"))  # Adjusted the field name to match the model
})

# Define the Visit model
visit_model = api.model("Visit", {
    "visit_id": fields.Integer,
    "user_id": fields.Integer,
    "restaurant_id": fields.Integer,
    "user": fields.String(attribute="email"),  # Adjusted the field name to match the model
    "restaurant": fields.String(attribute="name")  # Adjusted the field name to match the model
})

# Define the City model
city_model = api.model("City", {
    "city_id": fields.Integer,
    "name": fields.String,
    "updated_At": fields.DateTime
})

# Define the Category model
category_model = api.model("Category", {
    "category_id": fields.Integer,
    "name": fields.String
})

# Define the RestaurantCategory model
restaurant_category_model = api.model("RestaurantCategory", {
    "restcat_id": fields.Integer,
    "restaurant_id": fields.Integer,
    "category_id": fields.Integer
})

# Define the Image model
image_model = api.model("Image", {
    "image_id": fields.Integer,
    "visit_id": fields.Integer,
    "url": fields.String,
    "uploaded_At": fields.DateTime,
    "taken_At": fields.DateTime,
    "rating": fields.String,
    "visit": fields.String
})

# Define the Connection model
connection_model = api.model("Connection", {
    "connection_id": fields.Integer,
    "user_a_id": fields.Integer,
    "user_b_id": fields.Integer,
    "status": fields.String,
    "user_a": fields.String(attribute="email"),  # Adjusted the field name to match the model
    "user_b": fields.String(attribute="email")  # Adjusted the field name to match the model
})
