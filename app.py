from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import os
import cv2
import numpy as np
import face_recognition
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key'

db = SQLAlchemy(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    aadhar = db.Column(db.String(12), unique=True, nullable=False)
    mobile = db.Column(db.String(10), nullable=False)
    voted = db.Column(db.Boolean, default=False)
    face_encoding = db.Column(db.LargeBinary, nullable=False)

class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    candidate = db.Column(db.String(100), nullable=False)

class Candidate(db.Model):
    __tablename__ = 'candidates'
    id = db.Column(db.Integer, primary_key=True)
    candidate_name = db.Column(db.String(100), nullable=False)
    party_name = db.Column(db.String(100), nullable=False)
    party_logo = db.Column(db.String(100), nullable=False)

admin = Admin(app, name='Admin Panel', template_mode='bootstrap3')
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Vote, db.session))
admin.add_view(ModelView(Candidate, db.session))

@app.route('/')
def home():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        aadhar = request.form['aadhar'].strip()
        mobile = request.form['mobile'].strip()

        if not (name and aadhar.isdigit() and mobile.isdigit()):
            return "Invalid input. Name, Aadhar, and Mobile are required."

        video = cv2.VideoCapture(0)
        detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces_data = []

        while len(faces_data) < 5:
            ret, frame = video.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                face = frame[y:y+h, x:x+w]
                face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                encoding = face_recognition.face_encodings(face_rgb)
                if encoding:
                    faces_data.append(encoding[0])
                    cv2.putText(frame, f"Captured {len(faces_data)}", (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            cv2.imshow("Register Face - Press Q to Cancel", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video.release()
        cv2.destroyAllWindows()

        if len(faces_data) < 3:
            msg = "Face not detected properly. Try again."
            return render_template("final.html", msg=msg)

        average_encoding = np.mean(faces_data, axis=0)

        existing_users = User.query.all()
        for user in existing_users:
            stored = np.frombuffer(user.face_encoding, dtype=np.float64)
            distance = face_recognition.face_distance([stored], average_encoding)[0]
            if distance < 0.35:
                msg = f"Face already registered with Aadhaar: {user.aadhar}"
                return render_template("final.html", msg=msg)

        try:
            new_user = User(name=name, aadhar=aadhar, mobile=mobile, face_encoding=average_encoding.tobytes())
            db.session.add(new_user)
            db.session.commit()
            return render_template("success.html", aadhar=aadhar)
        except db.IntegrityError:
            db.session.rollback()
            msg = f"Aadhaar: {aadhar} already exists"
            return render_template("final.html", msg=msg)

    return render_template("register.html")

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if request.method == 'POST':
        aadhar = request.form['aadhar'].strip()
        if not aadhar.isdigit():
            return "Invalid Aadhar."

        user = User.query.filter_by(aadhar=aadhar).first()
        if not user:
            return "User not found."

        if user.voted:
            msg = "You have already voted"
            return render_template("final.html", msg=msg)

        known_encoding = np.frombuffer(user.face_encoding, dtype=np.float64)

        video = cv2.VideoCapture(0)
        detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        verified = False
        match_attempts = 0

        while match_attempts < 5:
            ret, frame = video.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                face = frame[y:y+h, x:x+w]
                face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                encoding = face_recognition.face_encodings(face_rgb)
                if encoding:
                    distance = face_recognition.face_distance([known_encoding], encoding[0])[0]
                    if distance < 0.35:
                        verified = True
                        break
                match_attempts += 1

            cv2.putText(frame, "Verifying...", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.imshow("Face Verification", frame)
            if cv2.waitKey(1) & 0xFF == ord('q') or verified:
                break

        video.release()
        cv2.destroyAllWindows()

        if verified:
            return render_template("verified.html", aadhar=aadhar)
        else:
            msg = "Face verification failed. Access denied."
            return render_template("final.html", msg=msg)

    return render_template("vote.html")

@app.route('/cast_vote/<aadhar>', methods=['GET', 'POST'])
def cast_vote(aadhar):
    if request.method == 'POST':
        candidate = request.form['candidate']
        user = User.query.filter_by(aadhar=aadhar).first()
        if user:
            user.voted = True
            new_vote = Vote(candidate=candidate)
            db.session.add(new_vote)
            db.session.commit()
            msg = "Vote casted successfully"
            return render_template("final.html", msg=msg)

    candidates = Candidate.query.all()
    return render_template("cast_vote.html", candidates=candidates, aadhar=aadhar)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET' and 'password' not in request.args:
        return "Enter password: <form method='GET'><input name='password'><button type='submit'>Submit</button></form>"
    if request.args.get('password') != 'secret123':
        return "Unauthorized", 403

    if request.method == 'POST' and 'add' in request.form:
        candidate_name = request.form['candidate_name']
        party_name = request.form['party_name']
        file = request.files['party_logo']
        if file and file.filename.endswith(('.png', '.jpeg', '.jpg')):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_candidate = Candidate(candidate_name=candidate_name, party_name=party_name, party_logo=filename)
            db.session.add(new_candidate)
            db.session.commit()

    if request.method == 'POST' and 'delete' in request.form:
        candidate_id = request.form['delete']
        candidate = Candidate.query.get(candidate_id)
        if candidate:
            db.session.delete(candidate)
            db.session.commit()

    candidates = db.session.query(Candidate, db.func.count(Vote.id).label('vote_count')).outerjoin(Vote, Candidate.candidate_name == Vote.candidate).group_by(Candidate).all()
    total_votes = Vote.query.count()

    return render_template('admin_panel.html', candidates=[{'id': c.Candidate.id, 'candidate_name': c.Candidate.candidate_name, 'party_name': c.Candidate.party_name, 'party_logo': c.Candidate.party_logo, 'vote_count': c.vote_count} for c in candidates], total_votes=total_votes)

@app.route('/admin/vote_data')
def vote_data():
    vote_counts = db.session.query(Candidate.candidate_name, db.func.count(Vote.id).label('vote_count')).outerjoin(Vote, Candidate.candidate_name == Vote.candidate).group_by(Candidate.candidate_name).all()
    data = {row.candidate_name: row.vote_count for row in vote_counts}
    return jsonify(data)

@app.route('/db_viewer', methods=['GET', 'POST'])
def db_viewer():
    if request.method == 'POST':
        if request.form.get('password') != 'ayushi23':
            return "Unauthorized", 403

        tables = {
            'users': User,
            'votes': Vote,
            'candidates': Candidate
        }

        table_data = {}
        for name, model in tables.items():
            try:
                rows = [row.__dict__ for row in model.query.all()]
                for row in rows:
                    row.pop('_sa_instance_state', None)
                columns = [column.name for column in model.__table__.columns]
                table_data[name] = {
                    'columns': columns,
                    'rows': rows
                }
            except Exception as e:
                table_data[name] = {
                    'error': f"Could not load table: {str(e)}"
                }

        return render_template('db_viewer.html', tables=table_data)

    return '''
        <form method="post">
            <input type="password" name="password" placeholder="Enter password">
            <button type="submit">View Database</button>
        </form>
    '''

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists("database.db"):
            db.create_all()
            if not Candidate.query.first():
                initial_candidates = [
                    Candidate(candidate_name="Ravi Kumar", party_name="Progressive Alliance", party_logo="progressive.png"),
                    Candidate(candidate_name="Sneha Shah", party_name="National Unity", party_logo="unity.png"),
                    Candidate(candidate_name="Arjun Mehta", party_name="Green Future", party_logo="green.png")
                ]
                db.session.bulk_save_objects(initial_candidates)
                db.session.commit()
    app.run(debug=True)
