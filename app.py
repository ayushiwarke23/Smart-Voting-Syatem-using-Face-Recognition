from flask import Flask, render_template, request, redirect, url_for, jsonify  # Add jsonify
import sqlite3
import os
import cv2
import numpy as np
import face_recognition
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

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
            msg = "Face not detected properly try again"
            return render_template("final.html",msg=msg)

        average_encoding = np.mean(faces_data, axis=0)

        conn = get_db_connection()
        existing = conn.execute("SELECT aadhar, face_encoding FROM users").fetchall()
        for row in existing:
            stored = np.frombuffer(row['face_encoding'], dtype=np.float64)
            if face_recognition.compare_faces([stored], average_encoding)[0]:
                conn.close()
                msg = "Face already registered with Aadhaar: " + row['aadhar']
                return render_template("final.html",msg=msg)

        try:
            conn.execute("INSERT INTO users (name, aadhar, mobile, face_encoding) VALUES (?, ?, ?, ?)",
                         (name, aadhar, mobile, average_encoding.tobytes()))
            conn.commit()
            conn.close()
            return render_template("success.html", aadhar=aadhar)
        except sqlite3.IntegrityError:
            msg = "Aadhaar: " + row['aadhar'] +" Already exists"
            return render_template("final.html",msg=msg)


    return render_template("register.html")

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if request.method == 'POST':
        aadhar = request.form['aadhar'].strip()
        if not aadhar.isdigit():
            return "Invalid Aadhar."

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE aadhar = ?", (aadhar,)).fetchone()
        conn.close()

        if not user:
            return "User not found."

        if user["voted"]:
            msg = "You have already voted"
            return render_template("final.html",msg=msg)

        known_encoding = np.frombuffer(user["face_encoding"], dtype=np.float64)

        video = cv2.VideoCapture(0)
        detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        verified = False

        while True:
            ret, frame = video.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                face = frame[y:y+h, x:x+w]
                face_rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                encoding = face_recognition.face_encodings(face_rgb)
                if encoding:
                    result = face_recognition.compare_faces([known_encoding], encoding[0])
                    if result[0]:
                        verified = True
                        break

            cv2.putText(frame, "Verifying...", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
            cv2.imshow("Face Verification", frame)
            if cv2.waitKey(1) & 0xFF == ord('q') or verified:
                break

        video.release()
        cv2.destroyAllWindows()

        if verified:
            return render_template("verified.html", aadhar=aadhar)
        else:
            msg = "Face verification failed"
            return render_template("final.html",msg=msg)


    return render_template("vote.html")

# Update /cast_vote route in app.py
@app.route('/cast_vote/<aadhar>', methods=['GET', 'POST'])
def cast_vote(aadhar):
    conn = get_db_connection()
    if request.method == 'POST':
        candidate = request.form['candidate']
        conn.execute("UPDATE users SET voted = 1 WHERE aadhar = ?", (aadhar,))
        conn.execute("INSERT INTO votes (candidate) VALUES (?)", (candidate,))
        conn.commit()
        conn.close()
        msg = "Vote casted successfully"
        return render_template("final.html", msg=msg)

    candidates = conn.execute("SELECT candidate_name, party_name, party_logo FROM candidates").fetchall()
    conn.close()
    return render_template("cast_vote.html", candidates=candidates, aadhar=aadhar)
    
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET' and 'password' not in request.args:
        return "Enter password: <form method='GET'><input name='password'><button type='submit'>Submit</button></form>"
    if request.args.get('password') != 'secret123':
        return "Unauthorized", 403

    conn = get_db_connection()
    if request.method == 'POST' and 'add' in request.form:
        candidate_name = request.form['candidate_name']
        party_name = request.form['party_name']
        file = request.files['party_logo']
        if file and file.filename.endswith(('.png', '.jpeg', '.jpg')):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            conn.execute("INSERT INTO candidates (candidate_name, party_name, party_logo) VALUES (?, ?, ?)",
                         (candidate_name, party_name, filename))
            conn.commit()

    if request.method == 'POST' and 'delete' in request.form:
        candidate_id = request.form['delete']
        conn.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
        conn.commit()

    candidates = conn.execute("""
        SELECT c.id, c.candidate_name, c.party_name, c.party_logo, COUNT(v.id) as vote_count
        FROM candidates c
        LEFT JOIN votes v ON c.candidate_name = v.candidate
        GROUP BY c.id, c.candidate_name, c.party_name, c.party_logo
    """).fetchall()

    total_votes = conn.execute("SELECT COUNT(*) FROM votes").fetchone()[0]
    conn.close()

    return render_template('admin_panel.html', candidates=candidates, total_votes=total_votes)

@app.route('/admin/vote_data')
def vote_data():
    conn = get_db_connection()
    vote_counts = conn.execute("""
        SELECT c.candidate_name, COUNT(v.id) as vote_count
        FROM candidates c
        LEFT JOIN votes v ON c.candidate_name = v.candidate
        GROUP BY c.candidate_name
    """).fetchall()
    conn.close()

    data = {row['candidate_name']: row['vote_count'] for row in vote_counts}
    return jsonify(data)

if __name__ == '__main__':
    if not os.path.exists("database.db"):
        import db_setup
        db_setup.create_db()
    app.run(debug=True)
