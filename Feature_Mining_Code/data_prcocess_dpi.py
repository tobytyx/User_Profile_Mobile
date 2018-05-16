# -*- coding: utf-8 -*-
from .tools import get_distance, get_possible_modes, use_baidu_api
from .config import opt
from .public_classes import Path
import os
import sys
import datetime
import json


class DPIDivision(object):

    def __init__(self, user):
        self.re_lat = '(lat|latitude)(={0,1})([0-9.]+|[%0-9A-Z]{4,16})'
        self.re_lng = '(lng|lon|longtitude)(={0,1})([0-9.]+|[%0-9A-Z]{4,16})'
        self.user = user
        self.s_max = opt.s_max
        self.t_min = opt.t_min
        self.t_max = opt.t_max
        self.dpi_divisions = self.get_dpi_divisions()
        self.data_write()

    def get_dpi_divisions(self):
        divisions = self.divide_dpi(self.data_read())
        dpi_divisions = []
        for dpi_division in divisions:  # dpi_division: {"kind","seq"}
            if dpi_division["kind"] == "resident":
                dpi_divisions.append(dpi_division)
                continue
            # prob_time,预测时间，单位：s
            prob_time = dpi_division["seq"][-1][3] - dpi_division["seq"][0][3]
            # prob_dis,预测距离，单位：m
            prob_dis = 0
            for i in range(1, len(dpi_division["seq"])):
                prob_dis += get_distance(
                    lat1=dpi_division["seq"][i][2],
                    lng1=dpi_division["seq"][i][1],
                    lat2=dpi_division["seq"][i-1][2],
                    lng2=dpi_division["seq"][i-1][1]
                )
            # prob_speed,预测速度，单位：m/s
            prob_speed = prob_dis / prob_time
            # pro_mode,预测模式，类型为list
            prob_mode = get_possible_modes(prob_dis, prob_speed)
            # prob_paths,预测路径，为list，单元为Path
            prob_paths = self.gain_route(
                dpi_division["seq"][0][2],
                dpi_division["seq"][0][1],
                dpi_division["seq"][-1][2],
                dpi_division["seq"][0][1],
                prob_mode,
                dpi_division["seq"][0][3],
                dpi_division["seq"][-1][3]
            )
            # 利用精确位置和Cell_ID位置筛选路径，打分机制，分高的为预测路径
            # 每一个点在对应的时间与对应的经纬度的距离 和 分值成反相关
            # predict_path,从预测路径中选择一条最合适路径
            scores = [0 for i in range(len(prob_paths))]
            for i, path in enumerate(prob_paths):
                scores[i] = path.match_route(dpi_division["seq"])
            predict_path = prob_paths[scores.index(max(scores))]

            # 更新精确位置
            for i in range(len(dpi_division["seq"])):
                loc = predict_path.get_acc_location(dpi_division["seq"][i][3])
                dpi_division["seq"][i][1] = loc["lng"]
                dpi_division["seq"][i][2] = loc["lat"]
            dpi_divisions.append(dpi_division)
        return dpi_divisions

    def data_read(self):
        with open(os.path.join(opt.clean_dpi_dir, self.user), mode="r", encoding="utf-8") as f:
            records = json.loads(f.read())["data"]
        return records

    def data_write(self):
        with open(os.path.join(opt.division_data_dir, "%s.division" % self.user), mode="w", encoding="utf-8") as f:
            f.write(json.dumps(self.dpi_divisions))

    #  分段
    def divide_dpi(self, trajectories):
        divisions = []
        residents = []  # 驻留段的集合
        seq_buff = []  # Seq缓冲区，存的是序号

        # 找出驻留段集合
        for i in range(len(trajectories)):
            if len(seq_buff) == 0:
                seq_buff.append(i)
                continue
            r_time = datetime.datetime.strptime(trajectories[i][3], "%Y-%m-%d %H:%M:%S")
            r_lat = float(trajectories[i][1])
            r_lng = float(trajectories[i][2])
            # 判断该记录与seq_buff里的所有记录中是否存在距离超出阈值的情况
            key = 1
            for buff in seq_buff:
                if get_distance(lat1=trajectories[buff][1], lng1=trajectories[buff][2], lat2=r_lat, lng2=r_lng) > self.s_max:
                    key = -1
                    break
            # 没有超出阈值，加入seq_buff
            if key == 1:
                seq_buff.append(i)
            # 距离超出了阈值
            else:  # 比较Tmin
                if r_time - datetime.datetime.strptime(trajectories[seq_buff[0]][3], "%Y-%m-%d %H:%M:%S") > self.t_min:
                    residents.append(seq_buff)  # 驻留数据
                    seq_buff = [i]
                else:
                    seq_buff = []  # 某一行进路段的一个片段，释放

        # 找出出行段集合
        trips = []
        if len(residents) == 0:
            trips.append({
                "kind": "trip",
                "seq": [j for j in range(len(trajectories))]
            })
        else:
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
                    j for j in range(residents[-1][-1] + 1, len(trajectories))
                ])
            res_length = 0
            for resident in residents:
                res_length += len(resident)

            trip_buff = []
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
        return divisions

    # 返回Path数组
    def gain_route(self, o_lat, o_lng, d_lat, d_lng, modes, st_time, en_time):
        paths = []
        for mode in modes:
            raw_url = "http://api.map.baidu.com/direction/v1"
            params = [
                "origin=%f,%f" % (o_lat, o_lng),
                "destination=%f,%f" % (d_lat, d_lng),
                "mode=%s" % mode,
                "region=北京",
                "origin_region=北京",
                "destination_region=北京",
                "output=json"
            ]
            result = use_baidu_api(raw_url=raw_url, params=params, api_type="server")
            if result is None:
                return None
            for route in result['routes']:
                paths.append(Path(route=route, mode=mode, st_time=st_time, en_time=en_time))
        return paths
