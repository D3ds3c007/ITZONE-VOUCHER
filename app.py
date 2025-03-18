from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vouchers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
m3u_url = "https://bit.ly/itzonetv2"
m3u_url_unregistered = "https://bit.ly/unregistered"

#Voucher Model
class Voucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    expiration_date = db.Column(db.DateTime, nullable=False)


# Create Database
with app.app_context():
    db.create_all()

@app.route('/m3u', methods=['GET'])
def get_m3u_url():
    return jsonify({"m3uUrl": m3u_url}), 200

# get m3u url for unregistered users
@app.route('/m3u_unregistered', methods=['GET'])
def get_m3u_url_unregistered():
    return jsonify({"m3uUrl": m3u_url_unregistered}), 200

@app.route('/vouchers', methods=['POST'])
def create_voucher():
    data = request.json
    voucher_code = data.get("voucher")

    if not voucher_code:
        return jsonify({"message": "Voucher code is required"}), 400
    
    voucher = Voucher.query.filter_by(code=voucher_code).first()

    if not voucher:
        return jsonify({"message": "Invalid voucher code"}), 400
    
    if voucher.is_used:
        return jsonify({"message": "Voucher code has already been used"}), 400
    
    if voucher.expiration_date < datetime.now():
        return jsonify({"message": "Voucher code has expired"}), 400
    
    voucher.is_used = True
    db.session.commit()

    # return success response with the voucher details
    return jsonify({
        "code": voucher.code,
        "expiration_date": voucher.expiration_date.strftime("%Y-%m-%d"),
        "m3uUrl": m3u_url,
        "success": True
    }), 200

#generate voucher and make expiration date for 1 year
@app.route('/generate', methods=['GET'])
def generate_voucher():
    voucher_code =  ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    expiration_date = datetime.now() + timedelta(days=365)
    voucher = Voucher(code=voucher_code, expiration_date=expiration_date)
    db.session.add(voucher)
    db.session.commit()

    return jsonify({
        "code": voucher.code,
        "expiration_date": voucher.expiration_date
    }), 201

#generate voucher by specifying expiration date
@app.route('/generate', methods=['POST'])
def generate_voucher_with_expiration_date():
    data = request.json
    expiration_date = data.get("expiration_date")

    if not expiration_date:
        return jsonify({"message": "Expiration date is required"}), 400

    try:
        expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"message": "Invalid expiration date. Date format should be YYYY-MM-DD"}), 400

    voucher_code =  ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    voucher = Voucher(code=voucher_code, expiration_date=expiration_date)
    db.session.add(voucher)
    db.session.commit()

    return jsonify({
        "code": voucher.code,
        "expiration_date": voucher.expiration_date
    }), 201
#get all available vouchers
@app.route('/vouchers', methods=['GET'])
def get_vouchers():
    vouchers = Voucher.query.all()
    vouchers_data = []
    for voucher in vouchers:
        vouchers_data.append({
            "code": voucher.code,
            "expiration_date": voucher.expiration_date,
            "is_used": voucher.is_used
        })
    return jsonify(vouchers_data), 200

#route to delete all vouchers
@app.route('/vouchers', methods=['DELETE'])
def delete_vouchers():
    Voucher.query.delete()
    db.session.commit()
    return jsonify({"message": "All vouchers deleted"}), 200


if __name__ == '__main__':
    app.run(debug=True)
    