# -*- coding: utf-8 -*-
import datetime
import os


class Config(object):
    # path root
    project_root = r"/home/tanyx/WorkSpace/PyProjects/User_Profile_Mobile"
    data_root = r"/home/tanyx/dataDemo/User_Profile-Mobile"
    # path raw
    raw_data_dir = os.path.join(data_root, r"Geolife Trajectories 1.3/Data")
    raw_dpi_file = os.path.join(data_root, r"dpi/dpi.csv")
    # path clean
    clean_dpi_dir = os.path.join(data_root, r"clean_dpi")
    clean_data_dir = os.path.join(data_root, r"clean_Data")
    clean_data_sub_dir = r"Trajectory"
    clean_data_label = r"labels.txt"
    # path division
    division_data_dir = os.path.join(data_root, r"division_Data")
    # path basic features
    basic_feature_dir = os.path.join(data_root, r"basic_feature")
    # path user features
    features_dir = os.path.join(data_root, r"user_feature")
    # path profile
    profile_dir = os.path.join(data_root, r"profile")
    # path other
    house_price_filename = os.path.join(project_root, r"static/beijing.csv")

    # division
    s_max = 50
    t_min = datetime.timedelta(days=0, seconds=1800)
    t_max = datetime.timedelta(days=0, seconds=300)
    # time
    time_segment = 48
    quitting_late = datetime.time(hour=21, minute=0, microsecond=0)
    # 出行相关，可以通过分析所有用户的时间来判断
    distance_long = 1
    distance_short = 1
    duration_long = 1
    duration_short = 1
    attendance_time_begin = datetime.time(hour=7, minute=0, microsecond=0)
    attendance_time_end = datetime.time(hour=9, minute=0, microsecond=0)
    quitting_time_begin = datetime.time(hour=17, minute=0, microsecond=0)
    quitting_time_end = datetime.time(hour=23, minute=0, microsecond=0)
    near_limit = 200
    # 收入水平
    income_high_level = 1
    income_low_level = 1
    # ak
    website_ak = "pBnPWrgXOz3sSp5R4xinB9c6Z0wvQ6Ra"
    server_ak = "ulBi2onbWKQ5peVZBGts52eU6i7VdesZ"


opt = Config()
