import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import hashlib
import json

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Student Management System", layout="centered")

# -------------------- FIREBASE INIT --------------------
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(st.secrets["FIREBASE_KEY"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# -------------------- HELPERS --------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------- SESSION --------------------
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None

# -------------------- AUTH --------------------
def login():
    st.subheader("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        doc = db.collection("users").document(email).get()
        if doc.exists:
            data = doc.to_dict()
            if data["password"] == hash_password(password):
                st.session_state.user = email
                st.session_state.role = data["role"]
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Wrong password")
        else:
            st.error("User not found")

# -------------------- STUDENT --------------------
def student_dashboard():
    st.subheader("Student Dashboard")

    email = st.session_state.user
    student_ref = db.collection("students").document(email)
    student_doc = student_ref.get()

    if student_doc.exists:
        data = student_doc.to_dict()
        st.write("### CGPA:", data.get("cgpa", 0))

        for sem in data.get("semesters", []):
            st.write(f"**Semester {sem['semester']} | GPA: {sem['gpa']}**")
            for sub in sem["subjects"]:
                st.write(f"- {sub['name']}: {sub['marks']}")

    st.divider()
    st.write("### Add New Semester")

    subjects = st.number_input("Number of subjects", min_value=1, step=1)
    subject_data = []
    total = 0

    for i in range(subjects):
        name = st.text_input(f"Subject {i+1} Name", key=f"s{i}")
        marks = st.number_input(f"Marks for {name}", 0.0, 100.0, key=f"m{i}")
        subject_data.append({"name": name, "marks": marks})
        total += marks

    if st.button("Save Semester"):
        semesters = []
        if student_doc.exists:
            semesters = student_doc.to_dict().get("semesters", [])

        gpa = round((total / subjects) / 10, 2)
        semesters.append({
            "semester": len(semesters) + 1,
            "subjects": subject_data,
            "gpa": gpa
        })

        cgpa = round(sum(s["gpa"] for s in semesters) / len(semesters), 2)

        student_ref.set({
            "email": email,
            "semesters": semesters,
            "cgpa": cgpa
        })

        st.success("Semester saved successfully")
        st.rerun()

# -------------------- STAFF --------------------
def staff_dashboard():
    st.subheader("Staff Dashboard")

    st.write("### Add Student")
    name = st.text_input("Student Name")
    email = st.text_input("Student Email")
    password = st.text_input("Student Password", type="password")

    if st.button("Create Student"):
        db.collection("users").document(email).set({
            "email": email,
            "password": hash_password(password),
            "role": "student",
            "name": name
        })
        st.success("Student created")

    st.divider()
    st.write("### All Students")

    students = db.collection("students").stream()
    for s in students:
        d = s.to_dict()
        st.write(f"**{d['email']}** | CGPA: {d['cgpa']}")
        if st.button(f"Delete {d['email']}"):
            db.collection("students").document(d["email"]).delete()
            db.collection("users").document(d["email"]).delete()
            st.warning("Student deleted")
            st.rerun()

# -------------------- MAIN --------------------
st.title("🎓 Student Management System")

if st.session_state.user is None:
    login()
else:
    st.write(f"Logged in as **{st.session_state.role.upper()}**")
    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()

    if st.session_state.role == "student":
        student_dashboard()
    else:
        staff_dashboard()
