# -*- coding: utf-8 -*-

# 分为出行属性和驻留点属性
import datetime
import json
import os
import pickle
from .tools import clustering_points, get_possible_modes, get_distance
from .config import opt


# 每个用户都有一个实例
class BasicFeatureExtraction(object):
    def __init__(self, user, d=opt.time_segment):
        # 用户基本属性
        self.user = str(user)
        self.src_path = opt.division_data_dir
        self.d = int(d)
        # 驻留点数据 & 出行数据
        weekday_static_data, weekend_static_data, self.weekday_trip_data_feature, self.weekend_trip_data_feature = self.get_data()

        # 驻留点特征
        # 把每个时段的驻留点聚类成一个点（暂定），该点就代表用户在这个时间段所在的位置，注意有的时间段数据为空
        self.frequent_weekday_segment_point = [
            clustering_points(segment_points)
            for segment_points in weekday_static_data
        ]
        self.frequent_weekend_segment_point = [
            clustering_points(segment_points)
            for segment_points in weekend_static_data
        ]

        # 出行特征
        self.weekday_ave_distance = 0
        self.weekday_ave_duration = 0
        self.weekday_ave_trip_times = 0
        self.weekday_trip_mode = []  # 工作日最可能的出行方式

        self.weekend_ave_distance = 0
        self.weekend_ave_duration = 0
        self.weekend_ave_trip_times = 0
        self.weekend_trip_mode = []  # 周末最可能的出行方式

        self.total_trip_mining()

    # 驻留点部分返回划分了周末/工作日、时间段的格式化数据， 出行部分返回
    def get_data(self):
        with open(
                os.path.join(self.src_path, "%s.division" % self.user),
                mode="r",
                encoding="utf8") as f:
            division_data = json.loads(f.read(), encoding="utf8")
        raw_static_data = []
        raw_trip_data = []
        for each_data in division_data:
            if each_data["kind"] == "resident":
                raw_static_data.extend(each_data["records"])
            elif each_data["kind"] == "trip":
                raw_trip_data.append(each_data["records"])

        weekday_static_data = [[] for i in range(self.d)]  # 长度为每天拥有的时间段
        weekend_static_data = [[] for i in range(self.d)]  # 长度为每天拥有的时间段

        for static_data in raw_static_data:
            data_time = datetime.datetime.strptime(static_data[3],
                                                   "%Y-%m-%d %H:%M:%S")
            if data_time.weekday() < 5:  # 工作日
                i = int(
                    (data_time.hour + data_time.minute / 60) // 24 * self.d)
                weekday_static_data[i].append((static_data[1], static_data[2]))
            else:
                i = int(
                    (data_time.hour + data_time.minute / 60) // 24 * self.d)
                weekend_static_data[i].append((static_data[1], static_data[2]))

        weekday_trip_data = []
        weekend_trip_data = []
        for trip_data in raw_trip_data:
            data_time = datetime.datetime.strptime(trip_data[0][3],
                                                   "%Y-%m-%d %H:%M:%S")
            trip_data_with_feature = self.single_trip_mining(trip_data)
            if data_time.weekday() < 5:  # 工作日
                weekday_trip_data.append(trip_data_with_feature)
            else:
                weekend_trip_data.append(trip_data_with_feature)

        return weekday_static_data, weekend_static_data, weekday_trip_data, weekend_trip_data

    def single_trip_mining(self, trip_data):  # 单段轨迹的特征提取，并附加到数据后面。
        origin_loc = (trip_data[0][1], trip_data[0][2])
        dest_loc = (trip_data[-1][1], trip_data[-1][2])
        start_time = datetime.datetime.strptime(trip_data[0][3],
                                                "%Y-%m-%d %H:%M:%S")
        end_time = datetime.datetime.strptime(trip_data[-1][3],
                                              "%Y-%m-%d %H:%M:%S")
        total_duration = abs((end_time-start_time).total_seconds())
        total_distance = 0

        for i in range(1, len(trip_data)):
            total_distance += get_distance(
                                lat1=trip_data[i-1][2],
                                lng1=trip_data[i-1][1],
                                lat2=trip_data[i][2],
                                lng2=trip_data[i][1])
        if end_time == start_time:
            average_speed = 0
        else:
            average_speed = total_distance / total_duration
        return {
            "origin_loc": origin_loc,
            "dest_loc": dest_loc,
            "start_time": start_time,
            "end_time": end_time,
            "total_duration": total_duration,
            "total_distance": total_distance,
            "average_speed": average_speed
        }

    def total_trip_mining(self):
        # weekday
        total_distance = 0
        total_duration = 0
        total_times = 0
        mode_list = ["walking", "riding", "transit", "driving"]
        mode_scores = [10, 5, 2, 1]  # 打分机制 10 5 2 1
        trip_modes = {"walking": 0, "riding": 0, "transit": 0, "driving": 0}
        for trip in self.weekday_trip_data_feature:
            total_distance += trip["total_distance"]
            total_duration += trip["total_duration"]
            possible_modes = get_possible_modes(
                prob_dis=trip["total_distance"],
                prob_speed=trip["average_speed"])
            for i, possible_mode in enumerate(possible_modes):
                trip_modes[possible_mode] += mode_scores[i]
            total_times += 1
        self.weekday_ave_trip_times = total_times
        if total_times == 0:
            self.weekday_ave_distance = 0
            self.weekday_ave_duration = 0

        else:
            self.weekday_ave_distance = total_distance / total_times
            self.weekday_ave_duration = total_duration / total_times
        self.weekday_trip_mode.extend(
            sorted(mode_list, key=lambda x: trip_modes[x], reverse=True))

        # weekend
        total_distance = 0
        total_duration = 0
        total_times = 0
        trip_modes = {"walking": 0, "riding": 0, "transit": 0, "driving": 0}
        for trip in self.weekend_trip_data_feature:
            total_distance += trip["total_distance"]
            total_duration += trip["total_duration"]
            possible_modes = get_possible_modes(
                prob_dis=trip["total_distance"],
                prob_speed=trip["average_speed"])
            for i, possible_mode in enumerate(possible_modes):
                trip_modes[possible_mode] += mode_scores[i]
            total_times += 1
        if total_times == 0:
            self.weekend_ave_distance = 0
            self.weekend_ave_duration = 0
        else:
            self.weekend_ave_distance = total_distance / total_times
            self.weekend_ave_duration = total_duration / total_times
        self.weekend_ave_trip_times = total_times
        self.weekend_trip_mode.extend(
            sorted(mode_list, key=lambda x: trip_modes[x], reverse=True))

    def save(self):
        if not os.path.exists(opt.basic_feature_dir):
            os.mkdir(opt.basic_feature_dir)
        with open(os.path.join(opt.basic_feature_dir, self.user), mode="wb") as f:
            f.write(pickle.dumps(self))
