# -*- coding: utf-8 -*-
import datetime
from .tools import get_distance, get_poi, clustering_points
from .config import opt
import pickle
import os


class UserFeatureExtraction(object):
    def __init__(self, basic_feature, level_std):
        self.level_std = level_std
        # *************用户的基本特征******************
        self.user = basic_feature.user
        self.d = opt.time_segment
        # 驻留点数据 & 出行数据
        self._weekday_trip_data_feature = basic_feature.weekday_trip_data_feature
        self._weekend_trip_data_feature = basic_feature.weekend_trip_data_feature

        # 驻留点特征
        # 把每个时段的驻留点聚类成一个点（暂定），该点就代表用户在这个时间段所在的位置，注意有的时间段数据为空
        self._frequent_weekday_segment_point = basic_feature.frequent_weekday_segment_point
        self._frequent_weekend_segment_point = basic_feature.frequent_weekend_segment_point

        # 出行特征
        # 工作日
        self._weekday_ave_distance = basic_feature.weekday_ave_distance
        self._weekday_ave_duration = basic_feature.weekday_ave_duration
        self._weekday_ave_trip_times = basic_feature.weekday_ave_trip_times
        self._weekday_trip_mode = basic_feature.weekday_trip_mode
        # 周末
        self._weekend_ave_distance = basic_feature.weekend_ave_distance
        self._weekend_ave_duration = basic_feature.weekend_ave_duration
        self._weekend_ave_trip_times = basic_feature.weekend_ave_trip_times
        self._weekend_trip_mode = basic_feature.weekend_trip_mode

        # *************用户属性特征***********************
        # {"lat","lng","province",city",district",street","name",tags","uid"}
        self.home_area = self.get_home_area()
        self.work_area = self.get_work_area()  # 返回格式同 home_area

        # ********出行习惯**********
        self.weekday_trip_distance_prefer = self.get_trip_distance("weekday")  # long/medium/short
        self.weekday_trip_duration_prefer = self.get_trip_duration("weekday")  # long/medium/short
        self.weekday_trip_mode_prefer = basic_feature.weekday_trip_mode[0]  # "walking", "riding", "transit", "driving"

        self.weekend_trip_distance_prefer = self.get_trip_distance("weekend")  # long/medium/short
        self.weekend_trip_duration_prefer = self.get_trip_duration("weekend")  # long/medium/short
        self.weekend_trip_mode_prefer = basic_feature.weekend_trip_mode[0]  # "walking", "riding", "transit", "driving"

        # ********娱乐习惯**********
        self.ent_area_prefer = self.get_ent_area_prefer()  # 返回格式为[weekday, weekend]
        self.ent_prefer = self.get_ent_prefer()  # 返回shopping, nature, home之一

        # ********工作习惯**********
        self.attendance_time, self.quitting_time = self.get_work_time()  # 返回的是datetime.time类型， 出行数据中得到

    def get_trip_distance(self, which_day):  # 求某一时间下的出行距离偏好 Long, medium, short？
        if which_day == "weekend":
            if self._weekend_ave_distance > self.level_std["weekend_distance_long"]:
                return "long"
            elif self._weekend_ave_distance < self.level_std["weekend_distance_short"]:
                return "short"
            return "medium"
        elif which_day == "weekday":
            if self._weekday_ave_distance > self.level_std["weekday_distance_long"]:
                return "long"
            elif self._weekday_ave_distance < self.level_std["weekday_distance_short"]:
                return "short"
            return "medium"
        return "medium"

    def get_trip_duration(self, which_day):  # 出行时间偏好
        if which_day == "weekend":
            if self._weekend_ave_duration > self.level_std["weekend_duration_long"]:
                return "long"
            elif self._weekend_ave_duration < self.level_std["weekend_duration_short"]:
                return "short"
            return "medium"
        elif which_day == "weekday":
            if self._weekday_ave_duration > self.level_std["weekday_duration_long"]:
                return "long"
            elif self._weekday_ave_duration < self.level_std["weekday_duration_short"]:
                return "short"
            return "medium"
        return "medium"

    def get_ent_prefer(self):  # 娱乐方式偏好
        std = {"shopping": 0, "home": 0, "nature": 0, "default": 0.5}
        for ent_area in self.ent_area_prefer:
            if "lat" in ent_area:
                if "lat" in self.home_area:
                    if get_distance(self.home_area["lat"], self.home_area["lng"], ent_area["lat"], ent_area["lng"]) < opt.near_limit:
                        std["home"] += 1
                if "tags" in ent_area:
                    for tag in ent_area["tags"]:
                        if ("购物" == tag) or ("美食" == tag):
                            std["shopping"] += 1
                        if "旅游景点" == tag:
                            std["nature"] += 1
        return max(std, key=std.get)

    def get_ent_area_prefer(self):  # 娱乐地点偏好：2个
        ent_tags = set(["美食", "购物", "旅游景点", "休闲娱乐", "运动健身", "自然地物", "文化传媒"])
        ent = []
        points = self._frequent_weekday_segment_point[int(self.d*0.75):int(self.d*0.9)]
        for trip in self._weekday_trip_data_feature:
            start_time = trip["start_time"].time()
            if 18 < start_time.hour < 20:
                points.append(trip["dest_loc"])
        point = clustering_points(points)
        if point == []:
            return {}
        lat1, lng1 = point
        weekday_pois, weekday_ent_address, business = get_poi(lat1, lng1)
        if weekday_pois is not None:
            name = business  # 娱乐地首选商圈，没有商圈再找POI点
            ent_poi_names = []
            ent_poi_tags = []
            for poi in weekday_pois:
                if len(ent_tags.intersection(poi["tags"])) > 0:
                    ent_poi_names.append(poi["name"])
                    ent_poi_tags.extend(poi["tags"])
            if name == "" and len(ent_poi_names) > 0:
                name = ent_poi_names[0]
            ent.append({
                "lat": lat1,
                "lng": lng1,
                "province": weekday_ent_address["province"],
                "city": weekday_ent_address["city"],
                "district": weekday_ent_address["district"] if len(weekday_ent_address["district"]) != 0 else weekday_ent_address["town"],
                "street": weekday_ent_address["street"],
                "name": name,  # 商圈名
                "tags": ent_poi_tags,  # poi tag的list
            })
        else:
            ent.append({"lat": lat1, "lng": lng1})

        points = self._frequent_weekend_segment_point[int(self.d*0.25):int(self.d*0.9)]
        for trip in self._weekend_trip_data_feature:
            start_time = trip["start_time"].time()
            if 6 < start_time.hour < 12:
                points.append(trip["origin_loc"])
            elif 18 < start_time.hour:
                points.append(trip["dest_loc"])
        point = clustering_points(points)
        if point == []:
            return {}
        lat2, lng2 = point
        weekend_pois, weekend_ent_address, business = get_poi(lat2, lng2)

        if weekend_pois is not None:
            name = business  # 娱乐地首选商圈，没有商圈再找POI点
            ent_poi_names = []
            ent_poi_tags = []
            for poi in weekend_pois:
                if len(ent_tags.intersection(poi["tags"])) > 0:
                    ent_poi_names.append(poi["name"])
                    ent_poi_tags.extend(poi["tags"])
            if name == "" and len(ent_poi_names) > 0:
                name = ent_poi_names[0]
            ent.append({
                "lat": lat1,
                "lng": lng1,
                "province": weekend_ent_address["province"],
                "city": weekend_ent_address["city"],
                "district": weekend_ent_address["district"] if len(weekend_ent_address["district"]) != 0 else weekend_ent_address["town"],
                "street": weekend_ent_address["street"],
                "name": name,
                "tags": ent_poi_tags,
            })
        else:
            ent.append({"lat": lat1, "lng": lng1})
        return ent

    def get_work_area(self):
        remove_tags = set(["宿舍", "住宅区"])
        points = self._frequent_weekday_segment_point[int(self.d/3):int(self.d*0.75)]
        for trip in self._weekday_trip_data_feature:
            start_time = trip["start_time"].time()
            if 6 < start_time.hour < 10:
                points.append(trip["dest_loc"])
            elif 16 < start_time.hour < 20:
                points.append(trip["origin_loc"])
        point = clustering_points(points)
        if point == []:
            return {}
        lat, lng = point
        work_pois, work_address, business = get_poi(lat, lng)

        if work_pois is not None:
            name = business
            work_poi_names = []
            work_poi_tags = []
            for poi in work_pois:
                if len(remove_tags.intersection(poi["tags"])) > 0:
                    work_poi_names.append(poi["name"])
                    work_poi_tags.extend(poi["tags"])
            if name == "" and len(work_poi_names) > 0:
                name = work_poi_names[0]
            return {
                "lat": lat,
                "lng": lng,
                "province": work_address["province"],
                "city": work_address["city"],
                "district": work_address["district"] if len(work_address["district"]) != 0 else work_address["town"],
                "street": work_address["street"],
                "name": name,
                "tags": work_poi_tags,
            }
        else:
            return {"lat": lat, "lng": lng}

    def get_home_area(self):  # 从驻留点矩阵找。0 ~ d*1/4
        home_tags = set(["教育培训", "酒店", "住宅区", "宿舍"])
        points = self._frequent_weekday_segment_point[:int(self.d/4)] + self._frequent_weekend_segment_point[:int(self.d/4)]
        points += self._frequent_weekday_segment_point[int(self.d*0.75):] + self._frequent_weekend_segment_point[:]
        for trip in self._weekday_trip_data_feature:
            start_time = trip["start_time"].time()
            if 6 < start_time.hour < 10:
                points.append(trip["origin_loc"])
            elif 18 < start_time.hour:
                points.append(trip["dest_loc"])

        for trip in self._weekend_trip_data_feature:
            start_time = trip["start_time"].time()
            if 6 < start_time.hour < 12:
                points.append(trip["origin_loc"])
            elif 18 < start_time.hour:
                points.append(trip["dest_loc"])

        point = clustering_points(points)
        if point == []:
            return {}
        lat, lng = point
        home_area, home_address, business = get_poi(lat, lng)
        if home_area is None:
            return {"lat": lat, "lng": lng}
        home_poi = None
        for poi in home_area:
            if "tags" not in poi:
                continue
            if len(home_tags.intersection(poi["tags"])) > 0:
                home_poi = poi
                break
        if home_poi is None:
            return {"lat": lat, "lng": lng}
        return {
            "lat": lat,
            "lng": lng,
            "province": home_address["province"],
            "city": home_address["city"],
            "district": home_address["district"] if len(home_address["district"]) != 0 else home_address["town"],
            "street": home_address["street"],
            "name": home_poi["name"],
            "tags": home_poi["tags"],
        }

    def get_work_time(self):  # 返回开始工作时间，结束工作时间，找出所有符合上班的轨迹，找到到达时间，取平均；同理
        attendance_time_list = []
        quit_time_list = []

        for trip in self._weekday_trip_data_feature:
            if opt.attendance_time_begin < trip["start_time"].time() < opt.attendance_time_end and True:
                attendance_time_list.append(trip["start_time"].time())
            if opt.quitting_time_begin < trip["start_time"].time() < opt.attendance_time_end and True:
                quit_time_list.append(trip["start_time"].time())

        avg_attendance_time = 0
        for attendance_time in attendance_time_list:
            avg_attendance_time += attendance_time.hour * 60 + attendance_time.minute
        attendant = datetime.time(hour=9, minute=0)
        if len(attendance_time_list) > 0:
            avg_attendance_time = avg_attendance_time / len(attendance_time_list)
            attendant = datetime.time(hour=int(avg_attendance_time // 60), minute=int(avg_attendance_time % 60))

        avg_quit_time = 0
        for quit_time in quit_time_list:
            avg_quit_time += quit_time.hour * 60 + quit_time.minute
        quits = datetime.time(hour=17, minute=0)
        if len(quit_time_list) > 0:
            avg_quit_time = avg_quit_time / len(quit_time_list)
            quits = datetime.time(hour=int(avg_quit_time // 60), minute=int(avg_quit_time % 60))
        return attendant, quits

    def save(self):
        if not os.path.exists(opt.features_dir):
            os.mkdir(opt.features_dir)
        with open(os.path.join(opt.features_dir, self.user), mode="wb") as f:
            f.write(pickle.dumps(self))
