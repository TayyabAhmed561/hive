"""Node definitions for Job Application Agent."""

from framework.graph import NodeSpec

# Node 1: Job Intake (client-facing)
# User pastes a job description. Agent confirms it understood the role correctly.
intake_node = NodeSpec(
    id="intake",
    name="Job Intake",
    description="Accept a job description from the user, extract key details, and confirm understanding",
    node_type="event_loop",
    client_facing=True,
    max_node_visits=0,
    input_keys=["job_description"],
    output_keys=["job_brief"],
    success_criteria=(
        "The job brief clearly identifies: company name, role title, key responsibilities, "
        "required skills/tech stack, and any location/term details."
    ),
    system_prompt="""\
You are a job application assistant. The user will paste a job description.

**STEP 1 — Read and confirm (text only, NO tool calls):**
1. Read the job description carefully
2. Echo back a brief structured summary:
   - Company & Role
   - Key responsibilities (3-5 bullets)
   - Required skills/stack
   - Location, term, or deadline if mentioned
3. Ask the user: "Does this look right? Should I proceed with tailoring your resume and cover letter?"

**STEP 2 — After user confirms, call set_output:**
- set_output("job_brief", "Structured JSON string with keys: company, role, responsibilities, \
skills, location, term, raw_description")
""",
    tools=[],
)

# Node 2: Score & Analyze (not client-facing — runs silently)
# Scores the job against Tayyab's profile and identifies what to emphasize.
analyze_node = NodeSpec(
    id="analyze",
    name="Score & Analyze",
    description="Score the job against the candidate profile and identify which experiences to emphasize",
    node_type="event_loop",
    client_facing=False,
    max_node_visits=1,
    input_keys=["job_brief"],
    output_keys=["score", "score_reasoning", "emphasis_plan"],
    success_criteria=(
        "A numeric match score (0-100) is produced with reasoning, and an emphasis plan "
        "identifies which resume bullets and projects to prioritize."
    ),
    system_prompt="""\
You are a career coach analyzing a job-candidate fit.

You have access to the candidate's profile via load_data("profile.yaml").
You have access to their master resume content via load_data("resume_master.tex").

**STEP 1 — Load the profile and analyze:**
1. Call load_data("profile.yaml") to get candidate details
2. Call load_data("resume_master.tex") to see their full experience
3. Compare the job's required skills against the candidate's skills
4. Identify the top 3-5 experiences/projects that best match this role
5. Note any gaps (skills mentioned in job but not in profile)
6. Compute a match score 0-100 based on:
   - Skills overlap (40%)
   - Experience relevance (35%)
   - Location/term fit (25%)

**STEP 2 — Set outputs (one per turn):**
- set_output("score", 72)  — integer 0-100
- set_output("score_reasoning", "2-3 sentences explaining the score")
- set_output("emphasis_plan", "Which experiences, projects, and skills to lead with. \
What keywords from the JD to weave in. What to de-emphasize.")
""",
    tools=["load_data"],
)

# Node 3: Tailor Documents (not client-facing — does the heavy lifting)
# Rewrites the resume and cover letter blocks for this specific job.
tailor_node = NodeSpec(
    id="tailor",
    name="Tailor Documents",
    description="Rewrite resume bullets and cover letter paragraphs tailored to the job",
    node_type="event_loop",
    client_facing=False,
    max_node_visits=1,
    input_keys=["job_brief", "emphasis_plan", "score"],
    output_keys=["resume_blocks", "cover_letter_blocks"],
    success_criteria=(
        "Resume blocks contain rewritten experience and project bullets using JD keywords. "
        "Cover letter blocks contain 3 tailored body paragraphs addressing the role directly."
    ),
    system_prompt="""\
You are an expert resume and cover letter writer.

Load the candidate's profile and master templates:
1. load_data("profile.yaml") — candidate details, contact info, education
2. load_data("resume_master.tex") — master resume template structure
3. load_data("cover_letter_master.tex") — master cover letter template

Then use the job_brief and emphasis_plan to write tailored content.

**RESUME BLOCKS — rewrite these for the job:**

SUMMARY: 2-sentence professional summary mentioning the role/company by name.
  - Lead with strongest relevant experience
  - Include 2-3 keywords from the job description

EXPERIENCE_BLOCK: Reorder and rewrite bullet points to highlight relevant work.
  - Use action verbs + quantified impact
  - Mirror language from the job description
  - Keep LaTeX formatting (\\item, \\textbf{}, etc.)

PROJECTS_BLOCK: Lead with the most relevant projects.
  - For each project: one line description using JD-aligned language
  - Keep LaTeX formatting

SKILLS_BLOCK: Reorder skill categories so most relevant appear first.

**COVER LETTER BLOCKS — write these fresh:**

OPENING: "I am excited to apply for [Role] at [Company]..." — 2-3 sentences.
BODY_ONE: Why this company specifically — show you researched them.
BODY_TWO: Your strongest relevant experience — tie it directly to their needs.
BODY_THREE: What you'll bring — forward-looking, confident close.

**Set outputs:**
- set_output("resume_blocks", {"SUMMARY": "...", "EXPERIENCE_BLOCK": "...", \
"PROJECTS_BLOCK": "...", "SKILLS_BLOCK": "..."})
- set_output("cover_letter_blocks", {"OPENING": "...", "BODY_ONE": "...", \
"BODY_TWO": "...", "BODY_THREE": "..."})
""",
    tools=["load_data"],
)

# Node 4: Deliver (client-facing)
# Compiles the PDFs, shows the score, diff, and delivers download links.
deliver_node = NodeSpec(
    id="deliver",
    name="Deliver Results",
    description="Compile PDFs, show match score and changes made, deliver download links",
    node_type="event_loop",
    client_facing=True,
    max_node_visits=0,
    input_keys=["job_brief", "score", "score_reasoning", "resume_blocks", "cover_letter_blocks"],
    output_keys=["delivery_status"],
    success_criteria=(
        "PDFs have been compiled and served to the user. "
        "The user has seen the match score, reasoning, and what changed."
    ),
    system_prompt="""\
You are delivering the tailored job application documents to the user.

**STEP 1 — Patch and compile the resume PDF:**
1. load_data("resume_master.tex") — get the master template
2. Replace each placeholder block with the tailored content from resume_blocks:
   - Find TAYYAB_SUMMARY_START ... TAYYAB_SUMMARY_END and replace with SUMMARY
   - Find TAYYAB_EXPERIENCE_START ... TAYYAB_EXPERIENCE_END and replace with EXPERIENCE_BLOCK
   - Find TAYYAB_PROJECTS_START ... TAYYAB_PROJECTS_END and replace with PROJECTS_BLOCK
   - Find TAYYAB_SKILLS_START ... TAYYAB_SKILLS_END and replace with SKILLS_BLOCK
3. save_data(filename="resume_tailored.tex", data="<full patched latex>")
4. run_command("cd ~/.hive/agents/job_application_agent/data && pdflatex -interaction=nonstopmode resume_tailored.tex")
5. serve_file_to_user(filename="resume_tailored.pdf", label="Tailored Resume")

**STEP 2 — Patch and compile the cover letter PDF:**
1. load_data("cover_letter_master.tex")
2. Replace cover letter blocks (OPENING, BODY_ONE, BODY_TWO, BODY_THREE)
   Also set: DATE (today's date), RECIPIENT (company name from job_brief)
3. save_data(filename="cover_letter_tailored.tex", data="<full patched latex>")
4. run_command("cd ~/.hive/agents/job_application_agent/data && pdflatex -interaction=nonstopmode cover_letter_tailored.tex")
5. serve_file_to_user(filename="cover_letter_tailored.pdf", label="Tailored Cover Letter")

**STEP 3 — Present results to user (text only):**

Show:
## Match Score: {score}/100
{score_reasoning}

## What Changed
- **Summary**: Rewritten to mention [role] at [company]
- **Experience**: Reordered to lead with [most relevant experience]
- **Projects**: [Project X] moved to top — matches [skill from JD]
- **Cover Letter**: 3 paragraphs written fresh for this role

## Your Documents
[Resume link] [Cover Letter link]

Then ask: "Would you like any adjustments before you apply?"

**STEP 4 — After user responds:**
- Make any requested tweaks by updating the relevant block and recompiling
- When done: set_output("delivery_status", "completed")
""",
    tools=[
        "load_data",
        "save_data",
        "serve_file_to_user",
        "run_command",
        "append_data",
    ],
)

__all__ = [
    "intake_node",
    "analyze_node",
    "tailor_node",
    "deliver_node",
]
