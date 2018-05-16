# -*- coding: utf-8 -*-
import re
import numpy as np
from urllib import request
from .config import opt
import json
from sklearn.cluster import AgglomerativeClustering, KMeans
import random


__all__ = ["get_distance", "get_possible_modes", "get_poi", "gaussian_distribute",
           "clustering_points", "use_baidu_api", "cid2pos", "search_url_location"]


def get_distance(lat1, lng1, lat2, lng2):
    return np.sqrt(((lat1 - lat2) * 111 * 1000)**2 + (
        (lng1 - lng2) * 85 * 1000)**2)


def get_possible_modes(prob_dis, prob_speed):
    # walking, riding, transit, driving
    kinds = ['walking', 'riding', 'transit', 'driving']
    score = [0, 0, 0, 0]
    # 最大速度，速度，距离
    # 速度： 0-3.5-6-12-16-18-^
    if prob_speed > 18:  # 只有汽车
        return ['driving']
    elif 16 < prob_speed < 18:
        score[3] += 1
        score[0] = -100
        score[1] = -100
    elif 12 < prob_speed < 16:
        score[2] += 1
        score[3] += 1
        score[0] = -100
        score[1] = -100
    elif 6 < prob_speed < 12:
        score[2] += 1
        score[3] += 1
        score[0] = -100
    elif 3.5 < prob_speed < 6:
        score[1] += 1
    else:  # <3.5
        score[0] += 1
    # 距离： 0-2000-6000-20000-^
    if prob_dis > 20000:
        return ['driving', 'transit']
    elif 6000 < prob_dis < 20000:
        score[2] += 2
        score[3] += 2
        score[0] = -100
    elif 2000 < prob_dis < 6000:
        score[1] += 2
    else:
        score[0] += 2
    ans = sorted(zip(kinds, score), key=lambda x: x[1], reverse=True)
    return [k[0] for k in ans if k[1] > 0]


def clustering_points(points):  # 对地理点进行聚类， points: list, (lat,lng)
    n_points = []
    for point in points:
        if len(point) > 0:
            n_points.append(point)
    if len(n_points) == 0:
        return []
    if len(n_points) < 2:
        return n_points[0]
    if len(n_points) > 10000:
        random.shuffle(n_points)
        n_points = n_points[:10000]

    num = int(len(n_points) / 10) + 1
    h_cluster = AgglomerativeClustering(n_clusters=num)
    h_cluster.fit(n_points)
    clusters = [[] for i in range(num)]
    for i, label in enumerate(h_cluster.labels_):
        clusters[label].append(n_points[i])
    clusters.sort(key=lambda x: len(x), reverse=True)
    kmeans = KMeans(n_clusters=1)
    kmeans.fit(clusters[0])
    return kmeans.cluster_centers_[0].tolist()


def use_baidu_api(raw_url, params=None, api_type="website"):
    parameters = []
    if api_type == "website":
        ak = "ak=%s" % opt.website_ak
    else:
        ak = "ak=%s" % opt.website_ak
    if params is not None:
        parameters.extend(params)
    parameters.append(ak)
    url = raw_url + "?" + "&".join(parameters)
    encodedStr = request.quote(url, safe="/:=&?#+!$,;'@()*[]")
    with request.urlopen(encodedStr) as f:
        data = json.loads(f.read().decode("utf-8"), encoding="utf-8")  # data是接收的原始数据，需要判断状态码等
    if data["status"] != 0:
        return None
    return data["result"]


def get_poi(lat, lng):  # 搜索具体经纬度点对应的POI语义，然后往poi_type方向去找
    raw_url = "http://api.map.baidu.com/geocoder/v2/"
    params = [
        "location=%f,%f" % (float(lat), float(lng)),
        "output=json",
        "radius=150",
        "pois=1",
        "latest_admin=1",
        "coordtype=wgs84ll"
    ]
    result = use_baidu_api(raw_url=raw_url, params=params, api_type="website")
    address = result["addressComponent"]
    business = result["business"].split(",")
    if len(business) > 0:
        business = business[0]
    else:
        business = ""
    pois = sorted(result["pois"], key=lambda x: x["distance"], reverse=False)
    return [{
        "name": poi["name"],
        "tags": poi["tag"].split(";")
    } for poi in pois], address, business


def cid2pos(cid):
    return 39.96372, 116.36765


def search_url_location(url):
    re_lat = '(lat|latitude)(={0,1})([0-9.]+|[%0-9A-Z]{4,16})'
    re_lng = '(lng|lon|longtitude)(={0,1})([0-9.]+|[%0-9A-Z]{4,16})'
    ans_lat = re.search(re_lat, url, flags=0)
    ans_lng = re.search(re_lng, url, flags=0)
    if ans_lat is not None and ans_lng:
        return {'lng': ans_lng.group(3), 'lat': ans_lat.group(3)}
    return None


def gaussian_distribute(values, limit=0.1):
    sort_values = sorted(values)
    length = len(sort_values)
    low_level = sort_values[int(length*limit)]
    high_level = sort_values[-int(length*limit)]
    return low_level, high_level
