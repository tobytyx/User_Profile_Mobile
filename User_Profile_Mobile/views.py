from django.shortcuts import render
from User_Profile_Mobile import users


def helloworld(request):
    return render(request, 'helloworld.html')


def display(request):
    user_name = "020"
    if request.GET:
        user_name = request.GET["id"]
    params = {}
    if user_name in users:
        user = users[user_name]
        home = {}
        if "lat" in user["home_area"]:
            home["lat"] = user["home_area"]["lat"]
            home["lng"] = user["home_area"]["lng"]
        if "name" in user["home_area"]:
            home["name"] = user["home_area"]["city"] + user["home_area"]["district"] + user["home_area"]["street"] + user["home_area"]["name"]
        work = {}
        if "lat" in user["work_area"]:
            work["lat"] = user["work_area"]["lat"]
            work["lng"] = user["work_area"]["lng"]
        if "name" in user["work_area"]:
            work["name"] = user["work_area"]["city"] + user["work_area"]["district"] + user["work_area"]["street"] + user["work_area"]["name"]
        ent1 = {}
        if len(user["ent_area"]) > 0:
            if "lat" in user["ent_area"][0]:
                ent1["lat"] = user["ent_area"][0]["lat"]
                ent1["lng"] = user["ent_area"][0]["lng"]
            if "name" in user["ent_area"][0]:
                ent1["name"] = user["ent_area"][0]["city"] + user["ent_area"][0]["district"] + user["ent_area"][0]["street"] + user["ent_area"][0]["name"]
        ent2 = {}
        if len(user["ent_area"]) > 1:
            if "lat" in user["ent_area"][1]:
                ent2["lat"] = user["ent_area"][1]["lat"]
                ent2["lng"] = user["ent_area"][1]["lng"]
            if "name" in user["ent_area"][1]:
                ent2["name"] = user["ent_area"][1]["city"] + user["ent_area"][1]["district"] + user["ent_area"][1]["street"] + user["ent_area"][1]["name"]
        ent_way = user["ent_way"]
        work_prefer = user["work_prefer"]
        trip_distance = user["trip_distance"]
        trip_duration = user["trip_duration"]
        trip_mode = user["trip_mode"]
        params["home"] = home
        params["work"] = work
        params["ent1"] = ent1
        params["ent2"] = ent2
        params["ent_way"] = ent_way
        params["work_prefer"] = work_prefer
        params["trip_distance"] = trip_distance
        params["trip_duration"] = trip_duration
        params["trip_mode"] = trip_mode
    return render(request, "display.html", params)
