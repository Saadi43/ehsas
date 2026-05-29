from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import json
import os

app = Flask(__name__)
app.secret_key = 'punjab_gov_secret_key'

# Database Configuration
database_url = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User database model
class User(db.Model):
    __tablename__ = 'users'
    cnic = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)

# Create tables if they do not exist
with app.app_context():
    try:
        db.create_all()
        # Seed users from users.json if database is empty
        if not User.query.first():
            if os.path.exists('users.json'):
                try:
                    with open('users.json', 'r') as f:
                        users_data = json.load(f)
                    for cnic, info in users_data.items():
                        db.session.add(User(cnic=cnic, name=info['name'], password=info['password']))
                    db.session.commit()
                    print("Successfully seeded database from users.json")
                except Exception as e:
                    print(f"Error seeding database from users.json: {e}")
            else:
                default_user = User(cnic="35202-1234567-1", name="Ahmed Khan", password="123")
                db.session.add(default_user)
                db.session.commit()
    except Exception as e:
        print(f"Error initializing SQLite database: {e}")

CATEGORY_META = {
    "education": {"title": "Education Schemes", "desc": "Scholarships, laptops, stipends and digital access for students."},
    "health": {"title": "Health Schemes", "desc": "Universal healthcare, insurance and welfare for every citizen."},
    "industrial": {"title": "Industrial Schemes", "desc": "Support for SMEs, workers, youth entrepreneurs and farmers."}
}

SCHEMES = [
    # ---------------- EDUCATION ----------------
    {
        "id": "cm-honhar-undergrad",
        "name": "CM Honhar Undergraduate Scholarship Program",
        "category": "education",
        "description": "Full undergraduate scholarship for talented students of Punjab from low-income families.",
        "link": "https://honhaarscholarship.punjabhec.gov.pk/",
        "fields": [
            {"key": "domicile", "label": "Domicile of Punjab?", "type": "select", "options": ["Yes", "No"]},
            {"key": "income", "label": "Monthly Family Income (PKR)", "type": "number"},
            {"key": "marks", "label": "HSSC / Equivalent Marks (%)", "type": "number"},
        ]
    },
    {
        "id": "honhar-phase-2",
        "name": "Honhar Scholarship Phase II",
        "category": "education",
        "description": "Continuation scholarship for meritorious students enrolled in public sector universities.",
        "link": "https://honhaarscholarship.punjabhec.gov.pk/",
        "fields": [
            {"key": "domicile", "label": "Domicile of Punjab?", "type": "select", "options": ["Yes", "No"]},
            {"key": "income", "label": "Monthly Family Income (PKR)", "type": "number"},
            {"key": "cgpa", "label": "Current CGPA (out of 4)", "type": "number"},
        ]
    },
    {
        "id": "merit-scholarship",
        "name": "Merit Based Scholarship Program",
        "category": "education",
        "description": "Awarded to top position holders in intermediate and graduate exams across Punjab.",
        "link": "https://pesrp.edu.pk/",
        "fields": [
            {"key": "domicile", "label": "Domicile of Punjab?", "type": "select", "options": ["Yes", "No"]},
            {"key": "marks", "label": "Marks Obtained (%)", "type": "number"},
        ]
    },
    {
        "id": "insaf-female-card",
        "name": "Insaf Female Education Card",
        "category": "education",
        "description": "Monthly stipend for female students from underdeveloped districts of Punjab.",
        "link": "https://www.pndpunjab.gov.pk/insaf_education_card",
        "fields": [
            {"key": "gender", "label": "Gender", "type": "select", "options": ["Female", "Male"]},
            {"key": "domicile", "label": "Domicile of Punjab?", "type": "select", "options": ["Yes", "No"]},
            {"key": "income", "label": "Monthly Family Income (PKR)", "type": "number"},
            {"key": "enrolled", "label": "Currently Enrolled in Govt. Institution?", "type": "select", "options": ["Yes", "No"]},
        ]
    },
    {
        "id": "cm-laptop-scheme",
        "name": "CM Punjab Laptop Scheme",
        "category": "education",
        "description": "Free laptops for high-achieving students in public sector universities and colleges.",
        "link": "https://pmyp.gov.pk/laptop-scheme/",
        "fields": [
            {"key": "domicile", "label": "Domicile of Punjab?", "type": "select", "options": ["Yes", "No"]},
            {"key": "cgpa", "label": "Current CGPA (out of 4)", "type": "number"},
            {"key": "institution", "label": "Institution Type", "type": "select", "options": ["Public", "Private"]},
        ]
    },
    {
        "id": "cm-free-wifi",
        "name": "CM Punjab Free Wi-Fi Program",
        "category": "education",
        "description": "Free public Wi-Fi access at universities, hospitals, parks and public spaces of Punjab.",
        "link": "https://pitb.gov.pk/free_wifi",
        "fields": [
            {"key": "domicile", "label": "Resident of Punjab?", "type": "select", "options": ["Yes", "No"]},
        ]
    },
    {
        "id": "cm-ebike",
        "name": "CM Punjab Free E-Bike Scheme",
        "category": "education",
        "description": "Free / subsidised electric bikes for students of higher education institutions in Punjab.",
        "link": "https://bok.punjab.gov.pk/ebike",
        "fields": [
            {"key": "domicile", "label": "Domicile of Punjab?", "type": "select", "options": ["Yes", "No"]},
            {"key": "student", "label": "Currently a student?", "type": "select", "options": ["Yes", "No"]},
            {"key": "age", "label": "Age", "type": "number"},
        ]
    },
    # ---------------- HEALTH ----------------
    {
        "id": "sehat-card",
        "name": "Sehat Sahulat Card",
        "category": "health",
        "description": "Free in-patient health treatment up to PKR 1 million per family per year.",
        "link": "https://www.pmhealthprogram.gov.pk/",
        "fields": [
            {"key": "domicile", "label": "Resident of Punjab?", "type": "select", "options": ["Yes", "No"]},
            {"key": "cnic_valid", "label": "Valid CNIC?", "type": "select", "options": ["Yes", "No"]},
        ]
    },
    {
        "id": "universal-health-insurance",
        "name": "Universal Health Insurance",
        "category": "health",
        "description": "Government-funded health insurance covering all citizens of Punjab.",
        "link": "https://pshealthpunjab.gov.pk/",
        "fields": [
            {"key": "domicile", "label": "Domicile of Punjab?", "type": "select", "options": ["Yes", "No"]},
        ]
    },
    {
        "id": "aaghosh-program",
        "name": "Aaghosh Program",
        "category": "health",
        "description": "Conditional cash transfer for pregnant & lactating mothers and children under two.",
        "link": "https://pshealthpunjab.gov.pk/aaghosh",
        "fields": [
            {"key": "gender", "label": "Gender", "type": "select", "options": ["Female", "Male"]},
            {"key": "status", "label": "Status", "type": "select", "options": ["Pregnant", "Lactating Mother", "None"]},
            {"key": "income", "label": "Monthly Family Income (PKR)", "type": "number"},
        ]
    },
    {
        "id": "deceased-transport",
        "name": "Deceased Transportation Service",
        "category": "health",
        "description": "Free transportation of deceased persons across Punjab via Rescue 1122 / health dept.",
        "link": "https://rescue.gov.pk/",
        "fields": [
            {"key": "domicile", "label": "Resident of Punjab?", "type": "select", "options": ["Yes", "No"]},
        ]
    },
    {
        "id": "suthra-punjab",
        "name": "Suthra Punjab Program",
        "category": "health",
        "description": "Province-wide cleanliness & sanitation initiative providing door-to-door waste collection.",
        "link": "https://lgcd.punjab.gov.pk/suthra_punjab",
        "fields": [
            {"key": "domicile", "label": "Resident of Punjab?", "type": "select", "options": ["Yes", "No"]},
        ]
    },
    {
        "id": "cm-cancer-treatment",
        "name": "CM Punjab Cancer Treatment Initiative",
        "category": "health",
        "description": "Free cancer screening, diagnosis and treatment at empanelled hospitals across Punjab.",
        "link": "https://pshealthpunjab.gov.pk/cancer-initiative",
        "fields": [
            {"key": "domicile", "label": "Domicile of Punjab?", "type": "select", "options": ["Yes", "No"]},
            {"key": "diagnosed", "label": "Diagnosed / Suspected Cancer?", "type": "select", "options": ["Yes", "No"]},
        ]
    },
    # ---------------- INDUSTRIAL ----------------
    {
        "id": "sme-developer",
        "name": "SME Developer Program",
        "category": "industrial",
        "description": "Capacity building, financing and market access for small & medium enterprises in Punjab.",
        "link": "https://smeda.org/",
        "fields": [
            {"key": "domicile", "label": "Business registered in Punjab?", "type": "select", "options": ["Yes", "No"]},
            {"key": "employees", "label": "Number of Employees", "type": "number"},
            {"key": "turnover", "label": "Annual Turnover (PKR Million)", "type": "number"},
        ]
    },
    {
        "id": "youth-entrepreneurship",
        "name": "Youth Entrepreneurship Scheme",
        "category": "industrial",
        "description": "Concessional loans to youth for setting up new businesses (PMYP / CM initiative).",
        "link": "https://pmyp.gov.pk/loan/",
        "fields": [
            {"key": "age", "label": "Age", "type": "number"},
            {"key": "domicile", "label": "Domicile of Punjab?", "type": "select", "options": ["Yes", "No"]},
            {"key": "loan", "label": "Loan Amount Required (PKR)", "type": "number"},
        ]
    },
    {
        "id": "labour-digital-services",
        "name": "Labour Department Digital Services",
        "category": "industrial",
        "description": "Online registration, social security, marriage grants and death grants for workers.",
        "link": "https://labour.punjab.gov.pk/",
        "fields": [
            {"key": "registered", "label": "Registered with Labour Dept.?", "type": "select", "options": ["Yes", "No"]},
            {"key": "domicile", "label": "Working in Punjab?", "type": "select", "options": ["Yes", "No"]},
        ]
    },
    {
        "id": "pwwf",
        "name": "Punjab Workers Welfare Fund Program",
        "category": "industrial",
        "description": "Education, housing, marriage grants and scholarships for registered industrial workers.",
        "link": "https://pwwb.punjab.gov.pk/",
        "fields": [
            {"key": "registered", "label": "Registered Industrial Worker?", "type": "select", "options": ["Yes", "No"]},
            {"key": "wage", "label": "Monthly Wage (PKR)", "type": "number"},
        ]
    },
    {
        "id": "hi-tech-mechanization",
        "name": "Hi-Tech Farm Mechanization Program",
        "category": "industrial",
        "description": "Subsidised tractors, harvesters and modern agri-machinery for Punjab farmers.",
        "link": "https://agripunjab.gov.pk/mechanization",
        "fields": [
            {"key": "domicile", "label": "Farmer in Punjab?", "type": "select", "options": ["Yes", "No"]},
            {"key": "land", "label": "Land Holding (Acres)", "type": "number"},
        ]
    }
]

def check_eligibility(scheme_id, data):
    reasons = []
    def get_int(key): return int(data.get(key, 0) or 0)
    def get_float(key): return float(data.get(key, 0) or 0)

    if scheme_id == "cm-honhar-undergrad":
        if data.get('domicile') != "Yes": reasons.append("Must hold Punjab domicile")
        if get_int('income') > 80000: reasons.append("Family income must be ≤ PKR 80,000/month")
        if get_int('marks') < 70: reasons.append("Required minimum 70% in HSSC")
    elif scheme_id == "honhar-phase-2":
        if data.get('domicile') != "Yes": reasons.append("Must hold Punjab domicile")
        if get_int('income') > 75000: reasons.append("Family income must be ≤ PKR 75,000/month")
        if get_float('cgpa') < 3.0: reasons.append("Minimum CGPA 3.0 required")
    elif scheme_id == "merit-scholarship":
        if data.get('domicile') != "Yes": reasons.append("Must hold Punjab domicile")
        if get_int('marks') < 80: reasons.append("Minimum 80% marks required for merit")
    elif scheme_id == "insaf-female-card":
        if data.get('gender') != "Female": reasons.append("Only female students eligible")
        if data.get('domicile') != "Yes": reasons.append("Must hold Punjab domicile")
        if get_int('income') > 50000: reasons.append("Family income must be ≤ PKR 50,000/month")
        if data.get('enrolled') != "Yes": reasons.append("Must be enrolled in a government institution")
    elif scheme_id == "cm-laptop-scheme":
        if data.get('domicile') != "Yes": reasons.append("Must hold Punjab domicile")
        if get_float('cgpa') < 3.0: reasons.append("Minimum CGPA 3.0 required")
        if data.get('institution') != "Public": reasons.append("Must be enrolled in a public institution")
    elif scheme_id == "cm-free-wifi":
        if data.get('domicile') != "Yes": reasons.append("Service available only to Punjab residents")
    elif scheme_id == "cm-ebike":
        if data.get('domicile') != "Yes": reasons.append("Must hold Punjab domicile")
        if data.get('student') != "Yes": reasons.append("Must be a registered student")
        age = get_int('age')
        if age < 18 or age > 35: reasons.append("Age must be between 18 and 35")
    elif scheme_id == "sehat-card":
        if data.get('domicile') != "Yes": reasons.append("Must be a resident of Punjab")
        if data.get('cnic_valid') != "Yes": reasons.append("A valid CNIC is required")
    elif scheme_id == "universal-health-insurance":
        if data.get('domicile') != "Yes": reasons.append("Must hold Punjab domicile")
    elif scheme_id == "aaghosh-program":
        if data.get('gender') != "Female": reasons.append("Program available for women only")
        if data.get('status') == "None": reasons.append("Must be pregnant or a lactating mother")
        if get_int('income') > 50000: reasons.append("Family income must be ≤ PKR 50,000/month")
    elif scheme_id == "deceased-transport":
        if data.get('domicile') != "Yes": reasons.append("Service available within Punjab")
    elif scheme_id == "suthra-punjab":
        if data.get('domicile') != "Yes": reasons.append("Available only in Punjab")
    elif scheme_id == "cm-cancer-treatment":
        if data.get('domicile') != "Yes": reasons.append("Must hold Punjab domicile")
        if data.get('diagnosed') != "Yes": reasons.append("Must have a confirmed or suspected diagnosis")
    elif scheme_id == "sme-developer":
        if data.get('domicile') != "Yes": reasons.append("Business must be registered in Punjab")
        if get_int('employees') > 250: reasons.append("SME limit: ≤ 250 employees")
        if get_int('turnover') > 800: reasons.append("Annual turnover must be ≤ PKR 800 million")
    elif scheme_id == "youth-entrepreneurship":
        age = get_int('age')
        if age < 21 or age > 45: reasons.append("Age must be between 21 and 45")
        if data.get('domicile') != "Yes": reasons.append("Must hold Punjab domicile")
        if get_int('loan') > 7500000: reasons.append("Maximum loan limit is PKR 7.5 million")
    elif scheme_id == "labour-digital-services":
        if data.get('registered') != "Yes": reasons.append("Must be registered with Punjab Labour Dept.")
        if data.get('domicile') != "Yes": reasons.append("Must be employed within Punjab")
    elif scheme_id == "pwwf":
        if data.get('registered') != "Yes": reasons.append("Must be a registered industrial worker")
        if get_int('wage') > 50000: reasons.append("Wage cap PKR 50,000/month for benefits")
    elif scheme_id == "hi-tech-mechanization":
        if data.get('domicile') != "Yes": reasons.append("Must be a farmer in Punjab")
        land = get_int('land')
        if land < 5 or land > 50: reasons.append("Eligible land holding 5–50 acres")
    return {"eligible": len(reasons) == 0, "reasons": reasons}

@app.route('/')
def index():
    if 'user' in session: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

import re

cnic_pattern = re.compile(r'^\d{5}-\d{7}-\d{1}$')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        cnic = (request.form.get('cnic') or '').strip()
        password = request.form.get('password')
        
        if not cnic_pattern.match(cnic):
            error = "Invalid CNIC format. Expected format: XXXXX-XXXXXXXX-X (e.g. 37105-23176954-2)"
        else:
            try:
                user_by_cnic = User.query.filter_by(cnic=cnic).first()
                if not user_by_cnic:
                    error = "CNIC does not exist. Please register first."
                else:
                    user = User.query.filter_by(cnic=cnic, password=password).first()
                    if user:
                        session['user'] = {'cnic': user.cnic, 'name': user.name}
                        return redirect(url_for('dashboard'))
                    else:
                        error = "Incorrect password. Please try again."
            except Exception as e:
                error = f"Database connection error: {e}"
    return render_template('login.html', error=error)

def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[@$!%*?&#^()_\-+={[\]}|:;\"'<>,.?/~`\\]", password):
        return False, "Password must contain at least one special character (e.g. @, $, !, %). "
    return True, ""

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    success = None
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        cnic = (request.form.get('cnic') or '').strip()
        password = request.form.get('password') or ''
        
        if not cnic_pattern.match(cnic):
            error = "Invalid CNIC format. Expected format: XXXXX-XXXXXXX-X (e.g. 37105-1215247-1)"
        else:
            is_strong, pw_msg = is_strong_password(password)
            if not is_strong:
                error = pw_msg
            else:
                try:
                    existing_user = User.query.get(cnic)
                    if existing_user:
                        if existing_user.name.strip().lower() == name.lower():
                            error = "You are already registered! Please sign in."
                        else:
                            error = "CNIC is already registered under a different name."
                    else:
                        # Check username uniqueness: no other citizen should have this exact username
                        existing_username = User.query.filter(db.func.lower(User.name) == name.lower()).first()
                        if existing_username:
                            error = "Username is already registered. Please choose a unique name."
                        else:
                            new_user = User(cnic=cnic, name=name, password=password)
                            db.session.add(new_user)
                            db.session.commit()
                            success = "Registration successful! Redirecting..."
                except Exception as e:
                    error = f"Database connection error: {e}"
    return render_template('signup.html', error=error, success=success)


@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html', user=session['user'])

@app.route('/schemes/<cat_id>')
def category(cat_id):
    if 'user' not in session: return redirect(url_for('login'))
    meta = CATEGORY_META.get(cat_id)
    cat_schemes = [s for s in SCHEMES if s['category'] == cat_id]
    return render_template('category.html', user=session['user'], meta=meta, schemes=cat_schemes, cat_id=cat_id)

@app.route('/scheme/<scheme_id>', methods=['GET', 'POST'])
def scheme_detail(scheme_id):
    if 'user' not in session: return redirect(url_for('login'))
    scheme = next((s for s in SCHEMES if s['id'] == scheme_id), None)
    if not scheme: return redirect(url_for('dashboard'))
    result = None
    if request.method == 'POST':
        result = check_eligibility(scheme_id, request.form)
    return render_template('scheme_detail.html', user=session['user'], scheme=scheme, result=result)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=8081)
