import streamlit as st
import json
import requests
import re
from modules import utils

# ─────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SkillBridge — AI Adaptive Onboarding Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────────────────
defaults = {
    "step": 1,
    "resume_text": "",
    "jd_text": "",
    "resume_file_name": None,
    "jd_file_name": None,
    "analysis_result": None,
    "api_key": "",
    "error_message": None,
    "show_reasoning": False,
    "config": {
        "industry": "Technology / Software",
        "seniority": "Mid-Level (2–5 years)",
        "timeline": 8,
        "preferences": ["Video Courses", "Documentation"],
        "focus": [],
        "catalog": "",
    },
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────
def go(step: int):
    st.session_state.step = step
    st.session_state.error_message = None


def load_sample():
    st.session_state.resume_text = """Sarah Chen — Software Engineer
Email: sarah.chen@example.com | GitHub: github.com/schen

EXPERIENCE
• Junior Software Developer, WebCo Inc (2 years)
  - Built REST APIs in Node.js/Express
  - Developed React frontends with Redux
  - Wrote MySQL queries for reporting dashboards
  - Used Git for version control in Agile sprints

EDUCATION
B.Sc Computer Science, State University (2022)

SKILLS
Languages: JavaScript, Python (basics), HTML/CSS
Frameworks: React, Node.js, Express
Databases: MySQL
Tools: Git, VS Code, Postman
Soft Skills: Communication, teamwork, Agile/Scrum"""

    st.session_state.jd_text = """Senior Full-Stack Engineer — FinTech Startup

ROLE OVERVIEW
We are seeking a Senior Full-Stack Engineer to lead product development for our payments platform. You will architect scalable cloud systems and mentor junior engineers.

REQUIRED SKILLS
• 5+ years full-stack development
• TypeScript (advanced)
• React with Next.js
• Node.js microservices architecture
• PostgreSQL + Redis
• AWS (EC2, S3, Lambda, RDS)
• Docker & Kubernetes
• CI/CD pipelines (GitHub Actions / Jenkins)
• REST API design & GraphQL
• System design & architecture

NICE TO HAVE
• Kafka / event-driven architecture
• Terraform / infrastructure as code
• Security best practices (OWASP)
• Financial domain experience"""


def fallback_data():
    return {
        "candidate_name": "Sarah Chen",
        "role_title": "Senior Full-Stack Engineer",
        "overall_readiness": 58,
        "time_saved_percent": 42,
        "skills_have": ["JavaScript","React","Node.js","MySQL","Git","HTML/CSS","REST APIs","Express","Agile/Scrum"],
        "skills_gap": ["TypeScript","Next.js","PostgreSQL","Redis","AWS","Docker","Kubernetes","GraphQL","CI/CD","System Design"],
        "total_weeks": 9,
        "modules": [
            {"id":1,"title":"TypeScript Mastery","priority":"critical","duration":"1.5 weeks",
             "description":"Transition from JavaScript to TypeScript with a focus on advanced types, interfaces, and type-safe React patterns. This is the most critical gap as TypeScript is the primary language for the role.",
             "skills_addressed":["TypeScript","Type-safe APIs"],"resources":"TypeScript Handbook (official docs) + Udemy TypeScript course"},
            {"id":2,"title":"Cloud Infrastructure with AWS","priority":"critical","duration":"2 weeks",
             "description":"Core AWS services: EC2, S3, RDS, and Lambda. Learn to provision, configure and deploy applications to production cloud environments using the AWS console and CLI.",
             "skills_addressed":["AWS","EC2","S3","Lambda","RDS"],"resources":"AWS Certified Developer course + hands-on lab projects"},
            {"id":3,"title":"Next.js & Advanced React Patterns","priority":"important","duration":"1 week",
             "description":"Leverage existing React knowledge to learn Next.js SSR/SSG, App Router, API routes, and performance optimization strategies used in production FinTech apps.",
             "skills_addressed":["Next.js","Server-side rendering"],"resources":"Next.js official docs + Vercel learning platform"},
            {"id":4,"title":"PostgreSQL, Redis & Data Architecture","priority":"important","duration":"1 week",
             "description":"Upgrade from MySQL to PostgreSQL and learn Redis for caching and session management. Focus on query optimization, indexing, and designing schemas for financial data.",
             "skills_addressed":["PostgreSQL","Redis","Data modeling"],"resources":"PostgreSQL official tutorial + Redis University (free)"},
            {"id":5,"title":"Docker & Container Orchestration","priority":"important","duration":"1.5 weeks",
             "description":"Build, containerize and deploy microservices using Docker. Introduction to Kubernetes for orchestration, scaling, and managing containerized workloads in production.",
             "skills_addressed":["Docker","Kubernetes","Microservices"],"resources":"Docker official getting started + KodeKloud Kubernetes course"},
            {"id":6,"title":"CI/CD & DevOps Practices","priority":"nice","duration":"1 week",
             "description":"Implement automated build, test, and deployment pipelines using GitHub Actions. Learn branching strategies, environment management, and deployment automation patterns.",
             "skills_addressed":["GitHub Actions","CI/CD","DevOps"],"resources":"GitHub Actions documentation + internal engineering playbook"},
            {"id":7,"title":"System Design & Architecture Capstone","priority":"foundation","duration":"1 week",
             "description":"Apply all acquired skills to design a scalable payment processing microservice. Covers system design principles, GraphQL API design, and architecture review with the engineering team.",
             "skills_addressed":["System Design","GraphQL","Architecture"],"resources":"System Design Primer (GitHub) + internal architecture review session"},
        ],
        "reasoning_trace": (
            "SKILL EXTRACTION ANALYSIS:\n"
            "From the resume, I identified: JavaScript (2+ years, strong), React with Redux, Node.js/Express, MySQL, Git, and Agile/Scrum.\n\n"
            "SKILL GAP COMPUTATION:\n"
            "Critical gaps: TypeScript (none vs advanced required), AWS cloud infrastructure, PostgreSQL/Redis, Docker/Kubernetes, CI/CD pipelines.\n\n"
            "PATHWAY ORDERING LOGIC:\n"
            "TypeScript first as foundational language. AWS second for deployment. Next.js third (depends on TS). DB upgrade fourth. Docker fifth. CI/CD near end. Capstone synthesises all.\n\n"
            "SKIPPED CONTENT:\n"
            "React fundamentals (~2 weeks), Node.js foundations (~1 week), Git/Agile (no training needed). Estimated 42% training time saved.\n\n"
            "TIMELINE:\n"
            "9 weeks at ~20 hrs/week. Capstone in week 9 acts as role-readiness gate."
        ),
    }


def call_claude(api_key, resume, jd, cfg):
    system_prompt = """You are SkillBridge, a precise AI Onboarding Engine that performs STRICTLY GROUNDED skill-gap analysis.

ABSOLUTE RULES — never break these:
1. skills_have must contain ONLY skills, tools, frameworks, languages, or methodologies that appear WORD-FOR-WORD or by clear abbreviation in the resume text. If a skill is not literally written in the resume, it does NOT go in skills_have. No exceptions.
2. Do NOT infer, assume, or deduce skills. "Built REST APIs" does NOT imply Docker. "Used AWS" does NOT imply Kubernetes. Only include what is explicitly stated.
3. skills_gap must contain ONLY skills that are explicitly required or listed in the job description AND are absent from the resume.
4. Never fabricate course names, certifications, or tools.
5. Respond with valid JSON only — no markdown fences, no preamble, no trailing text."""

    user_prompt = f"""Analyze ONLY the resume and job description text provided below.

=== RESUME (extract skills ONLY from this text) ===
{resume}
=== END RESUME ===

=== JOB DESCRIPTION (extract requirements ONLY from this text) ===
{jd}
=== END JOB DESCRIPTION ===

CONFIGURATION:
- Industry: {cfg['industry']}
- Target Seniority: {cfg['seniority']}
- Onboarding Timeline: {cfg['timeline']} weeks
- Learning Preferences: {', '.join(cfg['preferences']) if cfg['preferences'] else 'No preference'}
- Course Catalog/Notes: {cfg['catalog'] or 'None specified'}

STEP-BY-STEP INSTRUCTIONS — follow in order:

STEP 1 — RESUME SKILL EXTRACTION (strict):
Read every word in the resume. List only skills, tools, frameworks, languages, databases, platforms, and methodologies that are LITERALLY written there. Do not add anything that is not in the text. When in doubt, leave it out.

STEP 2 — JD REQUIREMENT EXTRACTION (strict):
Read every word in the JD. List only skills and technologies that are explicitly stated as required or expected.

STEP 3 — GAP COMPUTATION:
Gap = (skills in STEP 2) that are NOT in (skills in STEP 1). Only list a skill as a gap if it is absent from the resume entirely.

STEP 4 — LEARNING PATHWAY:
Design 5–7 modules that cover ONLY the gap skills from STEP 3. Order by prerequisite dependency first, then business criticality. Do not create modules for skills the candidate already has.

STEP 5 — METRICS:
- overall_readiness: percentage of JD requirements the candidate currently meets based on STEP 1 vs STEP 2.
- time_saved_percent: estimated % of a generic onboarding programme skipped due to existing skills.

STEP 6 — REASONING TRACE:
Write a detailed multi-paragraph explanation covering:
- Exactly which words/phrases in the resume led to each skill in skills_have
- Exactly which words/phrases in the JD led to each skill in skills_gap
- Why each module is ordered where it is
- What was skipped and the exact resume evidence for skipping it

Return ONLY this JSON (no extra text):
{{
  "candidate_name": "string from resume or 'Candidate'",
  "role_title": "string from JD",
  "overall_readiness": integer 0-100,
  "time_saved_percent": integer 0-100,
  "skills_have": ["only skills literally found in resume"],
  "skills_gap":  ["only skills literally in JD but absent from resume"],
  "total_weeks": integer,
  "modules": [
    {{
      "id": integer,
      "title": "string",
      "priority": "critical | important | nice | foundation",
      "duration": "e.g. 1.5 weeks",
      "description": "2-3 sentences: what is taught and why sequenced here",
      "skills_addressed": ["gap skills this module covers"],
      "resources": "realistic resource suggestions"
    }}
  ],
  "reasoning_trace": "detailed multi-paragraph explanation citing exact resume/JD text evidence"
}}"""

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 8000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        timeout=120,
    )

    if not resp.ok:
        err = resp.json().get("error", {})
        raise Exception(f"API {resp.status_code}: {err.get('message', resp.text)}")

    raw = resp.json()["content"][0]["text"].strip()

    # Strip any accidental markdown fences
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()

    # Find the outermost JSON object in case there is surrounding text
    match = re.search(r"\{.*\}", clean, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in API response")

    result = json.loads(match.group())

    # Validate required keys
    required = ["candidate_name","role_title","overall_readiness","time_saved_percent",
                "skills_have","skills_gap","total_weeks","modules","reasoning_trace"]
    missing = [k for k in required if k not in result]
    if missing:
        raise ValueError(f"API response missing keys: {missing}")

    # Post-process: cross-check skills_have against resume text (case-insensitive)
    # Remove any skill that cannot be found anywhere in the resume text
    resume_lower = resume.lower()
    verified_have = []
    hallucinated = []
    for skill in result.get("skills_have", []):
        # Check if any word from the skill name appears in the resume
        skill_words = [w for w in skill.lower().split() if len(w) > 2]
        if any(w in resume_lower for w in skill_words):
            verified_have.append(skill)
        else:
            hallucinated.append(skill)

    result["skills_have"] = verified_have
    if hallucinated:
        result["reasoning_trace"] = (
            f"[POST-PROCESSING NOTE: The following skills were removed from skills_have "
            f"because they could not be verified in the resume text: {', '.join(hallucinated)}]\n\n"
            + result.get("reasoning_trace", "")
        )

    return result


def run_analysis():
    try:
        if st.session_state.api_key.strip():
            result = call_claude(
                st.session_state.api_key.strip(),
                st.session_state.resume_text,
                st.session_state.jd_text,
                st.session_state.config,
            )
            st.session_state.error_message = None
        else:
            result = fallback_data()
            st.session_state.error_message = "ℹ️ No API key provided — showing demo pathway."
        st.session_state.analysis_result = result
    except Exception as e:
        st.session_state.error_message = f"⚠️ API error: {e} — showing demo pathway."
        st.session_state.analysis_result = fallback_data()
    go(4)


# ─────────────────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root {
  --bg:       #08080e;
  --s1:       #10101a;
  --s2:       #171722;
  --s3:       #1e1e2c;
  --s4:       #252535;
  --b:        rgba(255,255,255,0.06);
  --bh:       rgba(255,255,255,0.13);
  --ind:      #6366f1;
  --ind2:     #818cf8;
  --vio:      #a78bfa;
  --cya:      #22d3ee;
  --grn:      #34d399;
  --amb:      #fbbf24;
  --ros:      #fb7185;
  --txt:      #eeeef8;
  --txt2:     #9898b8;
  --txt3:     #46465a;
  --fh:       'Syne', sans-serif;
  --fb:       'DM Sans', sans-serif;
  --r:        12px;
  --rl:       18px;
  --rx:       24px;
}

/* ── STREAMLIT CHROME HIDE ── */
#MainMenu, footer, .stDeployButton,
header[data-testid="stHeader"] { display: none !important; }
.block-container { padding-top: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }

/* ── GLOBAL BASE ── */
html, body, .stApp {
  background: var(--bg) !important;
  color: var(--txt) !important;
  font-family: var(--fb) !important;
}
.stApp::before {
  content: '';
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 70% 55% at 15% 0%,  rgba(99,102,241,.11) 0%, transparent 60%),
    radial-gradient(ellipse 55% 45% at 85% 100%, rgba(34,211,238,.07) 0%, transparent 60%);
}

/* ── NAVBAR ── */
.sb-nav {
  display: flex; align-items: center; justify-content: space-between;
  height: 62px; padding: 0 2rem;
  background: rgba(8,8,14,.88); backdrop-filter: blur(18px);
  border-bottom: 1px solid var(--b);
  position: sticky; top: 0; z-index: 100;
}
.sb-logo {
  font-family: var(--fh); font-size: 1.2rem; font-weight: 800;
  letter-spacing: -.03em; display: flex; align-items: center; gap: 10px;
}
.sb-logo-mark {
  width: 32px; height: 32px; border-radius: 8px;
  background: linear-gradient(135deg,var(--ind),var(--cya));
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; box-shadow: 0 0 18px rgba(99,102,241,.4);
}
.sb-logo em { font-style: normal; color: var(--vio); }
.sb-pill {
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .07em; color: var(--ind2);
  background: rgba(99,102,241,.1); border: 1px solid rgba(99,102,241,.22);
  padding: 4px 12px; border-radius: 20px;
}

/* ── HERO ── */
.sb-hero {
  text-align: center; padding: 3.5rem 1.5rem 2.5rem;
}
.sb-hero h1 {
  font-family: var(--fh); font-size: clamp(2rem,5vw,3.4rem);
  font-weight: 800; letter-spacing: -.03em; line-height: 1.1;
  margin: .75rem 0 1rem;
}
.sb-hero h1 em {
  font-style: normal;
  background: linear-gradient(135deg,var(--vio),var(--cya));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.sb-eyebrow {
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .1em; color: var(--ind2);
  background: rgba(99,102,241,.1); border: 1px solid rgba(99,102,241,.2);
  padding: 5px 14px; border-radius: 20px;
}
.sb-eyebrow::before {
  content:''; width:6px; height:6px; border-radius:50%;
  background:var(--grn); animation: blink 2s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
.sb-hero p { font-size: 1.05rem; color: var(--txt2); font-weight: 300; line-height: 1.8; }

/* ── STEP BAR ── */
.sb-stepbar {
  display: flex; align-items: center; justify-content: center;
  gap: 0; max-width: 560px; margin: 1.75rem auto 0;
}
.sb-step { display: flex; flex-direction: column; align-items: center; gap: 7px; }
.sb-circle {
  width: 36px; height: 36px; border-radius: 50%;
  border: 1px solid var(--bh); background: var(--s2);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; color: var(--txt2);
  transition: all .3s;
}
.sb-step.active .sb-circle {
  background: var(--ind); border-color: var(--ind);
  color: #fff; box-shadow: 0 0 20px rgba(99,102,241,.45);
}
.sb-step.done .sb-circle {
  background: var(--grn); border-color: var(--grn); color: #08080e;
}
.sb-slabel {
  font-size: 10.5px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .07em; color: var(--txt3); white-space: nowrap;
}
.sb-step.active .sb-slabel { color: var(--ind2); }
.sb-step.done  .sb-slabel { color: var(--grn); }
.sb-sline {
  flex: 1; height: 1px; background: var(--b); min-width: 48px;
  transition: background .35s;
}
.sb-sline.done { background: linear-gradient(90deg,var(--grn),var(--ind)); }

/* ── CARD ── */
.sb-card {
  background: var(--s1); border: 1px solid var(--b);
  border-radius: var(--rx); overflow: hidden;
  box-shadow: 0 4px 32px rgba(0,0,0,.45);
  max-width: 900px; margin: 2rem auto 3rem;
}
.sb-card-hd {
  display: flex; align-items: center; gap: 14px;
  padding: 1.4rem 1.75rem; border-bottom: 1px solid var(--b);
}
.sb-hd-icon {
  width: 40px; height: 40px; border-radius: var(--r);
  display: flex; align-items: center; justify-content: center;
  font-size: 19px; flex-shrink: 0;
}
.sb-hd-icon.ind { background: rgba(99,102,241,.12); }
.sb-hd-icon.cya { background: rgba(34,211,238,.10); }
.sb-hd-icon.grn { background: rgba(52,211,153,.10); }
.sb-card-hd h2 {
  font-family: var(--fh); font-size: 1rem; font-weight: 700;
  letter-spacing: -.01em; color: #fff; margin: 0 0 2px;
}
.sb-card-hd p { font-size: 13px; color: var(--txt2); margin: 0; }

/* ── UPLOAD ZONE ── */
.sb-upload {
  border: 1.5px dashed var(--bh); border-radius: var(--rl);
  background: var(--s2); text-align: center; padding: 1.75rem 1.25rem;
  transition: all .25s;
}
.sb-upload.loaded {
  border-style: solid; border-color: rgba(52,211,153,.5);
  background: rgba(52,211,153,.04);
}
.sb-upload-icon { font-size: 2rem; margin-bottom: .6rem; }
.sb-upload h3 { font-size: .9rem; font-weight: 600; margin-bottom: 4px; color: var(--txt); }
.sb-upload p  { font-size: 12px; color: var(--txt2); line-height: 1.5; margin: 0; }
.sb-upload .fname { font-size: 12px; color: var(--grn); font-weight: 500; margin-top: 7px; }
.sb-upload .badge {
  display: inline-block; font-size: 10px; font-weight: 700;
  text-transform: uppercase; letter-spacing: .06em;
  background: rgba(52,211,153,.15); color: var(--grn);
  border: 1px solid rgba(52,211,153,.3); padding: 2px 9px;
  border-radius: 20px; margin-top: 7px;
}

/* ── OR DIVIDER ── */
.sb-or {
  display: flex; align-items: center; gap: 1rem; margin: 1.25rem 0;
}
.sb-or-line { flex: 1; height: 1px; background: var(--b); }
.sb-or-txt  { font-size: 11px; color: var(--txt3); font-weight: 600;
              text-transform: uppercase; letter-spacing: .09em; }

/* ── SECTION HEADING ── */
.sb-sh {
  display: flex; align-items: center; gap: 10px;
  font-family: var(--fh); font-size: .8rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .08em;
  color: var(--txt2); margin-bottom: 1rem;
}
.sb-sh::after { content:''; flex:1; height:1px; background:var(--b); }

/* ── STAT STRIP ── */
.sb-stats {
  display: grid; grid-template-columns: repeat(4,1fr);
  gap: 1px; background: var(--b);
  border-radius: var(--rl); overflow: hidden; margin-bottom: 1.25rem;
}
.sb-stat { background: var(--s2); padding: 1rem; text-align: center; }
.sb-stat-n {
  font-family: var(--fh); font-size: 1.8rem; font-weight: 800;
  letter-spacing: -.03em; line-height: 1; margin-bottom: 5px;
}
.sb-stat-l { font-size: 10.5px; color: var(--txt2); text-transform: uppercase; letter-spacing: .07em; }

/* ── PROGRESS BAR ── */
.sb-progress-wrap {
  height: 5px; background: var(--s4);
  border-radius: 3px; overflow: hidden; margin-top: 8px;
}
.sb-progress-fill {
  height: 100%; border-radius: 3px;
  background: linear-gradient(90deg,var(--ind),var(--cya));
  transition: width 1.2s cubic-bezier(.4,0,.2,1);
}

/* ── SKILLS SECTION ── */
.sb-skills-wrap {
  display: grid; grid-template-columns: 1fr 1fr;
  border: 1px solid var(--b); border-radius: var(--rl); overflow: hidden;
  margin-bottom: 1.25rem;
}
.sb-skill-col { padding: 1.25rem; }
.sb-skill-col:first-child { border-right: 1px solid var(--b); }
.sb-skill-col-hd {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .07em; padding-bottom: 8px;
  border-bottom: 1px solid var(--b); margin-bottom: 10px;
  display: flex; align-items: center; justify-content: space-between;
}
.sb-skill-col-hd.grn { color: var(--grn); }
.sb-skill-col-hd.amb { color: var(--amb); }
.sb-skill-col-hd span {
  font-family: var(--fh); font-size: 1.1rem; font-weight: 800;
}
.sb-stag {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 11px; border-radius: var(--r);
  font-size: 13px; margin-bottom: 6px;
}
.sb-stag.have {
  background: rgba(52,211,153,.07); border: 1px solid rgba(52,211,153,.18);
  color: var(--grn);
}
.sb-stag.gap {
  background: rgba(251,191,36,.06); border: 1px solid rgba(251,191,36,.18);
  color: var(--amb);
}

/* ── PATHWAY MODULES ── */
.sb-pathway-item {
  display: flex; gap: 0; margin-bottom: 0;
  animation: slidein .4s ease both;
}
@keyframes slidein { from{opacity:0;transform:translateX(-12px)} to{opacity:1;transform:none} }
.sb-spine {
  display: flex; flex-direction: column; align-items: center;
  width: 50px; flex-shrink: 0; padding-top: 16px;
}
.sb-node {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 800; flex-shrink: 0; z-index: 1;
}
.sb-node.critical   { background:rgba(251,113,133,.12); border:2px solid var(--ros); color:var(--ros); }
.sb-node.important  { background:rgba(251,191,36,.10);  border:2px solid var(--amb); color:var(--amb); }
.sb-node.nice       { background:rgba(34,211,238,.08);  border:2px solid var(--cya); color:var(--cya); }
.sb-node.foundation { background:rgba(99,102,241,.10);  border:2px solid var(--ind); color:var(--ind2); }
.sb-connector {
  flex:1; width:2px; background:var(--b); margin:3px 0; min-height:20px;
}
.sb-mod-body { flex:1; padding: 12px 0 20px 0; }
.sb-module {
  background: var(--s2); border: 1px solid var(--b);
  border-radius: var(--rl); padding: 1.1rem 1.3rem;
  transition: border-color .2s;
}
.sb-module:hover { border-color: var(--bh); }
.sb-mod-top {
  display: flex; align-items: flex-start;
  justify-content: space-between; gap: 12px; margin-bottom: 9px;
}
.sb-mod-title {
  font-family: var(--fh); font-size: .93rem; font-weight: 700;
  letter-spacing: -.015em; color: var(--txt); line-height: 1.3;
}
.sb-badges { display: flex; gap: 6px; flex-wrap: wrap; flex-shrink: 0; }
.sb-badge {
  font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .06em; padding: 3px 8px; border-radius: 20px;
}
.sb-badge.critical   { background:rgba(251,113,133,.12); color:var(--ros); border:1px solid rgba(251,113,133,.25); }
.sb-badge.important  { background:rgba(251,191,36,.10);  color:var(--amb); border:1px solid rgba(251,191,36,.22); }
.sb-badge.nice       { background:rgba(34,211,238,.08);  color:var(--cya); border:1px solid rgba(34,211,238,.20); }
.sb-badge.foundation { background:rgba(99,102,241,.10);  color:var(--ind2);border:1px solid rgba(99,102,241,.22); }
.sb-badge.dur        { background:var(--s3); color:var(--txt2); border:1px solid var(--b); }
.sb-mod-desc { font-size: 13px; color: var(--txt2); line-height: 1.65; margin-bottom: 10px; }
.sb-mod-skills { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.sb-skill-pill {
  font-size: 11px; padding: 3px 10px; border-radius: 20px;
  background: var(--s3); border: 1px solid var(--b); color: var(--txt2);
}
.sb-mod-res {
  display: flex; align-items: center; gap: 7px;
  font-size: 12px; color: var(--txt3);
  padding-top: 10px; border-top: 1px solid var(--b);
}

/* ── REASONING BOX ── */
.sb-reasoning {
  background: var(--s2); border: 1px solid var(--b);
  border-radius: var(--rl); overflow: hidden; margin-bottom: 1.25rem;
}
.sb-reasoning-hd {
  display: flex; align-items: center; gap: 9px;
  padding: .9rem 1.3rem;
  font-size: 13px; font-weight: 600; color: var(--txt2);
}
.sb-reasoning-body {
  padding: 1.1rem 1.3rem; border-top: 1px solid var(--b);
  font-size: 13px; color: var(--txt2);
  line-height: 1.8; white-space: pre-wrap;
}

/* ── LEGEND ── */
.sb-legend {
  display: flex; gap: 16px; flex-wrap: wrap;
  padding-bottom: 1.1rem; border-bottom: 1px solid var(--b); margin-bottom: 1.25rem;
}
.sb-legend-item { display: flex; align-items: center; gap: 7px; font-size: 12px; color: var(--txt2); }
.sb-legend-dot  { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }

/* ── STREAMLIT WIDGET OVERRIDES ── */
.stTextArea > label,
.stTextInput > label,
.stSelectbox > label,
.stSlider > label,
.stMultiSelect > label,
.stFileUploader > label { display: none !important; }

.stTextArea textarea {
  background: var(--s2) !important; color: var(--txt) !important;
  border-color: var(--b) !important; border-radius: var(--r) !important;
  font-family: var(--fb) !important; font-size: 14px !important;
  min-height: 120px !important;
}
.stTextArea textarea:focus { border-color: var(--ind) !important; }
.stTextInput input {
  background: var(--s2) !important; color: var(--txt) !important;
  border-color: var(--b) !important; border-radius: var(--r) !important;
  font-size: 14px !important;
}
.stTextInput input:focus { border-color: var(--ind) !important; }
.stSelectbox [data-baseweb="select"] > div {
  background: var(--s2) !important; border-color: var(--b) !important;
  border-radius: var(--r) !important; color: var(--txt) !important;
}
.stMultiSelect [data-baseweb="select"] > div {
  background: var(--s2) !important; border-color: var(--b) !important;
  border-radius: var(--r) !important;
}
.stSlider [data-baseweb="slider"] { margin-top: .25rem; }
.stSlider [data-testid="stThumbValue"] { color: var(--ind2) !important; }

/* File uploader */
.stFileUploader section {
  background: var(--s2) !important; border: 1.5px dashed var(--bh) !important;
  border-radius: var(--rl) !important; padding: 1.25rem !important;
}
.stFileUploader section:hover { border-color: var(--ind) !important; }
.stFileUploader [data-testid="stFileUploaderDropzone"] p { color: var(--txt2) !important; }

/* Primary button */
.stButton button {
  background: linear-gradient(135deg,var(--ind),#7c3aed) !important;
  color: #fff !important; border: none !important;
  border-radius: var(--r) !important;
  font-family: var(--fb) !important; font-weight: 600 !important;
  font-size: 14px !important; padding: 11px 24px !important;
  transition: all .2s !important;
  box-shadow: 0 4px 20px rgba(99,102,241,.35) !important;
}
.stButton button:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 28px rgba(99,102,241,.5) !important;
}
/* Ghost variant — apply via wrapper div */
div[data-ghost] .stButton button {
  background: var(--s2) !important;
  color: var(--txt2) !important;
  border: 1px solid var(--b) !important;
  box-shadow: none !important;
}
div[data-ghost] .stButton button:hover {
  background: var(--s3) !important;
  color: var(--txt) !important;
  transform: none !important;
}

/* Expander */
.streamlit-expanderHeader {
  background: var(--s2) !important; border-radius: var(--r) !important;
  color: var(--txt2) !important; font-size: 13px !important;
  border: 1px solid var(--b) !important;
}
.streamlit-expanderContent {
  background: var(--s2) !important; border: 1px solid var(--b) !important;
  border-top: none !important; border-radius: 0 0 var(--r) var(--r) !important;
  font-size: 13px !important; color: var(--txt2) !important;
}

/* Info / warning banners */
.stAlert { border-radius: var(--r) !important; }

/* Download button */
.stDownloadButton button {
  background: var(--s2) !important; color: var(--txt2) !important;
  border: 1px solid var(--b) !important; box-shadow: none !important;
}

/* Footer */
.sb-footer {
  border-top: 1px solid var(--b); padding: 1.25rem 2rem;
  display: flex; align-items: center; justify-content: space-between;
  font-size: 12px; color: var(--txt3);
}
.sb-footer-live { display: flex; align-items: center; gap: 7px; }
.sb-footer-dot  {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--grn); animation: blink 2s ease-in-out infinite;
}

/* ── FORM FIELD LABEL ── */
.sb-lbl {
  font-size: 11.5px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .07em; color: var(--txt2); margin-bottom: .35rem;
  display: block;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
#  NAVBAR
# ─────────────────────────────────────────────────────────
st.markdown("""
<div class="sb-nav">
  <div class="sb-logo">
    <div class="sb-logo-mark">🎯</div>
    Skill<em>Bridge</em>
  </div>
  <span class="sb-pill">AI Onboarding Engine</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
#  HERO + STEP BAR
# ─────────────────────────────────────────────────────────
step = st.session_state.step

def step_cls(n):
    if step == n: return "sb-step active"
    if step > n:  return "sb-step done"
    return "sb-step"

def line_cls(n):
    return "sb-sline done" if step > n else "sb-sline"

def circle_content(n):
    return "✓" if step > n else str(n)

st.markdown(f"""
<div class="sb-hero">
  <div class="sb-eyebrow"> AI Powered</div>
  <h1>Personalised Learning,<br/><em>Built for Every Hire</em></h1>
  <p>Upload a resume and job description — our AI maps the exact skills gap and builds a custom training pathway.</p>
  <div class="sb-stepbar">
    <div class="{step_cls(1)}">
      <div class="sb-circle">{circle_content(1)}</div>
      <div class="sb-slabel">Upload</div>
    </div>
    <div class="{line_cls(1)}"></div>
    <div class="{step_cls(2)}">
      <div class="sb-circle">{circle_content(2)}</div>
      <div class="sb-slabel">Configure</div>
    </div>
    <div class="{line_cls(2)}"></div>
    <div class="{step_cls(3)}">
      <div class="sb-circle">{circle_content(3)}</div>
      <div class="sb-slabel">Analyse</div>
    </div>
    <div class="{line_cls(3)}"></div>
    <div class="{step_cls(4)}">
      <div class="sb-circle">{circle_content(4)}</div>
      <div class="sb-slabel">Pathway</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────
#  CONTENT WRAPPER
# ─────────────────────────────────────────────────────────
_, mid, _ = st.columns([1, 6, 1])

with mid:

    # ── ERROR BANNER ──────────────────────────────────────
    if st.session_state.error_message:
        st.info(st.session_state.error_message)

    # ══════════════════════════════════════════════════════
    #  STEP 1 — UPLOAD
    # ══════════════════════════════════════════════════════
    if step == 1:

        # ── Card header ─────────────────────────────────────
        st.markdown("""
        <div class="sb-card">
          <div class="sb-card-hd">
            <div class="sb-hd-icon ind">📄</div>
            <div>
              <h2>Upload Documents</h2>
              <p>Resume + Job Description to extract skills and identify gaps</p>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── File uploaders (inside card visually via columns) ─
        col_r, col_j = st.columns(2)
        with col_r:
            st.markdown('<span class="sb-lbl">Candidate Resume</span>', unsafe_allow_html=True)
            resume_file = st.file_uploader(
                "Resume", type=["pdf", "txt", "docx"],
                key="resume_upload", label_visibility="collapsed"
            )
        with col_j:
            st.markdown('<span class="sb-lbl">Job Description</span>', unsafe_allow_html=True)
            jd_file = st.file_uploader(
                "Job Description", type=["pdf", "txt", "docx"],
                key="jd_upload", label_visibility="collapsed"
            )

        # ── Extract text from files ──────────────────────────
        def _extract(file_obj):
            raw = file_obj.getvalue()
            class _F:
                def __init__(self, name, data):
                    self.name = name
                    self._data = data
                def read(self):
                    return self._data
            return utils.extract_text_from_file(_F(file_obj.name, raw))

        if resume_file is not None:
            if st.session_state.get("resume_file_name") != resume_file.name:
                extracted = _extract(resume_file)
                if extracted.startswith("[ERROR:"):
                    st.warning("⚠️ Could not extract resume text — please paste manually below.")
                elif extracted.strip():
                    st.session_state.resume_text      = extracted
                    st.session_state.resume_file_name = resume_file.name
            st.success(f"✓ Resume loaded: {resume_file.name}")

        if jd_file is not None:
            if st.session_state.get("jd_file_name") != jd_file.name:
                extracted = _extract(jd_file)
                if extracted.startswith("[ERROR:"):
                    st.warning("⚠️ Could not extract job description — please paste manually below.")
                elif extracted.strip():
                    st.session_state.jd_text      = extracted
                    st.session_state.jd_file_name = jd_file.name
            st.success(f"✓ Job description loaded: {jd_file.name}")

        # ── OR divider ───────────────────────────────────────
        st.markdown('<div class="sb-or"><div class="sb-or-line"></div><span class="sb-or-txt">or paste text directly</span><div class="sb-or-line"></div></div>', unsafe_allow_html=True)

        # ── Text areas — NO key= so value= is always respected ──
        col_rt, col_jt = st.columns(2)
        with col_rt:
            st.markdown('<span class="sb-lbl">Resume Text</span>', unsafe_allow_html=True)
            resume_txt = st.text_area(
                "Resume Text",
                value=st.session_state.resume_text,
                height=180,
                placeholder="Paste resume content here…",
                label_visibility="collapsed",
            )
            st.session_state.resume_text = resume_txt

        with col_jt:
            st.markdown('<span class="sb-lbl">Job Description Text</span>', unsafe_allow_html=True)
            jd_txt = st.text_area(
                "Job Description Text",
                value=st.session_state.jd_text,
                height=180,
                placeholder="Paste job description here…",
                label_visibility="collapsed",
            )
            st.session_state.jd_text = jd_txt

        # ── Buttons ──────────────────────────────────────────
        st.markdown("<br/>", unsafe_allow_html=True)
        btn_c1, btn_c2, _ = st.columns([2, 2, 6])
        with btn_c1:
            if st.button("✨ Sample Data", key="btn_sample", use_container_width=True):
                load_sample()
                st.rerun()
        with btn_c2:
            if st.button("Continue →", key="btn_step1_next", use_container_width=True):
                resume_val = st.session_state.resume_text.strip()
                jd_val     = st.session_state.jd_text.strip()
                if not resume_val and not jd_val:
                    st.warning("Please provide both a resume and a job description — upload files or paste text.")
                elif not resume_val:
                    st.warning("Resume is missing — please upload a file or paste the text.")
                elif not jd_val:
                    st.warning("Job description is missing — please upload a file or paste the text.")
                else:
                    go(2)
                    st.rerun()

    # ══════════════════════════════════════════════════════
    #  STEP 2 — CONFIGURE
    # ══════════════════════════════════════════════════════
    elif step == 2:
        st.markdown("""
        <div class="sb-card">
          <div class="sb-card-hd">
            <div class="sb-hd-icon cya">⚙️</div>
            <div>
              <h2>Configure Analysis</h2>
              <p>Customise the pathway to match your organisation and role</p>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<span class="sb-lbl">Industry Domain</span>', unsafe_allow_html=True)
            industry = st.selectbox(
                "industry", label_visibility="collapsed",
                options=["Technology / Software","Data Science / Analytics","Finance / Banking",
                         "Healthcare / MedTech","Operations / Logistics","Marketing / Growth",
                         "Design / UX","HR / People Ops"],
            )
            st.session_state.config["industry"] = industry
        with c2:
            st.markdown('<span class="sb-lbl">Seniority Level</span>', unsafe_allow_html=True)
            seniority = st.selectbox(
                "seniority", label_visibility="collapsed",
                options=["Junior (0–2 years)","Mid-Level (2–5 years)",
                         "Senior (5–10 years)","Lead / Principal (10+ years)"],
                index=1,
            )
            st.session_state.config["seniority"] = seniority

        st.markdown('<span class="sb-lbl">Onboarding Timeline</span>', unsafe_allow_html=True)
        timeline = st.slider("timeline", 2, 16, 8, 2, label_visibility="collapsed",
                             format="%d weeks")
        st.session_state.config["timeline"] = timeline

        st.markdown('<span class="sb-lbl">Learning Preferences</span>', unsafe_allow_html=True)
        prefs = st.multiselect(
            "prefs", label_visibility="collapsed",
            options=["Video Courses","Documentation","Hands-on Labs","Mentorship","Projects"],
            default=["Video Courses","Documentation"],
        )
        st.session_state.config["preferences"] = prefs

        st.markdown('<span class="sb-lbl">Focus Areas (optional)</span>', unsafe_allow_html=True)
        focus = st.multiselect(
            "focus", label_visibility="collapsed",
            options=["Technical Skills","Soft Skills","Domain Knowledge","Tools & Platforms","Compliance"],
            default=[],
        )
        st.session_state.config["focus"] = focus

        st.markdown('<span class="sb-lbl">Course Catalog / Notes (optional)</span>', unsafe_allow_html=True)
        catalog = st.text_area(
            "catalog", label_visibility="collapsed", height=90,
            placeholder="List available courses, LMS platforms or constraints…",
            value=st.session_state.config.get("catalog",""),
        )
        st.session_state.config["catalog"] = catalog

        st.markdown('<span class="sb-lbl">Claude API Key (optional — blank uses demo data)</span>', unsafe_allow_html=True)
        api_key = st.text_input(
            "api_key", label_visibility="collapsed", type="password",
            placeholder="sk-ant-api03-…",
            value=st.session_state.api_key,
        )
        st.session_state.api_key = api_key

        st.markdown("<br/>", unsafe_allow_html=True)
        b1, b2, _ = st.columns([2, 2, 6])
        with b1:
            st.markdown('<div data-ghost>', unsafe_allow_html=True)
            if st.button("← Back", key="btn_step2_back", use_container_width=True):
                go(1); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with b2:
            if st.button("🚀 Generate Pathway", key="btn_generate", use_container_width=True):
                go(3); st.rerun()

    # ══════════════════════════════════════════════════════
    #  STEP 3 — LOADING (animated steps + runs analysis)
    # ══════════════════════════════════════════════════════
    elif step == 3:

        loading_steps = [
            ("ls1", "Parsing resume & extracting skills"),
            ("ls2", "Analysing job description requirements"),
            ("ls3", "Computing skill gap matrix"),
            ("ls4", "Building adaptive pathway graph"),
            ("ls5", "Optimising module sequence"),
            ("ls6", "Generating reasoning trace"),
        ]

        # Determine which step to highlight based on a counter in session state
        if "loading_tick" not in st.session_state:
            st.session_state.loading_tick = 0

        tick = st.session_state.loading_tick
        active_idx = min(tick, len(loading_steps) - 1)

        # ── CSS + card top (no variable injection) ──────────
        st.markdown("""
        <style>
          @keyframes orb-pulse {
            0%,100% { transform:scale(1);   box-shadow:0 0 50px rgba(99,102,241,.45); }
            50%      { transform:scale(1.07); box-shadow:0 0 70px rgba(99,102,241,.65); }
          }
          .ls-item {
            display:flex; align-items:center; gap:12px;
            padding:10px 16px; border-radius:10px;
            font-size:13px; color:#9898b8;
            background:#16161f; border:1px solid rgba(255,255,255,0.06);
            margin-bottom:7px;
          }
          .ls-item.ls-active {
            color:#eeeef8;
            border-color:rgba(99,102,241,.4);
            background:rgba(99,102,241,.08);
          }
          .ls-item.ls-done {
            color:#34d399;
            border-color:rgba(52,211,153,.25);
            background:rgba(52,211,153,.05);
          }
          .ls-dot {
            font-size:15px; width:22px; text-align:center; flex-shrink:0;
          }
        </style>
        <div class="sb-card">
          <div style="display:flex;flex-direction:column;align-items:center;
                      padding:3rem 2rem 1rem;gap:1.5rem;text-align:center;">
            <div style="width:80px;height:80px;border-radius:50%;
                        background:linear-gradient(135deg,#6366f1,#22d3ee);
                        display:flex;align-items:center;justify-content:center;
                        font-size:2.2rem;
                        animation:orb-pulse 2s ease-in-out infinite;">🧠</div>
            <div>
              <div style="font-family:'Syne',sans-serif;font-size:1.15rem;
                          font-weight:800;margin-bottom:5px;color:#eeeef8;">
                Analysing Profile
              </div>
              <div style="font-size:13px;color:#9898b8;">
                Usually takes 15–30 seconds
              </div>
            </div>
          </div>
          <div style="padding:0 2rem 2rem;max-width:480px;margin:0 auto;width:100%;">
        """, unsafe_allow_html=True)

        # ── Each step row rendered individually — no f-string ──
        for i, (_, label) in enumerate(loading_steps):
            if i < active_idx:
                cls, icon = "ls-item ls-done",   "✓"
            elif i == active_idx:
                cls, icon = "ls-item ls-active", "◉"
            else:
                cls, icon = "ls-item",           "○"
            st.markdown(
                f'<div class="{cls}"><span class="ls-dot">{icon}</span><span>{label}</span></div>',
                unsafe_allow_html=True,
            )

        # ── Close card ───────────────────────────────────────
        st.markdown("</div></div>", unsafe_allow_html=True)

        # Advance the tick on each rerun to animate steps, then call API on last tick
        if tick < len(loading_steps) - 1:
            st.session_state.loading_tick += 1
            import time
            time.sleep(0.55)
            st.rerun()
        else:
            # All steps shown — now run actual analysis
            st.session_state.loading_tick = 0  # reset for next time
            run_analysis()
            st.rerun()

    # ══════════════════════════════════════════════════════
    #  STEP 4 — RESULTS  (all rendered via Streamlit widgets)
    # ══════════════════════════════════════════════════════
    elif step == 4:
        data = st.session_state.analysis_result
        if not data:
            st.error("No results found. Please start a new analysis.")
            if st.button("🔄 New Analysis"): go(1); st.rerun()
            st.stop()

        # ── Card header ──────────────────────────────────
        st.markdown(f"""
        <div class="sb-card">
          <div class="sb-card-hd">
            <div class="sb-hd-icon grn">✅</div>
            <div>
              <h2>Personalised Learning Pathway</h2>
              <p>{data.get('candidate_name','Candidate')} → {data.get('role_title','Target Role')}</p>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Stats strip ───────────────────────────────────
        st.markdown(f"""
        <div class="sb-stats">
          <div class="sb-stat">
            <div class="sb-stat-n" style="color:var(--ind2)">{data['overall_readiness']}%</div>
            <div class="sb-stat-l">Role Readiness</div>
          </div>
          <div class="sb-stat">
            <div class="sb-stat-n" style="color:var(--grn)">{data['time_saved_percent']}%</div>
            <div class="sb-stat-l">Training Saved</div>
          </div>
          <div class="sb-stat">
            <div class="sb-stat-n" style="color:var(--cya)">{data['total_weeks']}w</div>
            <div class="sb-stat-l">Timeline</div>
          </div>
          <div class="sb-stat">
            <div class="sb-stat-n" style="color:var(--amb)">{len(data['skills_gap'])}</div>
            <div class="sb-stat-l">Skill Gaps</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Readiness bar ─────────────────────────────────
        pct = data["overall_readiness"]
        st.markdown(f"""
        <div style="background:var(--s2);border:1px solid var(--b);
                    border-radius:var(--rl);padding:1.25rem;margin-bottom:1.1rem;">
          <div class="sb-sh">Overall Role Readiness</div>
          <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:10px;">
            <span style="font-family:var(--fh);font-size:2rem;font-weight:800;
                         letter-spacing:-.03em;color:var(--ind2);">{pct}%</span>
            <span style="font-size:13px;color:var(--txt2);">ready for the target role upon completing pathway</span>
          </div>
          <div class="sb-progress-wrap">
            <div class="sb-progress-fill" style="width:{pct}%"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Skill gap section ─────────────────────────────
        have = data.get("skills_have", [])
        gaps = data.get("skills_gap", [])
        have_html = "".join(f'<div class="sb-stag have"><span>✓</span>{s}</div>' for s in have)
        gap_html  = "".join(f'<div class="sb-stag gap"><span>!</span>{s}</div>'  for s in gaps)

        st.markdown(f"""
        <div class="sb-skills-wrap">
          <div class="sb-skill-col">
            <div class="sb-skill-col-hd grn">✅ Skills Detected <span>{len(have)}</span></div>
            {have_html}
          </div>
          <div class="sb-skill-col">
            <div class="sb-skill-col-hd amb">⚠️ Gaps Identified <span>{len(gaps)}</span></div>
            {gap_html}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Pathway modules (each rendered individually) ──
        st.markdown("""
        <div style="background:var(--s1);border:1px solid var(--b);
                    border-radius:var(--rx);padding:1.75rem;margin-bottom:1.1rem;">
          <div class="sb-sh">Personalised Learning Pathway</div>
          <div class="sb-legend">
            <div class="sb-legend-item"><div class="sb-legend-dot" style="background:var(--ros)"></div>Critical Gap</div>
            <div class="sb-legend-item"><div class="sb-legend-dot" style="background:var(--amb)"></div>Important</div>
            <div class="sb-legend-item"><div class="sb-legend-dot" style="background:var(--cya)"></div>Nice to Have</div>
            <div class="sb-legend-item"><div class="sb-legend-dot" style="background:var(--ind2)"></div>Foundation</div>
          </div>
        """, unsafe_allow_html=True)

        for i, mod in enumerate(data.get("modules", [])):
            p      = mod.get("priority","foundation")
            pills  = "".join(f'<span class="sb-skill-pill">{s}</span>' for s in mod.get("skills_addressed",[]))
            is_last = (i == len(data["modules"]) - 1)
            connector = "" if is_last else '<div class="sb-connector"></div>'

            st.markdown(f"""
            <div class="sb-pathway-item" style="animation-delay:{0.05+i*0.07}s">
              <div class="sb-spine">
                <div class="sb-node {p}">{i+1}</div>
                {connector}
              </div>
              <div class="sb-mod-body">
                <div class="sb-module">
                  <div class="sb-mod-top">
                    <div class="sb-mod-title">{mod['title']}</div>
                    <div class="sb-badges">
                      <span class="sb-badge {p}">{p.upper()}</span>
                      <span class="sb-badge dur">⏱ {mod['duration']}</span>
                    </div>
                  </div>
                  <p class="sb-mod-desc">{mod['description']}</p>
                  <div class="sb-mod-skills">{pills}</div>
                  <div class="sb-mod-res">📚 {mod.get('resources','')}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)  # close pathway card

        # ── Reasoning trace — native Streamlit expander ───
        with st.expander("🧠 AI Reasoning Trace — click to expand"):
            st.markdown(
                f'<div style="font-size:13px;color:var(--txt2);line-height:1.8;white-space:pre-wrap;">'
                f'{data.get("reasoning_trace","No trace available.")}</div>',
                unsafe_allow_html=True,
            )

        # ── Action row — all three as uniform HTML buttons ──
        import base64, urllib.parse

        summary = (
            f"SkillBridge — Personalised Learning Pathway\n"
            f"{'─'*44}\n"
            f"Candidate : {data['candidate_name']}\n"
            f"Role      : {data['role_title']}\n"
            f"Readiness : {data['overall_readiness']}%\n"
            f"Timeline  : {data['total_weeks']} weeks\n"
            f"Saved     : {data['time_saved_percent']}% vs generic\n\n"
            f"SKILL GAPS: {', '.join(data['skills_gap'])}\n\n"
            f"MODULES:\n" +
            "\n".join(
                f"  {i+1}. [{m['priority'].upper()}] {m['title']} — {m['duration']}"
                for i, m in enumerate(data["modules"])
            )
        )
        json_str = json.dumps(data, indent=2)

        # Encode as data URIs so <a href download> works without a server
        summary_b64 = base64.b64encode(summary.encode()).decode()
        json_b64    = base64.b64encode(json_str.encode()).decode()

        st.markdown(f"""
        <style>
          .sb-action-row {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 1.5rem;
            flex-wrap: wrap;
          }}
          .sb-action-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-family: var(--fb);
            font-size: 14px;
            font-weight: 600;
            padding: 11px 22px;
            border-radius: 10px;
            border: none;
            cursor: pointer;
            text-decoration: none !important;
            transition: all 0.2s ease;
            white-space: nowrap;
            line-height: 1;
            background: linear-gradient(135deg, var(--ind), #7c3aed);
            color: #fff !important;
            box-shadow: 0 4px 20px rgba(99,102,241,0.35);
          }}
          .sb-action-btn:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 28px rgba(99,102,241,0.5);
            color: #fff !important;
          }}
        </style>
        <div class="sb-action-row">
          <a class="sb-action-btn"
             href="data:text/plain;base64,{summary_b64}"
             download="skillbridge-summary.txt">
            📋 Copy Summary
          </a>
          <a class="sb-action-btn"
             href="data:application/json;base64,{json_b64}"
             download="skillbridge-pathway.json">
            ⬇️ Export JSON
          </a>
        </div>
        """, unsafe_allow_html=True)

        # New Analysis — plain Streamlit button, no query_params needed
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("🔄 New Analysis", key="btn_new", use_container_width=False):
            go(1)
            st.session_state.analysis_result = None
            st.rerun()

# ─────────────────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────────────────
st.markdown("""
<div class="sb-footer">
  <div class="sb-footer-live">
    <div class="sb-footer-dot"></div>
    SkillBridge v1.0 — AI Adaptive Onboarding Engine
""", unsafe_allow_html=True)