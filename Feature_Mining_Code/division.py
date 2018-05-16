# -*- coding: utf-8 -*-

import json
import os
import datetime
from .tools import get_distance
from .config import opt


class TrajDivision(object):
    def __init__(self):
        self.s_max = opt.s_max
        self.t_min = opt.t_min
        self.t_max = opt.t_max
        self.base_dir = opt.clean_data_dir  # 原数据所在地
        self.des_dir = opt.division_data_dir  # 目标记录所在地
        if not os.path.exists(self.des_dir):
            os.mkdir(self.des_dir)

    def data_division(self, users="all"):
        if users == "all":
            users = [user_name[:3] for user_name in os.listdir(self.base_dir)]

        for user in users:
            trajectories = self.division_read(user=user)
            divisions = []
            residents = []  # 驻留段的集合
            seq_buff = []  # Seq缓冲区，存的是序号

            # 找出驻留段集合
            for i in range(len(trajectories)):
                if len(seq_buff) == 0:
                    seq_buff.append(i)
                    continue
                r_time = datetime.datetime.strptime(trajectories[i][3],
                                                    "%Y-%m-%d %H:%M:%S")
                r_lat = trajectories[i][1]
                r_lng = trajectories[i][2]
                # r_mode = trajectories[i][4]
                # 判断该记录与seq_buff里的所有记录中是否存在距离超出阈值的情况
                key = 1
                for buff in seq_buff:
                    if get_distance(
                            lat1=trajectories[buff][1],
                            lng1=trajectories[buff][2],
                            lat2=r_lat,
                            lng2=r_lng) > self.s_max:
                        key = -1
                        break

                # 没有超出阈值，加入seq_buff
                if key == 1:
                    seq_buff.append(i)

                # 距离超出了阈值
                else:  # 比较Tmin
                    if r_time - datetime.datetime.strptime(
                            trajectories[seq_buff[0]][3],
                            "%Y-%m-%d %H:%M:%S") > self.t_min:
                        residents.append(seq_buff)  # 驻留数据
                        seq_buff = [i]
                    else:
                        seq_buff = []  # 某一行进路段的一个片段，释放

            # 找出出行段集合
            if len(residents) == 0:
                divisions.append({
                    "kind": "trip",
                    "seq": [j for j in range(len(trajectories))]
                })
            else:
                trips = []
                if residents[0][0] > 1:  # 开头就是出行段
                    trips.extend([j for j in range(residents[0][0])])
                for i in range(1, len(residents)):
                    if residents[i][0] - residents[i - 1][-1] > 1:  # 有出行段
                        trips.extend([
                            j for j in range(residents[i - 1][-1] + 1,
                                             residents[i][0])
                        ])
                if residents[-1][-1] + 1 < len(trajectories):  # 结尾还有出行段
                    trips.extend([
                        j for j in range(residents[-1][-1] + 1,
                                         len(trajectories))
                    ])

                res_length = 0
                for resident in residents:
                    # print(resident)
                    res_length += len(resident)
                # print("resident length: %d" % res_length)

                trip_buff = []
                # print("trips length: %d" % (len(trips)))

                for trip_record in trips:
                    if len(trip_buff) == 0:
                        trip_buff.append(trip_record)
                        continue
                    if datetime.datetime.strptime(
                            trajectories[trip_record][3],
                            "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(
                                trajectories[trip_buff[-1]][3],
                                "%Y-%m-%d %H:%M:%S") >= self.t_max:
                        divisions.append({"kind": "trip", "seq": trip_buff})
                        trip_buff = []
                    trip_buff.append(trip_record)
                if len(trip_buff) > 0:
                    divisions.append({"kind": "trip", "seq": trip_buff})
            for resident in residents:
                divisions.append({"kind": "resident", "seq": resident})
            divisions.sort(key=lambda x: x["seq"][0], reverse=False)
            self.division_write(
                divisions=divisions, trajectories=trajectories, user=user)

    #  分割模块统一写接口
    def division_write(self, divisions, trajectories, user):
        json_data = []
        for division in divisions:
            json_data.append({
                "kind":
                division["kind"],
                "records":
                trajectories[division["seq"][0]:division["seq"][-1] + 1]
            })
        with open(
                os.path.join(self.des_dir, "%s.division" % user),
                encoding="utf8",
                mode='w') as f:
            f.write(json.dumps(json_data))
        json_data.clear()

    #  分割模块统一读接口
    def division_read(self, user):
        with open(
                os.path.join(self.base_dir, "%s.data" % str(user)),
                encoding="utf8",
                mode='r') as f:
            clean_data = json.loads(s=f.read(), encoding="utf8")
        return clean_data["data"]
