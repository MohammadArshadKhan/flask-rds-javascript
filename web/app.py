
from flask import Flask, g, jsonify, request
from flask import  current_app as app
import sqlalchemy
from flask import render_template
import pickle
import datetime
from pandas._libs import json

app = Flask(__name__,template_folder='templates')
app.config.from_object('config')

print(app.config["SQLALCHEMY_DATABASE_URI"])

# getting the database
def connect_to_database():
    engine = sqlalchemy.create_engine(app.config["SQLALCHEMY_DATABASE_URI"])  # connect to server
    return engine
# to return the database
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db
# index page router to application
@app.route("/")
def index():
    return render_template('index.html')

# router to the station services
@app.route("/stations")
# @functools.lru_cache(maxsize=128)
def get_stations():
    engine = get_db()
    station = []
    rows = engine.execute("SELECT * from station;")
    for row in rows:
        station.append(dict(row))

    return jsonify(station=station)

# router to the occupancy status services
@app.route("/occupancy/<int:station_id>")
def get_occupancy(station_id):
    engine = get_db()
    data = []
    rows = engine.execute("SELECT * From Bike where number={} order by last_update limit 1;".format(station_id))
    for row in rows:
        data.append(dict(row))
    print(data)
    return jsonify(bikes_available=data)

# router to the chart data services
@app.route("/data/<int:station_id>")
def graph(station_id):
    engine = get_db()
    data = []
    rows = engine.execute("SELECT available_bikes, hour( last_update ) as hour FROM  Bike where number={}  group by hour( last_update ) asc;".format(station_id))
    #rows = engine.execute("SELECT available_bikes, dayname( last_update ) as day,hour( last_update ) as hour From Bike where number={} group by dayname( last_update ),hour( last_update );".format(station_id))
    for row in rows:
        data.append(dict(row))
    print(data)
    return jsonify(bikes_available=data)

# Load the trained ML pickel file
monday = pickle.load(open('./pickle/monday_station.pkl', 'rb'))
tuesday = pickle.load(open("./pickle/tuesday_station.pkl", "rb"))
wednesday = pickle.load(open("./pickle/wednesday_station.pkl", "rb"))
thursday = pickle.load(open("./pickle/thursday_station.pkl", "rb"))
friday = pickle.load(open("./pickle/friday_station.pkl", "rb"))
saturday = pickle.load(open("./pickle/saturday_station.pkl", "rb"))
sunday = pickle.load(open("./pickle/sunday_station.pkl", "rb"))

# router to the prediction service
@app.route("/prediction", methods=['GET', 'POST'])
def prediction_model():
    import numpy as np

    # Store the request from JS
    data = request.args.get('post', 0, type=str)
    data = data.split()
    main_temp = float(data[0])
    main_pressure = int(data[1])
    main_humidity = int(data[2])
    wind_speed = float(data[3])
    date = (data[4])
    d = datetime.datetime.strptime(date, "%Y-%m-%d")
    date = d.strftime("%A")
    minute = (data[5])
    station = int(data[6])
    d = datetime.datetime.strptime(minute, "%H:%M")
    hours = int(d.hour)
    minute = int(d.minute)

    print("Data to be sent to the prediction model ", data)
    print(type(data))
    prediction_input = [[station, main_temp, main_pressure, main_humidity, wind_speed, hours, minute]]
    if date == "Monday":
        x = monday.predict(prediction_input)
    elif date == "Tuesday":
        x = tuesday.predict(prediction_input)
    elif date == "Wednesday":
        x = wednesday.predict(prediction_input)
    elif date == "Thurday":
        x = thursday.predict(prediction_input)
    elif date == "Friday":
        x = friday.predict(prediction_input)
    elif date == "Saturday":
        x = saturday.predict(prediction_input)
    elif date == "Sunday":
        x = sunday.predict(prediction_input)

    print("Predicted available bikes for selected station is", int(x[0]))

    # Fetch the ML model output and return as JSON to client
    prediction = [int(x[0])]
    return json.dumps(prediction);

# Run Server
if __name__ == "__main__":
    app.run(debug=True)