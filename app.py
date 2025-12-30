import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib

# ---------------------------------
# PAGE CONFIG
# ---------------------------------
st.set_page_config(page_title="Student Management System", layout="centered")

# ---------------------------------
# FIREBASE INITIALIZATION (FIXED)
# ---------------------------------
if not firebase_admin._apps:
    try:
        firebase_key = dict(st.secrets["FIREBASE_KEY"])
        cred = credentials.Certificate(firebase_key)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error("❌ Firebase initialization failed")
        st.stop()

db = firestore.client()

# ---------------------------------
# HELPER FUNCTIONS
# ---------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------------------
# AUTH FUNCTIONS
# ---------------------------------
def create_default_staff():
    staff_ref = db.collection("users").document("staff@example.com")
    if not staff_ref.get().exists:
        staff_ref.set({
            "email": "staff@example.com",
            "password": hash_password("staff123"),
            "role": "staff",
            "name": "Admin Staff"
        })

def login_user(email, password):
    user_ref = db.collection("users").document(email)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return None

    user = user_doc.to_dict()
    if user["password"] == hash_password(password):
        return user
    return None

# ---------------------------------
# STUDENT FUNCTIONS
# ---------------------------------
def add_marks(student_email, student_name):
    st.subheader("➕ Add Semester Marks")

    semester = st.number_input("Semester Number", min_value=1, step=1)
    subjects = st.number_input("Number of Subjects", min_value=1, step=1)

    marks = []
    total = 0

    for i in range(subjects):
        m = st.number_input(f"Marks for Subject {i+1}", min_value=0.0, max_value=100.0)
        marks.append(m)
        total += m

    if st.button("Save Marks"):
        gpa = round((total / subjects) / 10, 2)

        db.collection("students").document(student_email).set({
            "email": student_email,
            "name": student_name,
            f"semester_{semester}": {
                "marks": marks,
                "gpa": gpa
            }
        }, merge=True)

        st.success(f"✅ Semester {semester} saved with GPA {gpa}")

def view_marks(student_email):
    st.subheader("📊 My Academic Record")

    doc = db.collection("students").document(student_email).get()
    if not doc.exists:
        st.info("No records found")
        return

    data = doc.to_dict()
    for key, value in data.items():
        if key.startswith("semester_"):
            st.write(key, value)

# ---------------------------------
# STAFF FUNCTIONS
# ---------------------------------
def add_student():
    st.subheader("👨‍🎓 Add New Student")

    name = st.text_input("Student Name")
    email = st.text_input("Student Email")
    password = st.text_input("Password", type="password")

    if st.button("Create Student"):
        db.collection("users").document(email).set({
            "email": email,
            "password": hash_password(password),
            "role": "student",
            "name": name
        })
        st.success("✅ Student account created")

def view_all_students():
    st.subheader("📋 All Students")

    students = db.collection("students").stream()
    for s in students:
        st.write(s.to_dict())

# ---------------------------------
# MAIN APP
# ---------------------------------
def main():
    create_default_staff()

    st.title("🎓 Student Management System")

    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(email, password)
            if user:
                st.session_state.user = user
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid email or password")

    else:
        user = st.session_state.user
        st.success(f"Logged in as {user['name']} ({user['role']})")

        if user["role"] == "student":
            add_marks(user["email"], user["name"])
            view_marks(user["email"])

        if user["role"] == "staff":
            add_student()
            view_all_students()

        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

# ---------------------------------
main()
