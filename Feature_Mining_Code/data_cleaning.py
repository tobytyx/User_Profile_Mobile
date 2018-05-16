# -*- coding: utf-8 -*-

import os
import json
import datetime
import time
import pandas as pd
from .config import opt
from .tools import cid2pos


class DataClean(object):
    def __init__(self):
        self.base_dir = opt.raw_data_dir  # 原数据所在地
        self.users = os.listdir(self.base_dir)
        self.sub_dir = opt.clean_data_sub_dir
        self.label_name = opt.clean_data_label
        self.des_dir = opt.clean_data_dir  # 目标记录所在地
        if not os.path.exists(self.des_dir):
            os.mkdir(self.des_dir)

# 把最原始的数据清洗、整理成json格式
# {"data":[ ["user_id", latitude, longitude, "datetime stamp", "mode"],[]]}
    def clean_gps_data(self):
        for user in self.users:
            current_dir = os.path.join(self.base_dir, user, self.sub_dir)
            trans_modes = []
            # 拥有出行方式的记录，若拥有，则将记录以字典列表的形式存入trans_mode中
            if os.path.exists(os.path.join(self.base_dir, user, self.label_name)):
                with open(
                        os.path.join(self.base_dir, user, self.label_name),
                        encoding="utf8",
                        mode="r") as f:
                    raw_data = f.readlines()[1:]
                    for line in raw_data:
                        line2 = line.strip().split('\t')
                        start_time = datetime.datetime.strptime(
                            line2[0], "%Y/%m/%d %H:%M:%S")
                        end_time = datetime.datetime.strptime(
                            line2[1], "%Y/%m/%d %H:%M:%S")
                        mode = line2[2]
                        trans_modes.append({
                            "start_time": start_time,
                            "end_time": end_time,
                            "mode": mode
                        })

            user_records = []
            for file_name in os.listdir(current_dir):
                with open(
                        os.path.join(current_dir, file_name), encoding="utf8",
                        mode='r') as f:
                    raw_data = f.readlines()[6:]
                    for line in raw_data:
                        line2 = line.strip().split(',')
                        longitude = float(line2[0])
                        latitude = float(line2[1])
                        record_time = datetime.datetime.strptime(
                            ' '.join(line2[-2:]),
                            "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=8)
                        # 确认出行的方式，缺省为"default"
                        record_mode = "default"
                        for trans_mode in trans_modes:
                            if (record_time >= trans_mode['start_time']) and (
                                    record_time <=
                                    trans_mode['end_time']):  # 在该段范围内
                                record_mode = trans_mode['mode']
                                break
                        user_records.append([
                            user, longitude, latitude,
                            record_time.strftime("%Y-%m-%d %H:%M:%S"),
                            record_mode
                        ])
            # 一个人的记录全部结束后再写入
            with open(
                    os.path.join(self.des_dir, "%s.data" % user),
                    encoding="utf8",
                    mode='w') as f:
                f.write(json.dumps({'data': user_records}))

# 分用户， 提取关键字段
    @classmethod
    def clean_dpi_data(cls):
        clean_data = {}
        raw_dpi = pd.read_csv(opt.raw_dpi_file, sep="|", encoding="utf-8")
        raw_dpi = raw_dpi[raw_dpi["imsi"].notnull & raw_dpi["url"].notnull & raw_dpi["cellid"].notnull]
        for index, row in raw_dpi.iterrows():
            imsi = row["imsi"]
            url = row["url"]
            cell_id = row["cellid"]
            r_time = time.localtime(float(row["time"]))
            r_time = time.strftime("%Y-%m-%d %H:%M:%S", r_time)
            lat, lng = cid2pos(cell_id)
            if imsi not in clean_data:
                clean_data[imsi] = []
            clean_data[imsi].append([imsi, lng, lat, r_time, url])
        for imsi, records in clean_data.items():
            with open(os.path.join(opt.clean_dpi_dir, imsi), mode="w", encoding="utf-8") as f:
                f.write(json.dumps({'data': records}))
