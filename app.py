from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)

# New database so it doesn't conflict with the previous version
DB = "job_agent_v2.db"


# =========================================================
# DATABASE
# =========================================================

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = db()
    cur = conn.cursor()

    # -------------------------
    # CANDIDATES
    # -------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            education TEXT,
            skills TEXT,
            experience TEXT,
            projects TEXT,
            location TEXT,
            target_role TEXT,
            resume TEXT,
            created_at TEXT
        )
    """)

    # -------------------------
    # JOBS
    # -------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            salary TEXT,
            description TEXT,
            required_skills TEXT,
            created_at TEXT
        )
    """)

    # -------------------------
    # APPLICATIONS
    # -------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER,
            job_id INTEGER,
            match_score INTEGER,
            matched_skills TEXT,
            missing_skills TEXT,
            resume TEXT,
            cover_letter TEXT,
            answers TEXT,
            recruiter_email TEXT,
            status TEXT,
            created_at TEXT,

            FOREIGN KEY(candidate_id)
            REFERENCES candidates(id),

            FOREIGN KEY(job_id)
            REFERENCES jobs(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================================================
# SKILL DATABASE
# =========================================================

SKILLS = [
    "python",
    "java",
    "c",
    "c++",
    "javascript",
    "typescript",
    "html",
    "css",
    "react",
    "node",
    "express",
    "mongodb",
    "sql",
    "mysql",
    "postgresql",
    "git",
    "github",
    "machine learning",
    "deep learning",
    "artificial intelligence",
    "ai",
    "generative ai",
    "genai",
    "prompt engineering",
    "data analytics",
    "data analysis",
    "pandas",
    "numpy",
    "power bi",
    "tableau",
    "tensorflow",
    "pytorch",
    "flask",
    "django",
    "aws",
    "azure",
    "docker",
    "rest api",
    "api",
    "data structures",
    "algorithms",
    "communication",
    "problem solving",
    "excel",
    "leadership",
    "teamwork"
]


def extract_skills(text):

    text = (text or "").lower()

    found = []

    for skill in SKILLS:

        if skill in text:
            found.append(skill)

    return sorted(set(found))


def calculate_match(candidate, job):

    candidate_text = " ".join([
        candidate["skills"] or "",
        candidate["education"] or "",
        candidate["experience"] or "",
        candidate["projects"] or "",
        candidate["resume"] or ""
    ])

    job_text = " ".join([
        job["description"] or "",
        job["required_skills"] or ""
    ])

    candidate_skills = set(
        extract_skills(candidate_text)
    )

    job_skills = set(
        extract_skills(job_text)
    )

    if not job_skills:

        return 0, [], []

    matched = sorted(
        candidate_skills.intersection(job_skills)
    )

    missing = sorted(
        job_skills - candidate_skills
    )

    score = int(
        len(matched) / len(job_skills) * 100
    )

    return score, matched, missing


# =========================================================
# GENERATORS
# =========================================================

def make_resume(candidate, job, matched):

    skills = ", ".join(matched)

    return f"""
{candidate['name']}

Email: {candidate['email']}
Phone: {candidate['phone']}
Location: {candidate['location']}

TARGET POSITION
{job['title']} - {job['company']}

PROFESSIONAL SUMMARY
Motivated candidate seeking the {job['title']} position.
Academic background, technical skills and project experience
are aligned with the requirements of this opportunity.

EDUCATION
{candidate['education']}

TECHNICAL SKILLS
{candidate['skills']}

JOB-MATCHED SKILLS
{skills}

EXPERIENCE
{candidate['experience']}

PROJECTS
{candidate['projects']}
""".strip()


def make_cover_letter(candidate, job, matched):

    skills = ", ".join(matched)

    return f"""
Dear Hiring Manager,

I am writing to apply for the {job['title']} position
at {job['company']}.

My background includes {candidate['education']} and experience
with {skills if skills else candidate['skills']}.

I am interested in this opportunity because it aligns with
my technical interests and career goals. I am eager to apply
my knowledge to real-world problems and continue developing
my skills.

Thank you for considering my application.

Regards,
{candidate['name']}
{candidate['email']}
""".strip()


def make_answers(candidate, job):

    return f"""
1. Why are you interested in this position?

I am interested in the {job['title']} position because it
matches my technical background, projects and career goals.

2. Why should we consider you?

I have a background in {candidate['education']} and experience
with {candidate['skills']}. I am a motivated learner and enjoy
solving practical technical problems.

3. What are your relevant technical skills?

{candidate['skills']}

4. Tell us about your experience.

{candidate['experience']}

5. Tell us about a relevant project.

{candidate['projects']}
""".strip()


def make_email(candidate, job, matched):

    skills = ", ".join(matched)

    return f"""
Subject: Application for {job['title']} - {candidate['name']}

Dear Hiring Manager,

I am interested in the {job['title']} opportunity at
{job['company']}.

My relevant skills include:
{skills if skills else candidate['skills']}

I would appreciate the opportunity to be considered for this role.

Thank you for your time.

Regards,
{candidate['name']}
{candidate['email']}
""".strip()


# =========================================================
# COMMON HTML
# =========================================================

PAGE = """
<!DOCTYPE html>

<html>

<head>

<title>Job Automation Agent</title>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f3f4f6;
    color: #1f2937;
}

/* NAVBAR */

.navbar {
    background: #111827;
    color: white;
    padding: 16px 28px;

    display: flex;
    justify-content: space-between;
    align-items: center;

    position: sticky;
    top: 0;
    z-index: 10;
}

.logo {
    font-size: 21px;
    font-weight: bold;
}

.nav a {
    color: white;
    text-decoration: none;
    margin-left: 18px;
    font-size: 14px;
}

.nav a:hover {
    color: #93c5fd;
}

/* CONTAINER */

.container {
    width: 94%;
    max-width: 1250px;
    margin: 28px auto;
}

/* CARDS */

.card {
    background: white;
    padding: 24px;
    border-radius: 12px;
    margin-bottom: 22px;

    box-shadow:
        0 2px 8px rgba(0,0,0,0.06);
}

/* DASHBOARD */

.stats {
    display: grid;
    grid-template-columns:
        repeat(4, 1fr);

    gap: 18px;
    margin: 20px 0;
}

.stat {
    background: white;
    padding: 25px;
    border-radius: 12px;
    text-align: center;
}

.stat h2 {
    font-size: 32px;
    margin: 5px;
    color: #2563eb;
}

/* FORMS */

label {
    display: block;
    font-weight: bold;
    margin-top: 12px;
}

input,
textarea,
select {

    width: 100%;

    padding: 12px;

    border: 1px solid #d1d5db;

    border-radius: 7px;

    margin-top: 6px;
    margin-bottom: 12px;

    font-size: 14px;
}

textarea {
    min-height: 120px;
    resize: vertical;
}

/* BUTTONS */

button,
.button {

    display: inline-block;

    background: #2563eb;

    color: white;

    border: none;

    padding: 11px 18px;

    border-radius: 7px;

    cursor: pointer;

    text-decoration: none;

    font-size: 14px;
}

button:hover,
.button:hover {
    background: #1d4ed8;
}

.danger {
    background: #dc2626;
}

.danger:hover {
    background: #b91c1c;
}

.secondary {
    background: #6b7280;
}

.green {
    background: #16a34a;
}

/* TABLE */

.table-wrap {
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    padding: 13px;

    border-bottom:
        1px solid #e5e7eb;

    text-align: left;
}

th {
    background: #f9fafb;
}

/* TAGS */

.tag {
    display: inline-block;

    padding: 6px 10px;

    margin: 3px;

    border-radius: 20px;

    background: #dbeafe;

    font-size: 12px;
}

.missing {
    background: #fee2e2;
}

.success {
    background: #dcfce7;

    padding: 13px;

    border-radius: 7px;

    margin-bottom: 15px;
}

.warning {
    background: #fef3c7;

    padding: 13px;

    border-radius: 7px;

    margin-bottom: 15px;
}

/* JOB CARD */

.job-card {
    border: 1px solid #e5e7eb;

    border-radius: 10px;

    padding: 18px;

    margin-bottom: 15px;

    background: #fff;
}

/* SCORE */

.score {
    font-size: 25px;
    font-weight: bold;
    color: #2563eb;
}

/* TEXT */

pre {
    background: #f8fafc;

    padding: 20px;

    border-radius: 8px;

    white-space: pre-wrap;

    line-height: 1.6;
}

/* TWO COLUMNS */

.two-col {

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 22px;
}

/* STATUS */

.status {
    padding: 6px 10px;

    border-radius: 20px;

    background: #e0e7ff;

    font-size: 12px;
}

/* MOBILE */

@media(max-width: 850px) {

    .navbar {
        flex-direction: column;
        gap: 15px;
    }

    .stats {
        grid-template-columns: 1fr 1fr;
    }

    .two-col {
        grid-template-columns: 1fr;
    }

    .nav a {
        margin-left: 8px;
    }

}

</style>

</head>

<body>

<div class="navbar">

<div class="logo">
🤖 Job Automation Agent
</div>

<div class="nav">

<a href="/">Dashboard</a>

<a href="/candidates">Candidates</a>

<a href="/jobs">Jobs</a>

<a href="/applications">Applications</a>

<a href="/analytics">Analytics</a>

</div>

</div>

<div class="container">

{{ content | safe }}

</div>

</body>

</html>
"""


def render_page(content):

    return render_template_string(
        PAGE,
        content=content
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
def dashboard():

    conn = db()

    candidates = conn.execute(
        "SELECT COUNT(*) FROM candidates"
    ).fetchone()[0]

    jobs = conn.execute(
        "SELECT COUNT(*) FROM jobs"
    ).fetchone()[0]

    applications = conn.execute(
        "SELECT COUNT(*) FROM applications"
    ).fetchone()[0]

    interviews = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE status='Interview'"
    ).fetchone()[0]

    recent = conn.execute("""
        SELECT
            applications.*,
            candidates.name AS candidate_name
        FROM applications
        JOIN candidates
        ON applications.candidate_id = candidates.id
        ORDER BY applications.id DESC
        LIMIT 8
    """).fetchall()

    conn.close()

    content = f"""

<h1>📊 Dashboard</h1>

<p>
Welcome to your Job Automation Agent.
</p>

<div class="stats">

<div class="stat">
<h2>{candidates}</h2>
<p>👥 Candidates</p>
</div>

<div class="stat">
<h2>{jobs}</h2>
<p>💼 Jobs</p>
</div>

<div class="stat">
<h2>{applications}</h2>
<p>📋 Applications</p>
</div>

<div class="stat">
<h2>{interviews}</h2>
<p>🎯 Interviews</p>
</div>

</div>

<div class="card">

<h2>⚡ Quick Actions</h2>

<a class="button" href="/candidates">
➕ Add Candidate
</a>

<a class="button" href="/jobs">
➕ Add Job
</a>

<a class="button" href="/applications">
📋 Create Application
</a>

</div>

<div class="card">

<h2>🕒 Recent Applications</h2>

"""

    if not recent:

        content += """
<p>No applications yet.</p>
"""

    else:

        content += """

<div class="table-wrap">

<table>

<tr>
<th>Candidate</th>
<th>Job</th>
<th>Company</th>
<th>Match</th>
<th>Status</th>
</tr>
"""

        for item in recent:

            content += f"""

<tr>

<td>
{item['candidate_name']}
</td>

<td>
{item['job_title']}
</td>

<td>
{item['company']}
</td>

<td>
{item['match_score']}%
</td>

<td>
<span class="status">
{item['status']}
</span>
</td>

</tr>

"""

        content += """
</table>
</div>
"""

    content += "</div>"

    return render_page(content)


# =========================================================
# CANDIDATES
# =========================================================

@app.route("/candidates", methods=["GET", "POST"])
def candidates():

    conn = db()

    # -------------------------
    # SAVE NEW CANDIDATE
    # -------------------------

    if request.method == "POST":

        conn.execute("""
            INSERT INTO candidates
            (
                name,
                email,
                phone,
                education,
                skills,
                experience,
                projects,
                location,
                target_role,
                resume,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            request.form.get("name"),

            request.form.get("email"),

            request.form.get("phone"),

            request.form.get("education"),

            request.form.get("skills"),

            request.form.get("experience"),

            request.form.get("projects"),

            request.form.get("location"),

            request.form.get("target_role"),

            request.form.get("resume"),

            datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )

        ))

        conn.commit()

        conn.close()

        return redirect(
            url_for(
                "candidates",
                saved="1"
            )
        )

    # -------------------------
    # GET CANDIDATES
    # -------------------------

    search = request.args.get(
        "search",
        ""
    )

    if search:

        candidates_list = conn.execute("""
            SELECT *
            FROM candidates
            WHERE name LIKE ?
            OR email LIKE ?
            OR target_role LIKE ?
            ORDER BY id DESC
        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        )).fetchall()

    else:

        candidates_list = conn.execute("""
            SELECT *
            FROM candidates
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    saved = request.args.get("saved")

    content = """

<h1>👥 Candidate Management</h1>
"""

    if saved:

        content += """

<div class="success">
✅ Candidate saved successfully!
You can add another candidate below.
</div>

"""

    # -------------------------
    # CANDIDATE LIST
    # -------------------------

    content += """

<div class="card">

<h2>📋 Candidate List</h2>

<form method="GET">

<input
name="search"
placeholder="Search candidate by name, email or role..."
>

<button type="submit">
🔎 Search
</button>

<a
class="button secondary"
href="/candidates"
>
Clear
</a>

</form>

"""

    if not candidates_list:

        content += """
<p>No candidates found.</p>
"""

    else:

        content += """

<div class="table-wrap">

<table>

<tr>

<th>ID</th>
<th>Name</th>
<th>Email</th>
<th>Target Role</th>
<th>Location</th>
<th>Actions</th>

</tr>
"""

        for c in candidates_list:

            content += f"""

<tr>

<td>{c['id']}</td>

<td>
<b>{c['name']}</b>
</td>

<td>
{c['email']}
</td>

<td>
{c['target_role']}
</td>

<td>
{c['location']}
</td>

<td>

<a
class="button"
href="/candidate/{c['id']}"
>
View
</a>

<a
class="button secondary"
href="/candidate/{c['id']}/edit"
>
Edit
</a>

<a
class="button danger"
href="/candidate/{c['id']}/delete"
onclick="return confirm('Delete this candidate?')"
>
Delete
</a>

</td>

</tr>

"""

        content += """
</table>
</div>
"""

    content += """

</div>

"""

    # -------------------------
    # NEW CANDIDATE FORM
    # -------------------------

    content += """

<div class="card">

<h2>➕ Add New Candidate</h2>

<p>
Fill this form and click Save. After saving,
the candidate will appear in the list and this
form will automatically become blank.
</p>

<form method="POST">

<label>Name *</label>

<input
name="name"
placeholder="Candidate full name"
required
>

<label>Email</label>

<input
type="email"
name="email"
placeholder="candidate@email.com"
>

<label>Phone</label>

<input
name="phone"
placeholder="+91 XXXXX XXXXX"
>

<label>Education</label>

<input
name="education"
placeholder="B.Tech Computer Science"
>

<label>Skills</label>

<textarea
name="skills"
placeholder="Python, SQL, Generative AI, Prompt Engineering..."
></textarea>

<label>Experience</label>

<textarea
name="experience"
placeholder="Fresher / Internship / Work experience..."
></textarea>

<label>Projects</label>

<textarea
name="projects"
placeholder="Describe projects..."
></textarea>

<label>Location</label>

<input
name="location"
placeholder="Hyderabad"
>

<label>Target Job Role</label>

<input
name="target_role"
placeholder="Generative AI Developer"
>

<label>Resume</label>

<textarea
name="resume"
style="min-height:200px"
placeholder="Paste the candidate's resume text here..."
></textarea>

<button type="submit">
💾 Save Candidate
</button>

</form>

</div>

"""

    return render_page(content)


# =========================================================
# VIEW CANDIDATE
# =========================================================

@app.route("/candidate/<int:candidate_id>")
def view_candidate(candidate_id):

    conn = db()

    candidate = conn.execute(
        "SELECT * FROM candidates WHERE id=?",
        (candidate_id,)
    ).fetchone()

    applications = conn.execute("""
        SELECT
            applications.*,
            jobs.title AS job_title,
            jobs.company AS job_company
        FROM applications
        JOIN jobs
        ON applications.job_id = jobs.id
        WHERE applications.candidate_id=?
        ORDER BY applications.id DESC
    """, (candidate_id,)).fetchall()

    conn.close()

    if not candidate:

        return "Candidate not found."

    content = f"""

<h1>👤 Candidate Profile</h1>

<div class="card">

<h2>{candidate['name']}</h2>

<p>
<b>Email:</b> {candidate['email']}
</p>

<p>
<b>Phone:</b> {candidate['phone']}
</p>

<p>
<b>Education:</b> {candidate['education']}
</p>

<p>
<b>Location:</b> {candidate['location']}
</p>

<p>
<b>Target Role:</b> {candidate['target_role']}
</p>

<h3>Skills</h3>

<p>
{candidate['skills']}
</p>

<h3>Experience</h3>

<pre>{candidate['experience']}</pre>

<h3>Projects</h3>

<pre>{candidate['projects']}</pre>

<a
class="button"
href="/candidate/{candidate_id}/edit"
>
✏️ Edit Candidate
</a>

<a
class="button secondary"
href="/candidates"
>
← Back
</a>

</div>

<div class="card">

<h2>📋 Application History</h2>

"""

    if not applications:

        content += """
<p>No applications for this candidate.</p>
"""

    else:

        content += """

<div class="table-wrap">

<table>

<tr>
<th>Job</th>
<th>Company</th>
<th>Match</th>
<th>Status</th>
<th>Action</th>
</tr>
"""

        for a in applications:

            content += f"""

<tr>

<td>{a['job_title']}</td>

<td>{a['job_company']}</td>

<td>{a['match_score']}%</td>

<td>
<span class="status">
{a['status']}
</span>
</td>

<td>
<a
class="button"
href="/application/{a['id']}"
>
View
</a>
</td>

</tr>

"""

        content += """
</table>
</div>
"""

    content += "</div>"

    return render_page(content)


# =========================================================
# EDIT CANDIDATE
# =========================================================

@app.route(
    "/candidate/<int:candidate_id>/edit",
    methods=["GET", "POST"]
)
def edit_candidate(candidate_id):

    conn = db()

    candidate = conn.execute(
        "SELECT * FROM candidates WHERE id=?",
        (candidate_id,)
    ).fetchone()

    if not candidate:

        conn.close()

        return "Candidate not found."

    if request.method == "POST":

        conn.execute("""
            UPDATE candidates

            SET
                name=?,
                email=?,
                phone=?,
                education=?,
                skills=?,
                experience=?,
                projects=?,
                location=?,
                target_role=?,
                resume=?

            WHERE id=?
        """, (

            request.form.get("name"),

            request.form.get("email"),

            request.form.get("phone"),

            request.form.get("education"),

            request.form.get("skills"),

            request.form.get("experience"),

            request.form.get("projects"),

            request.form.get("location"),

            request.form.get("target_role"),

            request.form.get("resume"),

            candidate_id

        ))

        conn.commit()

        conn.close()

        return redirect(
            url_for(
                "view_candidate",
                candidate_id=candidate_id
            )
        )

    conn.close()

    content = f"""

<h1>✏️ Edit Candidate</h1>

<div class="card">

<form method="POST">

<label>Name</label>

<input
name="name"
value="{candidate['name']}"
required
>

<label>Email</label>

<input
name="email"
value="{candidate['email']}"
>

<label>Phone</label>

<input
name="phone"
value="{candidate['phone']}"
>

<label>Education</label>

<input
name="education"
value="{candidate['education']}"
>

<label>Skills</label>

<textarea
name="skills"
>{candidate['skills']}</textarea>

<label>Experience</label>

<textarea
name="experience"
>{candidate['experience']}</textarea>

<label>Projects</label>

<textarea
name="projects"
>{candidate['projects']}</textarea>

<label>Location</label>

<input
name="location"
value="{candidate['location']}"
>

<label>Target Role</label>

<input
name="target_role"
value="{candidate['target_role']}"
>

<label>Resume</label>

<textarea
name="resume"
style="min-height:220px"
>{candidate['resume']}</textarea>

<button type="submit">
💾 Update Candidate
</button>

<a
class="button secondary"
href="/candidate/{candidate_id}"
>
Cancel
</a>

</form>

</div>

"""

    return render_page(content)


# =========================================================
# DELETE CANDIDATE
# =========================================================

@app.route("/candidate/<int:candidate_id>/delete")
def delete_candidate(candidate_id):

    conn = db()

    # Delete applications first
    conn.execute(
        "DELETE FROM applications WHERE candidate_id=?",
        (candidate_id,)
    )

    conn.execute(
        "DELETE FROM candidates WHERE id=?",
        (candidate_id,)
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for("candidates")
    )


# =========================================================
# JOBS
# =========================================================

@app.route("/jobs", methods=["GET", "POST"])
def jobs():

    conn = db()

    if request.method == "POST":

        title = request.form.get("title")
        company = request.form.get("company")
        location = request.form.get("location")
        salary = request.form.get("salary")
        description = request.form.get("description")

        detected = extract_skills(
            description
        )

        required = ", ".join(
            detected
        )

        conn.execute("""
            INSERT INTO jobs
            (
                title,
                company,
                location,
                salary,
                description,
                required_skills,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (

            title,
            company,
            location,
            salary,
            description,
            required,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )

        ))

        conn.commit()

        conn.close()

        return redirect(
            url_for(
                "jobs",
                saved="1"
            )
        )

    job_list = conn.execute("""
        SELECT *
        FROM jobs
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    saved = request.args.get("saved")

    content = """

<h1>💼 Job Management</h1>
"""

    if saved:

        content += """

<div class="success">
✅ Job saved successfully!
You can add another job below.
</div>

"""

    # -------------------------
    # JOB LIST
    # -------------------------

    content += """

<div class="card">

<h2>📋 Available Jobs</h2>

"""

    if not job_list:

        content += """
<p>No jobs added yet.</p>
"""

    for job in job_list:

        content += f"""

<div class="job-card">

<h2>{job['title']}</h2>

<p>
<b>Company:</b>
{job['company']}
</p>

<p>
<b>Location:</b>
{job['location']}
</p>

<p>
<b>Salary:</b>
{job['salary']}
</p>

<p>
<b>Required Skills:</b>
{job['required_skills'] or 'Not detected'}
</p>

<a
class="button"
href="/job/{job['id']}"
>
🔎 Analyze
</a>

<a
class="button danger"
href="/job/{job['id']}/delete"
onclick="return confirm('Delete this job?')"
>
Delete
</a>

</div>

"""

    content += """

</div>

"""

    # -------------------------
    # ADD JOB
    # -------------------------

    content += """

<div class="card">

<h2>➕ Add New Job</h2>

<form method="POST">

<label>Job Title *</label>

<input
name="title"
placeholder="Generative AI Developer"
required
>

<label>Company *</label>

<input
name="company"
placeholder="ABC Technologies"
required
>

<label>Location</label>

<input
name="location"
placeholder="Hyderabad / Remote"
>

<label>Salary</label>

<input
name="salary"
placeholder="6 - 10 LPA"
>

<label>Job Description *</label>

<textarea
name="description"
style="min-height:250px"
placeholder="Paste complete job description..."
required
></textarea>

<button type="submit">
💾 Save Job
</button>

</form>

</div>

"""

    return render_page(content)


# =========================================================
# VIEW / ANALYZE JOB
# =========================================================

@app.route("/job/<int:job_id>")
def view_job(job_id):

    conn = db()

    job = conn.execute(
        "SELECT * FROM jobs WHERE id=?",
        (job_id,)
    ).fetchone()

    candidates_list = conn.execute("""
        SELECT *
        FROM candidates
        ORDER BY name
    """).fetchall()

    conn.close()

    if not job:

        return "Job not found."

    content = f"""

<h1>🔎 Job Analysis</h1>

<div class="card">

<h2>{job['title']}</h2>

<p>
<b>Company:</b>
{job['company']}
</p>

<p>
<b>Location:</b>
{job['location']}
</p>

<p>
<b>Salary:</b>
{job['salary']}
</p>

<h3>Required Skills</h3>

<p>
"""

    for skill in extract_skills(
        job["description"]
    ):

        content += f"""
<span class="tag">
{skill}
</span>
"""

    content += f"""

</p>

<h3>Job Description</h3>

<pre>{job['description']}</pre>

</div>

<div class="card">

<h2>👤 Check Candidate Match</h2>

<form method="POST"
action="/analyze-job">

<input
type="hidden"
name="job_id"
value="{job_id}"
>

<label>Select Candidate</label>

<select name="candidate_id" required>

<option value="">
-- Select Candidate --
</option>
"""

    for candidate in candidates_list:

        content += f"""

<option value="{candidate['id']}">
{candidate['name']} - {candidate['target_role']}
</option>

"""

    content += """

</select>

<button type="submit">
📊 Analyze Match
</button>

</form>

</div>

"""

    return render_page(content)


# =========================================================
# ANALYZE JOB MATCH
# =========================================================

@app.route("/analyze-job", methods=["POST"])
def analyze_job():

    candidate_id = request.form.get(
        "candidate_id"
    )

    job_id = request.form.get(
        "job_id"
    )

    conn = db()

    candidate = conn.execute(
        "SELECT * FROM candidates WHERE id=?",
        (candidate_id,)
    ).fetchone()

    job = conn.execute(
        "SELECT * FROM jobs WHERE id=?",
        (job_id,)
    ).fetchone()

    conn.close()

    if not candidate or not job:

        return "Candidate or job not found."

    score, matched, missing = calculate_match(
        candidate,
        job
    )

    content = f"""

<h1>📊 Candidate Match Result</h1>

<div class="card">

<h2>
{candidate['name']}
→
{job['title']}
</h2>

<p>
<b>Company:</b>
{job['company']}
</p>

<p class="score">
Match Score: {score}%
</p>

<h3>✅ Matching Skills</h3>

"""

    if matched:

        for skill in matched:

            content += f"""
<span class="tag">
{skill}
</span>
"""

    else:

        content += "<p>No matching skills found.</p>"

    content += """

<h3>⚠️ Missing Skills</h3>

"""

    if missing:

        for skill in missing:

            content += f"""
<span class="tag missing">
{skill}
</span>
"""

    else:

        content += """
<p>No major missing skills detected.</p>
"""

    content += f"""

<br><br>

<form method="POST"
action="/create-application">

<input
type="hidden"
name="candidate_id"
value="{candidate_id}"
>

<input
type="hidden"
name="job_id"
value="{job_id}"
>

<button type="submit">
✨ Generate Application
</button>

</form>

</div>

"""

    return render_page(content)


# =========================================================
# DELETE JOB
# =========================================================

@app.route("/job/<int:job_id>/delete")
def delete_job(job_id):

    conn = db()

    conn.execute(
        "DELETE FROM applications WHERE job_id=?",
        (job_id,)
    )

    conn.execute(
        "DELETE FROM jobs WHERE id=?",
        (job_id,)
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for("jobs")
    )


# =========================================================
# APPLICATIONS
# =========================================================

@app.route("/applications")
def applications():

    conn = db()

    applications_list = conn.execute("""
        SELECT
            applications.*,
            candidates.name AS candidate_name,
            jobs.title AS job_title,
            jobs.company AS job_company
        FROM applications

        JOIN candidates
        ON applications.candidate_id =
           candidates.id

        JOIN jobs
        ON applications.job_id =
           jobs.id

        ORDER BY applications.id DESC

    """).fetchall()

    candidates_list = conn.execute("""
        SELECT *
        FROM candidates
        ORDER BY name
    """).fetchall()

    jobs_list = conn.execute("""
        SELECT *
        FROM jobs
        ORDER BY title
    """).fetchall()

    conn.close()

    content = """

<h1>📋 Application Management</h1>

<div class="card">

<h2>➕ Create New Application</h2>

<form method="POST"
action="/create-application">

<label>Candidate</label>

<select name="candidate_id" required>

<option value="">
-- Select Candidate --
</option>
"""

    for c in candidates_list:

        content += f"""

<option value="{c['id']}">
{c['name']} - {c['target_role']}
</option>

"""

    content += """

</select>

<label>Job</label>

<select name="job_id" required>

<option value="">
-- Select Job --
</option>
"""

    for job in jobs_list:

        content += f"""

<option value="{job['id']}">
{job['title']} - {job['company']}
</option>

"""

    content += """

</select>

<button type="submit">
✨ Generate Application
</button>

</form>

</div>

<div class="card">

<h2>📋 Application Tracker</h2>

"""

    if not applications_list:

        content += """
<p>No applications created yet.</p>
"""

    else:

        content += """

<div class="table-wrap">

<table>

<tr>

<th>Candidate</th>
<th>Job</th>
<th>Company</th>
<th>Match</th>
<th>Status</th>
<th>Created</th>
<th>Action</th>

</tr>
"""

        for a in applications_list:

            content += f"""

<tr>

<td>
{a['candidate_name']}
</td>

<td>
{a['job_title']}
</td>

<td>
{a['job_company']}
</td>

<td>
<b>{a['match_score']}%</b>
</td>

<td>

<form method="POST"
action="/application/{a['id']}/status">

<select name="status"
onchange="this.form.submit()">

"""

            statuses = [
                "Saved",
                "Applied",
                "Shortlisted",
                "Interview",
                "Rejected",
                "Selected"
            ]

            for status in statuses:

                selected = ""

                if a["status"] == status:
                    selected = "selected"

                content += f"""

<option
value="{status}"
{selected}
>
{status}
</option>

"""

            content += f"""

</select>

</form>

</td>

<td>
{a['created_at']}
</td>

<td>

<a
class="button"
href="/application/{a['id']}"
>
View
</a>

</td>

</tr>

"""

        content += """
</table>
</div>
"""

    content += "</div>"

    return render_page(content)


# =========================================================
# CREATE APPLICATION
# =========================================================

@app.route(
    "/create-application",
    methods=["POST"]
)
def create_application():

    candidate_id = request.form.get(
        "candidate_id"
    )

    job_id = request.form.get(
        "job_id"
    )

    conn = db()

    candidate = conn.execute(
        "SELECT * FROM candidates WHERE id=?",
        (candidate_id,)
    ).fetchone()

    job = conn.execute(
        "SELECT * FROM jobs WHERE id=?",
        (job_id,)
    ).fetchone()

    conn.close()

    if not candidate or not job:

        return "Candidate or job not found."

    score, matched, missing = calculate_match(
        candidate,
        job
    )

    resume = make_resume(
        candidate,
        job,
        matched
    )

    cover = make_cover_letter(
        candidate,
        job,
        matched
    )

    answers = make_answers(
        candidate,
        job
    )

    email = make_email(
        candidate,
        job,
        matched
    )

    conn = db()

    conn.execute("""
        INSERT INTO applications

        (
            candidate_id,
            job_id,
            match_score,
            matched_skills,
            missing_skills,
            resume,
            cover_letter,
            answers,
            recruiter_email,
            status,
            created_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        candidate_id,

        job_id,

        score,

        ", ".join(matched),

        ", ".join(missing),

        resume,

        cover,

        answers,

        email,

        "Saved",

        datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )

    ))

    conn.commit()

    application_id = conn.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    conn.close()

    return redirect(
        url_for(
            "view_application",
            application_id=application_id
        )
    )


# =========================================================
# VIEW APPLICATION
# =========================================================

@app.route("/application/<int:application_id>")
def view_application(application_id):

    conn = db()

    application = conn.execute("""
        SELECT
            applications.*,
            candidates.name AS candidate_name,
            jobs.title AS job_title,
            jobs.company AS company
        FROM applications

        JOIN candidates
        ON applications.candidate_id =
           candidates.id

        JOIN jobs
        ON applications.job_id =
           jobs.id

        WHERE applications.id=?

    """, (application_id,)).fetchone()

    conn.close()

    if not application:

        return "Application not found."

    content = f"""

<h1>📄 Application Details</h1>

<div class="card">

<h2>{application['job_title']}</h2>

<p>
<b>Candidate:</b>
{application['candidate_name']}
</p>

<p>
<b>Company:</b>
{application['company']}
</p>

<p>
<b>Match Score:</b>

<span class="score">
{application['match_score']}%
</span>

</p>

<p>
<b>Status:</b>
<span class="status">
{application['status']}
</span>
</p>

</div>

<div class="two-col">

<div class="card">

<h2>📄 Customized Resume</h2>

<pre>{application['resume']}</pre>

</div>

<div class="card">

<h2>✉️ Cover Letter</h2>

<pre>{application['cover_letter']}</pre>

</div>

</div>

<div class="card">

<h2>❓ Application Answers</h2>

<pre>{application['answers']}</pre>

</div>

<div class="card">

<h2>📨 Recruiter Email</h2>

<pre>{application['recruiter_email']}</pre>

</div>

<div class="card">

<h2>🎯 Skills Analysis</h2>

<h3>Matching Skills</h3>

<p>
{application['matched_skills'] or 'None'}
</p>

<h3>Missing Skills</h3>

<p>
{application['missing_skills'] or 'None'}
</p>

</div>

<a
class="button"
href="/applications"
>
← Back to Applications
</a>

"""

    return render_page(content)


# =========================================================
# CHANGE APPLICATION STATUS
# =========================================================

@app.route(
    "/application/<int:application_id>/status",
    methods=["POST"]
)
def change_status(application_id):

    status = request.form.get(
        "status"
    )

    allowed = [
        "Saved",
        "Applied",
        "Shortlisted",
        "Interview",
        "Rejected",
        "Selected"
    ]

    if status not in allowed:

        status = "Saved"

    conn = db()

    conn.execute("""
        UPDATE applications
        SET status=?
        WHERE id=?
    """, (
        status,
        application_id
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for("applications")
    )


# =========================================================
# ANALYTICS
# =========================================================

@app.route("/analytics")
def analytics():

    conn = db()

    total = conn.execute(
        "SELECT COUNT(*) FROM applications"
    ).fetchone()[0]

    saved = conn.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status='Saved'
    """).fetchone()[0]

    applied = conn.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status='Applied'
    """).fetchone()[0]

    shortlisted = conn.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status='Shortlisted'
    """).fetchone()[0]

    interviews = conn.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status='Interview'
    """).fetchone()[0]

    rejected = conn.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status='Rejected'
    """).fetchone()[0]

    selected = conn.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status='Selected'
    """).fetchone()[0]

    average = conn.execute("""
        SELECT AVG(match_score)
        FROM applications
    """).fetchone()[0]

    conn.close()

    average = round(
        average or 0,
        1
    )

    content = f"""

<h1>📈 Analytics</h1>

<div class="stats">

<div class="stat">
<h2>{total}</h2>
<p>Total Applications</p>
</div>

<div class="stat">
<h2>{applied}</h2>
<p>Applied</p>
</div>

<div class="stat">
<h2>{shortlisted}</h2>
<p>Shortlisted</p>
</div>

<div class="stat">
<h2>{interviews}</h2>
<p>Interviews</p>
</div>

</div>

<div class="stats">

<div class="stat">
<h2>{selected}</h2>
<p>Selected</p>
</div>

<div class="stat">
<h2>{rejected}</h2>
<p>Rejected</p>
</div>

<div class="stat">
<h2>{saved}</h2>
<p>Saved</p>
</div>

<div class="stat">
<h2>{average}%</h2>
<p>Average Match</p>
</div>

</div>

<div class="card">

<h2>📊 Application Pipeline</h2>

<p>
Saved → Applied → Shortlisted → Interview → Selected
</p>

<div style="
background:#e5e7eb;
height:30px;
border-radius:8px;
overflow:hidden;
">

<div style="
background:#2563eb;
height:30px;
width:{min(100, total * 10)}%;
">
</div>

</div>

<br>

<p>
The analytics page helps track the candidate
application pipeline and overall job-search activity.
</p>

</div>

"""

    return render_page(content)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    print()
    print("========================================")
    print("       JOB AUTOMATION AGENT")
    print("========================================")
    print()
    print("Open this in your browser:")
    print()
    print("http://127.0.0.1:5000")
    print()
    print("Press CTRL+C to stop the server.")
    print("========================================")
    print()

    app.run(
        debug=True,
        port=5000
    )