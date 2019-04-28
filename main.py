# -*- coding: utf-8 -*-
import sys
import Feature_Mining_Code
from Feature_Mining_Code.tools import gaussian_distribute
import argparse
from Feature_Mining_Code import opt
import pickle
import os
import json


def main():
    # 初始化
    print("initializing...")
    data_clean = Feature_Mining_Code.DataClean()
    data_division = Feature_Mining_Code.TrajDivision()
    estate_price = Feature_Mining_Code.EstatePrice()
    user_names = data_clean.users
    users = {}
    for user_name in user_names:
        users[user_name] = Feature_Mining_Code.User(name=user_name)

    if loading_pre == 0:
        print("data cleaning...")
        # 1、data_cleaning
        # 2、data_process_dpi / division
        data_clean.clean_gps_data()
        print("data dividing...")
        data_division.data_division(user_names)

    if loading_basic == 0:
        # 3、basic_feature_extraction
        print("basic feature extracting...")
        for user_name in user_names:
            users[user_name].set_basic_feature_extraction()
            users[user_name].basic_feature_extraction.save()
    else:
        print("loading basic feature...")
        for user_name in user_names:
            users[user_name].load_basic_feature(opt.basic_feature_dir)

    if loading_feature == 0:
        # 5、user_feature_extraction
        print("user feature extracting...")
        weekday_durations = []
        weekend_durations = []
        weekday_distances = []
        weekend_distances = []
        for user_name in user_names:
            weekday_distances.append(users[user_name].basic_feature_extraction.weekday_ave_distance)
            weekend_distances.append(users[user_name].basic_feature_extraction.weekend_ave_distance)
            weekday_durations.append(users[user_name].basic_feature_extraction.weekday_ave_duration)
            weekend_durations.append(users[user_name].basic_feature_extraction.weekend_ave_duration)

        # 4、从所有的数据段中提取duration_long/short, distance_long/short
        weekday_distance_short, weekday_distance_long = gaussian_distribute(weekday_distances)
        weekend_distance_short, weekend_distance_long = gaussian_distribute(weekend_distances)
        weekday_duration_short, weekday_duration_long = gaussian_distribute(weekday_durations)
        weekend_duration_short, weekend_duration_long = gaussian_distribute(weekend_durations)
        level_std = {
            "weekday_distance_short": weekday_distance_short,
            "weekday_distance_long": weekday_distance_long,
            "weekend_distance_short": weekend_distance_short,
            "weekend_distance_long": weekend_distance_long,
            "weekday_duration_short": weekday_duration_short,
            "weekday_duration_long": weekday_duration_long,
            "weekend_duration_short": weekend_duration_short,
            "weekend_duration_long": weekend_duration_long
        }
        for user_name in user_names:
            users[user_name].set_user_feature_extraction(level_std=level_std)
            users[user_name].user_feature_extraction.save()
    else:
        print("loading user feature...")
        for user_name in user_names:
            users[user_name].load_user_feature(feature_dir=opt.features_dir)

    # 6、从所有数据中根据房屋数据提取低收入、高收入分界线
    prices = []
    for user_name in user_names:
        home = users[user_name].user_feature_extraction.home_area
        if "name" in home:
            price = estate_price.name2price(home["name"])
            if price is not None:
                prices.append(price)
    low_level, high_level = gaussian_distribute(prices)
    price_level = {
        "high": high_level,
        "low": low_level
    }

    # 7、user_profile
    print("user profiling")
    for user_name in user_names:
        users[user_name].set_user_profile(price_level=price_level, estate_price=estate_price)
        users[user_name].save_profile(file_dir=opt.profile_dir)

    users_pkl = {}
    files = os.listdir(opt.profile_dir)
    for profile in files:
        with open(os.path.join(opt.profile_dir, profile), mode="r", encoding="utf-8") as f:
            users_pkl[profile[:3]] = json.loads(f.read())

    with open(opt.profile_pkl_path, mode="wb") as f:
        f.write(pickle.dumps(users_pkl))


if __name__ == "__main__":
    sys.path.append(opt.project_root)
    parser = argparse.ArgumentParser(description="choose to premake or not")
    parser.add_argument('-1', '--pre', type=int, help="1 for loading premake, 0 for not", default=1)
    parser.add_argument('-2', '--basic', type=int, help="1 for loading basic feature, 0 for not", default=1)
    parser.add_argument('-3', '--feature', type=int, help="1 for loading feature, 0 for not", default=1)
    args = parser.parse_args()
    loading_pre = args.pre
    loading_basic = args.basic
    loading_feature = args.feature
    main()
