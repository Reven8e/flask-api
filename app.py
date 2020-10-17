# © Flask api- Made by Yuval Simon. For bogan.cool

from flask import Flask, request, session, render_template, send_file, flash, redirect, url_for, json, jsonify
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
import requests

# configs
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api.db'
db = SQLAlchemy(app)
app.secret_key = "sup"
ADMIN_TOKEN = "admin123"


# classes
class auth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uname = db.Column(db.Text(12), unique=True, nullable=False)
    password = db.Column(db.Text(50), nullable=False)
    admin = db.Column(db.String, nullable=True)

    def __repr__(self):
        return f'| {self.uname}, Admin={self.admin}, id= {str(self.id)} |'


class storage(db.Model):
    Sid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    data = db.Column(db.LargeBinary)

    def __repr__(self):
        return f'{self.name} id= ' + str(self.Sid)


class recaptcha(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_token = db.Column(db.String(12), unique=True)
    session_token_status = db.Column(db.String)

    def __repr__(self):
        return f'{str(self.session_token)}'
        

# routes

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register/<string:reg_uname>/<string:reg_password>', methods=['POST', 'GET'])
def register(reg_uname, reg_password):

    if "s_uname" not in session and "s_password" not in session:

        try:

            new_user = auth(uname=reg_uname, password=reg_password, admin='False')
            db.session.add(new_user)
            db.session.commit()
            return "Registered as:" + reg_uname

        except:
            
            return 'Username already in use', 404

    elif "s_uname" in session and "s_password" in session:

        return 'You already logged in'


@app.route('/register/admin/<string:ad_uname>/<string:ad_password>/<string:ad_token>', methods=['POST', 'GET'])
def admin_register(ad_uname, ad_password, ad_token):

    if "s_uname" not in session and "s_password" not in session:
        if ad_token == ADMIN_TOKEN:

            try:

                new_admin_user = auth(uname=ad_uname, password=ad_password, admin='True')
                db.session.add(new_admin_user)
                db.session.commit()
                return "New Admin!\nRegistered as:" + ad_uname

            except:
                
                return 'Username already in use', 404

        elif ad_token != ADMIN_TOKEN:

            return 'Invalid reg token!'

    elif "s_uname" in session and "s_password" in session:

        return 'You already logged in'


@app.route('/login/<string:l_uname>/<string:l_password>', methods=['POST', 'GET'])
def login(l_uname, l_password):

    if "s_uname" not in session and "s_password" not in session:

        check_uname = auth.query.filter_by(uname=l_uname).first()
        check_password = auth.query.filter_by(password=l_password).first()

        if check_uname and check_password:

            session['s_uname'] = l_uname
            session['s_password'] = l_password
            status = 'logged in as ' + l_uname
            
        else:

            status = 'Username or password not found in our database'

    elif "s_uname" in session and "s_password" in session:

        status =  "Your already logged in."
    
    return (status)


@app.route('/login/admin/<string:ad_l_uname>/<string:ad_l_password>/<ad_token>', methods=['POST', 'GET'])
def admin_login(ad_l_uname, ad_l_password, ad_token):

    if "admin_session_uname" not in session and "admin_session_password" not in session:

        check_uname = auth.query.filter_by(uname=ad_l_uname).first()
        check_password = auth.query.filter_by(password=ad_l_password).first()

        if check_uname and check_password:

            session["admin_session_uname"] = ad_l_uname
            session["admin_session_password"] = ad_l_password
            status = 'logged in as ' + ad_l_uname
            
        else:

            status = 'Username or password not found in our database'

    elif "admin_session_uname" in session and "admin_session_password" in session:

        status =  "Your already logged in."
    
    return (status)


@app.route('/logout', methods=['POST', 'GET'])
def logout():

    if "s_uname" in session and "s_password" in session:

        session.pop("s_uname", None)
        session.pop("s_password", None)
        return "You logged out."

    elif 'admin_session_uname' in session and 'admin_session_password' in session:

        session.pop('admin_session_uname', None)
        session.pop('admin_session_password', None)
        return "Your logged out."

    elif "s_uname" not in session and "s_password" not in session:

        return "You are not logged in"

    elif 'admin_session_uname' not in session and 'admin_session_password' not in session:

        return "Your are not logged in"


@app.route('/users/delete/<int:id>', methods=['POST', 'GET'])
def delete_user(id):

    if "admin_session_uname" not in session and "admin_session_password" not in session:

        return "You need to be admin and to login to delete users."
    
    if "admin_session_uname" in session and "admin_session_password" in session:
        
        try:

            delete_user = auth.query.get_or_404(id)
            db.session.delete(delete_user)
            db.session.commit()
        except:

            return 'User not found', 404

        return 'deleted user ' + str(id)


@app.route('/users/all')
def all_users():
    return f"{auth.query.all()}"


@app.route("/upload/", methods=['POST', 'GET'])
def upload():

    if "s_uname" or 'admin_session_uname' in session and "s_password" or 'admin_session_uname' in session:

        if request.method == "POST":

            if 'file' not in request.files:

                return 'No file part'
            
            file = request.files.get('file')

            if file.filename == '':

                return 'No file has been chosen.'

            else:

                new_file = storage(name=file.filename, data=file.read())
                db.session.add(new_file)
                db.session.commit()
                return('done!')

        return render_template('upload.html')

    elif "s_uname" or 'admin_session_uname' not in session and "s_password" or 'admin_session_uname' not in session:

        return 'You are not logged in, please login to upload files to our db'



@app.route("/uploads/download/<int:Sid>", methods=['GET', 'POST'])
def download(Sid):

    if "s_uname" or 'admin_session_uname' in session and "s_password" or 'admin_session_uname' in session:

        try:
            
            Storage = storage().query.filter_by(Sid=Sid).first()
            return send_file (BytesIO(Storage.data), mimetype='image/jpg', as_attachment=True, attachment_filename=Storage.name)

        except:
            return 'File not found', 404

    elif "s_uname" or 'admin_session_uname' not in session and "s_password" or 'admin_session_uname' not in session:

        return 'You are not logged in, please login to upload files to our db'


@app.route("/uploads/show/<int:Sid>", methods=['GET', 'POST'])
def show(Sid):
    if "s_uname" or 'admin_session_uname' in session and "s_password" or 'admin_session_uname' in session:

        try:
            
            Storage = storage().query.filter_by(Sid=Sid).first()
            return send_file (BytesIO(Storage.data), attachment_filename=Storage.name)

        except:
            return 'File not found', 404
    
    elif "s_uname" or 'admin_session_uname' not in session and "s_password" or 'admin_session_uname' not in session:

        return 'You are not logged in, please login to upload files to our db'


@app.route('/uploads/delete/<int:d_Sid>', methods=['POST', 'GET'])
def delete_upload(d_Sid):

    if 'admin_session_uname' in session and 'admin_session_password' in session:

        try:

            delete_upload = storage.query.get_or_404(d_Sid)
            db.session.delete(delete_upload)
            db.session.commit()
            db.session.commit()
            return 'deleted upload ' + str(d_Sid)
        
        except:

            return 'file not found', 404

    elif 'admin_session_uname' not in session and 'admin_session_password' not in session:

       return "You need to be an admin and to login to delete uploads from the db."


@app.route('/uploads/all')
def all_uploads():
    if "s_uname" or 'admin_session_uname' in session and "s_password" or 'admin_session_uname' in session:

        return f"{storage.query.all()}"
    
    elif "s_uname" or 'admin_session_uname' not in session and "s_password" or 'admin_session_uname' not in session:

        return "You need to login to see the uploads"



# Reaptcha


def is_human(captcha_response):
    """ Validating recaptcha response from google server
        Returns True captcha test passed for submitted form else returns False.
    """
    secret = "6LejatIZAAAAAOLtcBHyIAcDeE36fnQZmmo_bV7B"
    payload = {'response':captcha_response, 'secret':secret}
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", payload)
    response_text = json.loads(response.text)
    return response_text['success']


@app.route('/recaptcha/verify/<string:token>', methods=['GET', 'POST'])
def captcha(token):

    sitekey = "6LejatIZAAAAAJ9TCQrLDS_flYHEknmnNFHqfcpM"
    token_checker = recaptcha.query.all()

    try:

        if request.method == "POST":

            captcha_response = request.form['g-recaptcha-response']

            if is_human(captcha_response):
                
                status = "Verification successful. You may now close this window."
                new_session_token = recaptcha(session_token=token, session_token_status = 'Successed')
                db.session.add(new_session_token)
                db.session.commit()
                
            else:

                status = "Sorry! Please Check Im not a robot again."

            flash(status)

    except:
        flash ('This token in not valid or has already been used, please request new token.')

    return render_template("captcha.html", sitekey=sitekey)


@app.route('/api/recaptcha/check/<string:token>', methods=['GET', 'POST'])
def protected(token):

    find_token = recaptcha.query.filter_by(session_token=token).first()
    if find_token:
        status = 'Verfication successed'
    else:
        status = 'Verfication failed'
    
    return (status)



if __name__ == "__main__":
    app.run(debug=True)
