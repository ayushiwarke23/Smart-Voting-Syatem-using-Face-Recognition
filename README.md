# Smart-Voting-Syatem-using-Face-Recognition
🗳️ Smart Voting System using Face Recognition &amp; Admin Dashboard This project is a Flask-based anonymous voting system where users can cast their vote securely. It includes an admin dashboard for managing candidates and tracking votes, along with a real-time bar graph to visualize voting results.  
Got it! Here's a clean and simple `README.md` file—perfect for GitHub, with no personal branding, portfolios, or extra fluff.



# ✅ Plain `README.md` for Smart Election Voting System

```markdown
# Smart Election Voting System using Face Recognition

A web-based voting system that uses face recognition for secure voter authentication and ensures that each person can vote only once. Built with Django, OpenCV, and a KNN classifier.



 Features

- Face recognition login for voters using webcam
- One vote per user – prevents duplicate voting
- Vote anonymously for candidates
- Admin panel to view votes (no names) and results as a graph
- Admin can manage candidates and users
- Simple, responsive UI



 Tech Stack

- Python
- Django
- OpenCV
- KNN (K-Nearest Neighbors) Classifier
- Chart.js (for vote graph)
- HTML/CSS (TailwindCSS used for styling)



 Project Structure

```
smart_voting/
├── voting_app/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
├── templates/
│   ├── cast_vote.html
│   ├── login.html
│   ├── admin_dashboard.html
│   └── ...
├── static/
│   ├── css/
│   ├── js/
│   └── ...
├── face_data/           # Collected face images
├── trained_model/       # Trained KNN model
├── train_model.py       # Script to train the model
├── collect_faces.py     # Script to collect faces
├── manage.py
└── db.sqlite3
```



 Setup Instructions

1. Clone the Repository
   ```bash
   git clone https://github.com/yourusername/smart-election-voting.git
   cd smart-election-voting
   ```

2. Create Virtual Environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. Install Requirements
   ```bash
   pip install -r requirements.txt
   ```

4. Run Migrations
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Create Superuser
   ```bash
   python manage.py createsuperuser
   ```

6. Run the Server
   ```bash
   python manage.py runserver
   ```



 How to Use

1. Collect Face Data
   ```bash
   python collect_faces.py
   ```

2. Train the Face Recognition Model
   ```bash
   python train_model.py
   ```

3. Start the Django Server
   ```bash
   python manage.py runserver
   ```

4. Voters: Log in using face recognition, then cast a vote.
5. Admin: Log in to view vote counts and the result graph (anonymous data).



 Admin Dashboard

- View total votes per candidate (no user details shown)
- Graph displayed using Chart.js
- Manage users and candidates



 To Do / Future Improvements

- Add email/OTP verification
- Use Dlib or deep learning model for better face recognition
- Store data in a remote database
- Add voter ID verification
- Deploy to cloud (Heroku, PythonAnywhere, etc.)



