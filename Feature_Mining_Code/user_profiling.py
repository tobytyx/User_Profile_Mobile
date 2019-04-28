# -*- coding: utf-8 -*-
from .tools import get_distance
from .config import opt
import datetime


class UserProfile(object):

    def __init__(self, user_feature, price_level, estate_price):
        # ********出行习惯**********
        self._weekday_trip_distance_prefer = user_feature.weekday_trip_distance_prefer  # long/medium/short
        self._weekday_trip_duration_prefer = user_feature.weekday_trip_duration_prefer  # long/medium/short
        self._weekday_trip_mode_prefer = user_feature.weekday_trip_mode_prefer  # "walking", "riding", "transit", "driving"
        self._weekend_trip_distance_prefer = user_feature.weekend_trip_distance_prefer  # long/medium/short
        self._weekend_trip_duration_prefer = user_feature.weekend_trip_duration_prefer  # long/medium/short
        self._weekend_trip_mode_prefer = user_feature.weekend_trip_mode_prefer  # "walking", "riding", "transit", "driving"
        # ********娱乐习惯**********
        self._ent_prefer = user_feature.ent_prefer  # 返回shopping, nature, home之一
        # ********工作习惯**********
        # 返回的是datetime.time类型， 出行数据中得到
        self._attendance_time, self._quitting_time = user_feature.attendance_time, user_feature.quitting_time

        # ************************  用户画像  *************************

        # ********主要活动地点**********
        self.home_area = user_feature.home_area
        self.work_area = user_feature.work_area
        self.ent_area = user_feature.ent_area_prefer

        # ********家庭收入水平**********
        self.income_level = "default"
        self.get_income_level(price_level, estate_price)

        # ********生活风格**********
        self.work_prefer = self.get_work_prefer()

        # ********娱乐方式偏好**********
        self.ent_way = self.get_ent_way()

        # ********出行偏好*********
        self.trip_distance = "default"
        self.trip_duration = "default"
        self.trip_mode = "default"
        self.get_commuting_status()

    def get_income_level(self, price_level, estate_price):
        if "name" in self.home_area:
            if "房地产" not in self.home_area["tags"]:
                return
            house_price = estate_price.name2price(self.home_area["name"])
            if house_price is None:
                return
            if house_price > price_level["high"]:
                self.income_level = "high"
            elif house_price < price_level["low"]:
                self.income_level = "low"
            else:
                self.income_level = "medium"

    def get_work_prefer(self):
        if "lat" in self.work_area and "lat" in self.home_area:
            if get_distance(self.work_area["lat"], self.work_area["lng"], self.home_area["lat"], self.home_area["lng"]) < opt.near_limit:
                return "home_based"
        if self._quitting_time > opt.quitting_late:
            return "workaholic"
        if (datetime.time(hour=8, minute=0, microsecond=0) < self._attendance_time < datetime.time(hour=9, minute=0, microsecond=0)
                and
                datetime.time(hour=17, minute=0, microsecond=0) < self._quitting_time < datetime.time(hour=18, minute=30, microsecond=0)):
            return "nine-to-five"
        return "default"

    def get_commuting_status(self):
        if self._weekday_trip_distance_prefer == "long" and self._weekend_trip_distance_prefer == "long":
            self.trip_distance = "long"
        elif self._weekday_trip_distance_prefer == "short" and self._weekend_trip_distance_prefer == "short":
            self.trip_distance = "short"
        else:
            self.trip_distance = "medium"

        if self._weekday_trip_duration_prefer == "long" and self._weekend_trip_duration_prefer == "long":
            self.trip_duration = "long"
        elif self._weekday_trip_duration_prefer == "short" and self._weekend_trip_duration_prefer == "short":
            self.trip_duration = "short"
        else:
            self.trip_duration = "medium"

        if self._weekday_trip_mode_prefer == self._weekend_trip_mode_prefer:
            self.trip_mode = self._weekend_trip_mode_prefer

    def get_ent_way(self):
        return self._ent_prefer
