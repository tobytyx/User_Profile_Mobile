# -*- coding: utf-8 -*-
from .config import opt
from .tools import get_distance
import re
from fuzzywuzzy import fuzz


class EstatePrice(object):
    def __init__(self):
        self.estates = {}
        with open(opt.house_price_filename, mode="r", encoding="utf-8") as f:
            f.readline()  # header
            for line in f:
                line = line.strip().split("|")
                name = line[0].strip()  # 小区名
                b_type = line[1].strip()  # 类型
                city = line[2].strip()  # 城市
                urban_area = line[3].strip()  # 城区
                business_area = line[4].strip()  # 商圈
                address = line[5]  # 地址
                era = int(re.match("[0-9]*", line[6]).group(0))  # 年代
                avg_price = int(re.match("[0-9]*", line[7]).group(0))  # 均价
                c_time = line[8]  # 采集时间
                url = line[9]  # 链接
                if name in self.estates:
                    # print("Wrong")
                    continue
                self.estates[name] = {
                    "b_type": b_type,
                    "city": city,
                    "urban_area": urban_area,
                    "business_area": business_area,
                    "era": era,
                    "address": address,
                    "avg_price": avg_price,
                    "c_time": c_time,
                    "url": url,
                }

    def name2address(self, name):
        name = self.clean_name(name)
        if name not in self.estates:
            return None
        return self.estates[name]["address"]

    def name2price(self, name):
        name = self.clean_name(name)
        cell_name = self.match(name)
        if cell_name is None:
            return None
        return self.estates[cell_name]["avg_price"]

    def clean_name(self, name):
        re.sub(r"[-\s]", "", name)
        return name.upper()

    def match(self, name):
        for e_name, value in self.estates.items():
            if fuzz.partial_ratio(self.clean_name(e_name), name) > 60:
                return e_name
            if fuzz.partial_ratio(self.clean_name(value["address"]), name) > 60:
                return e_name
        return None


# 路径，包含路径整体参数和Step的list
class Path(object):
    # time单位为秒
    def __init__(self, route, mode, st_time, en_time):
        self.status = 0
        self.steps = []
        self.start_time = st_time
        self.end_time = en_time
        self.mode = mode
        self.total_time = 0  # 路径给定的总时间
        self.step_total_time = 0  # step的时间之和
        self.distance = 0
        self.origin = {}
        self.destination = {}
        try:
            if mode == 'transit':
                self.total_time = route['scheme'][0]['duration']
                self.distance = route['scheme'][0]['distance']
                self.origin = route['scheme'][0]['originLocation']
                self.destination = route['scheme'][0]['destinationLocation']
                for step in route['scheme'][0]['steps']:  # 这里的step还需要研究
                    self.steps.append(Step(step, self.mode))
            else:
                self.total_time = route['duration']
                self.distance = route['distance']
                self.origin = route['originLocation']
                self.destination = route['destinationLocation']
                for step in route['steps']:
                    self.steps.append(Step(step, self.mode))
            for step in self.steps:
                self.step_total_time += step.total_time
        except Exception:
            self.status = -1

    # 提取时间，用对应时间的位置来进行比较，精确位置阈值为100m，模糊位置阈值为300m。
    def match_route(self, seq):
        score = 0
        for record in seq:
            cur_dis = self.get_acc_location(seq[3])
            if cur_dis is None:
                continue
            if get_distance(cur_dis["lat"], cur_dis["lng"], record[2], record[1]) < 300:
                score += 1
        return score

    def show_path(self):
        if self.status == 0:
            print('Path: mode: %s, total_time: %d, distance: %s, origin: (%f,%f), dest: (%f,%f)'
                  % (self.mode, self.total_time, self.distance, self.origin['lat'], self.origin['lng'], self.destination['lat'], self.destination['lng']))
            print('steps: ')
            for step in self.steps:
                step.show_path()
        else:
            print('PathError')

    # timePer为时间百分比
    def get_acc_location(self, time_stamp):
        relative_time = time_stamp - self.start_time
        if time_stamp > self.end_time:
            return None

        for step in self.steps:
            # 在该段step中
            if step.total_time >= relative_time:
                tar_lat = step.origin['lat'] + (step.destination['lat'] - step.origin['lat']) * (relative_time / step.total_time)
                tar_lng = step.origin['lng'] + (step.destination['lng'] - step.origin['lng']) * (relative_time / step.total_time)
                return {'lat': tar_lat, 'lng': tar_lng, 'mode': step.mode}
            else:
                relative_time -= step.total_time
        return None


# 方式，耗时，距离，起点，终点
class Step(object):
    """docstring for Step"""

    def __init__(self, step, mode):
        self.mode = mode  # 'transit, driving, riding, walking'
        self.total_time = 0
        self.distance = 0
        self.origin = {}
        self.destination = {}
        self.status = 0
        try:
            if mode == 'transit':
                if step[0]['type'] == 3:
                    if step[0]['vehicle']['type'] == 1:  # 地铁、轻轨
                        self.mode = 'subway'
                    elif step[0]['vehicle']['type'] == 12:  # 机场快轨，出发
                        self.mode = 'airSubwayto'
                    elif step[0]['vehicle']['type'] == 13:  # 机场快轨，返回
                        self.mode = 'airSubwayback'
                if step[0]['type'] == 5:
                    self.mode = 'walking'
                self.total_time = step[0]['duration']
                self.distance = step[0]['distance']
                self.origin = step[0]['stepOriginLocation']
                self.destination = step[0]['stepDestinationLocation']
            else:
                self.total_time = step['duration']
                self.distance = step['distance']
                self.origin = step['stepOriginLocation']
                self.destination = step['stepDestinationLocation']
        except Exception as e:
            self.status = -1
            raise e

    def show_path(self):
        print('mode: %s, total_time: %d, distance: %s, origin: (%f,%f), dest: (%f,%f)'
              % (self.mode, self.total_time, self.distance, self.origin['lat'], self.origin['lng'], self.destination['lat'], self.destination['lng']))
