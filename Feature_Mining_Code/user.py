# -*- coding: utf-8 -*-
from .user_feature_extraction import UserFeatureExtraction
from .basic_feature_extraction import BasicFeatureExtraction
from .user_profiling import UserProfile
import os
import json
import pickle


class User(object):
    def __init__(self, name):
        self.name = name
        self.basic_feature_extraction = None
        self.user_feature_extraction = None
        self.user_profile = None
        self.profile = None

    def set_basic_feature_extraction(self):
        if self.basic_feature_extraction is None:
            self.basic_feature_extraction = BasicFeatureExtraction(user=self.name)

    def set_user_feature_extraction(self, level_std):
        if self.user_feature_extraction is None and self.basic_feature_extraction is not None:
            self.user_feature_extraction = UserFeatureExtraction(
                basic_feature=self.basic_feature_extraction,
                level_std=level_std
            )

    def set_user_profile(self, price_level, estate_price):
        if self.user_profile is None and self.user_feature_extraction is not None:
            self.user_profile = UserProfile(
                user_feature=self.user_feature_extraction,
                price_level=price_level,
                estate_price=estate_price
            )
            self.profile = {
                "home_area": self.user_profile.home_area,
                "work_area": self.user_profile.work_area,
                "ent_area": self.user_profile.ent_area,
                "income_level": self.user_profile.income_level,
                "work_prefer": self.user_profile.work_prefer,
                "ent_way": self.user_profile.ent_way,
                "trip_distance": self.user_profile.trip_distance,
                "trip_duration": self.user_profile.trip_duration,
                "trip_mode": self.user_profile.trip_mode
            }

    def get_profile(self):
        return self.profile

    def show_profile(self):
        if self.profile is None:
            print("No profile!")
            return
        # 家
        if "name" in self.profile["home_area"]:
            print("住址:\n\t%s" % (
                self.profile["home_area"]["city"] +
                self.profile["home_area"]["district"] +
                self.profile["home_area"]["name"]
            ))
        elif "lat" in self.profile["home_area"]:
            print("住址:\n\t%f,%f" % (self.profile["home_area"]["lat"], self.profile["home_area"]["lng"]))
        # 工作地
        if "name" in self.profile["work_area"]:
            print("工作地:\n\t%s" % (
                self.profile["work_area"]["city"] +
                self.profile["work_area"]["district"] +
                self.profile["work_area"]["name"]
            ))
        elif "lat" in self.profile["work_area"]:
            print("工作地: %f,%f" % (self.profile["work_area"]["lat"], self.profile["work_area"]["lng"]))
        # 娱乐地
        print("娱乐地:")
        for place in self.profile["ent_area"]:
            if "name" in place:
                print("\t%s" % (
                    place["city"] +
                    place["district"] +
                    place["name"]
                ))
            elif "lat" in place:
                print("\t%f,%f" % (place["lat"], place["lng"]))
        print("娱乐方式: %s" % self.profile["ent_way"])
        print("收入水平: %s" % self.profile["income_level"])
        print("工作偏好: %s" % self.profile["work_prefer"])
        print("出行偏好:")
        print("\t路程: %s\n\t时间: %s\n\t方式: %s" % (
            self.profile["trip_distance"],
            self.profile["trip_duration"],
            self.profile["trip_mode"]
        ))

    def save_profile(self, file_dir):
        if not os.path.exists(file_dir):
            os.mkdir(file_dir)
        with open(os.path.join(file_dir, "%sprofile.json" % self.name), mode="w", encoding="utf-8") as f:
            f.write(json.dumps(self.profile, ensure_ascii=False, indent=2))

    def load_user_feature(self, feature_dir):
        with open(os.path.join(feature_dir, self.name), mode="rb") as f:
            self.user_feature_extraction = pickle.loads(f.read())

    def load_basic_feature(self, basic_feature_dir):
        with open(os.path.join(basic_feature_dir, self.name), mode="rb") as f:
            self.basic_feature_extraction = pickle.loads(f.read())
