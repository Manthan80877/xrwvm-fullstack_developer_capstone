from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import logout
from django.contrib import messages
from datetime import datetime
from .models import CarMake, CarModel
from .populate import initiate
import requests
from .restapis import backend_url
import requests
from .restapis import get_request, analyze_review_sentiments, post_review
from django.http import JsonResponse
from django.contrib.auth import login, authenticate
import logging
import json
from django.views.decorators.csrf import csrf_exempt
# from .populate import initiate


# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.

# Create a `login_request` view to handle sign in request
@csrf_exempt
def login_user(request):
    # Get username and password from request.POST dictionary
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    # Try to check if provide credential can be authenticated
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        # If user is valid, call login method to login current user
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)

def logout_request(request):
    logout(request)
    data = {"userName": ""}
    return JsonResponse(data)

@csrf_exempt
def registration(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data["userName"]

        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Already Registered"})

        user = User.objects.create_user(
            username=username,
            password=data["password"],
            first_name=data["firstName"],
            last_name=data["lastName"],
            email=data["email"]
        )

        login(request, user)
        return JsonResponse({"userName": username, "status": "Authenticated"})

    return JsonResponse({"error": "POST request required"}, status=405)

def get_dealerships(request, state="All"):
    if state == "All":
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/" + state

    dealerships = get_request(endpoint)
    return JsonResponse({"status": 200, "dealers": dealerships})

def get_dealer_reviews(request, dealer_id):
    reviews = get_request(f"/fetchReviews/dealer/{dealer_id}")

    if reviews:
        for review in reviews:
            review["sentiment"] = analyze_review_sentiments(
                review.get("review", "")
            )

    return JsonResponse({"status": 200, "reviews": reviews})

def get_dealer_details(request, dealer_id):
    dealer = get_request(f"/fetchDealer/{dealer_id}")
    return JsonResponse({"status": 200, "dealer": dealer})

@csrf_exempt
def add_review(request):
    if request.user.is_anonymous:
        return JsonResponse(
            {"status": 403, "message": "Unauthorized"},
            status=403
        )

    if request.method != "POST":
        return JsonResponse(
            {"status": 405, "message": "POST required"},
            status=405
        )

    try:
        data = json.loads(request.body)
        post_review(data)
        return JsonResponse({"status": 200})
    except Exception:
        return JsonResponse(
            {"status": 401, "message": "Error in posting review"},
            status=401
        )
def get_cars(request):
    count = CarMake.objects.count()
    print(count)

    if count == 0:
        initiate()

    car_models = CarModel.objects.select_related('car_make')
    cars = []

    for car_model in car_models:
        cars.append({
            "CarModel": car_model.name,
            "CarMake": car_model.car_make.name
        })

    return JsonResponse({"CarModels": cars})