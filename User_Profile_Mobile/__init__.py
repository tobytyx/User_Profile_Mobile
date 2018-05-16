import pickle
with open("C:\\Users\\Toby's\\WorkSpace\\PyProjects\\User_Profile_Mobile\\User_Profile_Mobile\\users.pkl", mode="rb") as f:
    users = pickle.loads(f.read())
