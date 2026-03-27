from pathlib import Path

from latex_patch import patch_file
from render_pdf import compile_latex
from parse_job import parse_job
from score_job import score_job
from utils import slugify, load_profile


BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
INPUTS_DIR = BASE_DIR / "inputs" / "jobs"
OUT_ROOT = BASE_DIR / "out"
CONFIG_DIR = BASE_DIR / "config"



def build_experience_block(keywords: set[str]) -> str:
    verismo = r"""
\resumeSubheading{Machine Learning Engineer}{May 2025 -- Present}{Verismo AI}{Hybrid - Toronto, ON}
\resumeItemListStart
  \resumeItem{Designed and evaluated end-to-end machine learning pipelines in \textbf{Python} and \textbf{PyTorch} from problem definition through validation.}
  \resumeItem{Engineered scalable \textbf{data ingestion and preprocessing pipelines} for microscopy datasets in collaboration with lab researchers.}
  \resumeItem{Led structured experiments using \textbf{cross-validation} and quantitative error analysis to validate performance across model variants.}
  \resumeItem{Owned model evaluation strategy and performance benchmarking, iterating based on empirical results and deployment constraints.}
\resumeItemListEnd
"""

    gdsc = r"""
\resumeSubheading{Google Developer Student Club (GDSC) – University of Guelph}{2024 -- Present}{Events Organizer \& Technical Contributor}{Guelph, ON}
\resumeItemListStart
  \resumeItem{Co-organized technical workshops and speaker events on \textbf{machine learning}, \textbf{cloud systems}, and \textbf{applied AI}, engaging 100+ students.}
  \resumeItem{Contributed to technical planning and curriculum design for sessions covering \textbf{Python}, \textbf{API development}, and ML fundamentals.}
  \resumeItem{Collaborated with student teams to foster a research-oriented and product-building community on campus.}
\resumeItemListEnd
"""

    gryphon = r"""
\resumeSubheading{Embedded Systems Developer (Formula SAE EV)}{2026 -- Present}{Gryphon Racing}{Guelph, ON}
\resumeItemListStart
\resumeItem{Developing embedded software for EV subsystems using microcontrollers and real-time sensor data acquisition.}
\resumeItem{Implementing low-latency processing and safety-aware control logic under performance and reliability constraints.}
\resumeItem{Collaborating across electrical and mechanical teams to ensure robust hardware-software system integration.}
\resumeItemListEnd
"""

    geotab = r"""
\resumeSubheading{Software Engineering Intern}{May 2021 -- Aug 2021}{Geotab}{Waterloo, ON}
\resumeItemListStart
 \resumeItem{Observed and analyzed large-scale \textbf{cloud ingestion} systems processing \textbf{30+ TB/day} of telematics data.}
 \resumeItem{Collaborated with engineers using \textbf{C\#, .NET Core, and SQL}, gaining insight into enterprise software design and system reliability.}
\resumeItemListEnd
"""

    stemotics = r"""
\resumeSubheading{Technical Mentor}{July 2022 -- Dec 2025}{STEMOTICS / FIRST Robotics Canada}{Cambridge, ON}
\resumeItemListStart
  \resumeItem{Led 20+ workshops on \textbf{embedded systems} and \textbf{IoT}, mentoring students in robotics, navigation, and structured debugging.}
  \resumeItem{Coached a team to \textbf{2nd place out of 15 teams} at a \textbf{FIRST LEGO League competition} hosted at the University of Waterloo.}
\resumeItemListEnd
"""

    ordered = [verismo]

    if {"embedded systems", "c++"} & keywords:
        ordered += [gryphon, geotab, gdsc, stemotics]
    elif {"machine learning", "evaluation", "multimodal", "llms", "nlp"} & keywords:
        ordered += [gdsc, geotab, gryphon, stemotics]
    else:
        ordered += [gdsc, gryphon, geotab, stemotics]

    return "\n\n".join(ordered)


def build_projects_block(keywords: set[str]) -> str:
    mindsync = r"""
\resumeSubheading{MindSync - EEG-Based Therapy Decision Support System}{Jan, 2025}{}{}
\resumeItemListStart
  \resumeItem{Designed and \textbf{trained deep learning models} for noisy physiological time-series data under constrained sample conditions.}
  \resumeItem{Built structured \textbf{preprocessing} and \textbf{feature extraction pipelines} for high-variance signal inputs.}
  \resumeItem{Optimized inference workflow for low-latency decision support integration.}
\resumeItemListEnd
"""

    safesteps = r"""
\resumeSubheading{SafeSteps - Pedestrian Safety System}{Feb, 2025}{}{}
\resumeItemListStart
  \resumeItem{Developed a \textbf{data-driven safety platform} integrating real-time hazard reports with geospatial data to support safer routing decisions.}
  \resumeItem{Engineered \textbf{location-based analytics and routing logic} to prioritize hazards based on severity, frequency, and historical trends.}
  \resumeItem{Built feature-based classification and ranking models to prioritize hazards using severity, frequency, and historical data patterns.}
\resumeItemListEnd
"""

    esv = r"""
\resumeSubheading{ESV (Endangered Species Visualized)}{June, 2025}{}{}
\resumeItemListStart
  \resumeItem{Built a \textbf{data visualization platform} to explore large geospatial datasets and communicate regional biodiversity trends.}
  \resumeItem{Implemented interactive map layers, heatmaps, and spatial filters to enable \textbf{exploratory data analysis} across Ontario.}
  \resumeItem{Designed scalable frontend components to support clear communication of insights to non-technical audiences.}
\resumeItemListEnd
"""

    ums = r"""
\resumeSubheading{University Management System – Fullstack Java Cloud Application}{Jan--Apr 2025}{}{}
\resumeItemListStart
  \resumeItem{Developed a modular \textbf{Java} fullstack application using \textbf{FXML}, OOP design principles, and RESTful architecture.}
  \resumeItem{Designed and deployed a cloud-backed data layer using \textbf{AWS EC2} and \textbf{MySQL (RDS)} with structured schema modeling.}
  \resumeItem{Implemented logging, validation, and error-handling mechanisms to ensure reliability and maintainability.}
\resumeItemListEnd
"""

    if {"multimodal", "machine learning", "evaluation", "llms", "nlp"} & keywords:
        ordered = [mindsync, safesteps, esv, ums]
    elif {"data pipelines", "sql"} & keywords:
        ordered = [ums, esv, safesteps, mindsync]
    else:
        ordered = [mindsync, safesteps, esv, ums]

    return "\n\n".join(ordered)



def build_resume_replacements(job: dict, profile: dict) -> dict[str, str]:
    keywords = set(job.get("keywords", []))

    emphasis = []
    if "evaluation" in keywords:
        emphasis.append("evaluation")
    if "multimodal" in keywords:
        emphasis.append("multimodal learning")
    if "llms" in keywords or "nlp" in keywords:
        emphasis.append("language model applications")
    if "pytorch" in keywords:
        emphasis.append("PyTorch systems")

    emphasis_text = ", ".join(emphasis[:3])
    if emphasis_text:
        emphasis_text = f" with interest in {emphasis_text}"

    summary = (
        "Data-focused machine learning engineer experienced in building end-to-end modeling pipelines "
        "and running structured experiments on real-world datasets. Strong foundation in statistical "
        "evaluation, cross-validation, and translating research problems into measurable insights."
    )

    experience_block = build_experience_block(keywords)
    projects_block = build_projects_block(keywords)

    return {
        "SUMMARY": summary,
        "EXPERIENCE_BLOCK": experience_block,
        "PROJECTS_BLOCK": projects_block,
    }


def build_cover_replacements(job: dict, profile: dict) -> dict[str, str]:
    company = job["company"]
    title = job["title"]
    location = job["location"]
    keywords = set(job.get("keywords", []))

    role_focus = []
    if "llms" in keywords or "nlp" in keywords:
        role_focus.append("language models")
    if "evaluation" in keywords:
        role_focus.append("evaluation")
    if "multimodal" in keywords:
        role_focus.append("multimodal systems")
    if "distributed training" in keywords:
        role_focus.append("scalable training systems")

    if role_focus:
        focus_text = ", ".join(role_focus[:3])
        opening = (
            f"I am writing to apply for the {title} position at {company}. "
            f"The opportunity to contribute to {focus_text} strongly aligns with the direction "
            f"I am building toward as a computer engineering student focused on machine learning systems. "
            f"{company}'s emphasis on building practical, production-grade systems that solve real problems "
            f"makes this role particularly compelling to me, and I am eager to contribute to that mission "
            f"in a meaningful way."
        )
    else:
        opening = (
            f"I am writing to apply for the {title} position at {company}. "
            f"The opportunity to contribute to machine learning systems, evaluation, and applied AI development "
            f"strongly aligns with the direction I am building toward as a computer engineering student focused "
            f"on machine learning systems. {company}'s emphasis on building practical systems that solve real "
            f"problems makes this role particularly compelling to me, and I am eager to contribute meaningfully."
        )

    return {
        "RECIPIENT": f"Hiring Team\n{company}\n{location}",
        "SALUTATION": "Dear Hiring Team,",
        "OPENING": opening,
        "BODY_ONE": (
            "At Verismo AI, I lead the development of applied machine learning systems from problem "
            "formulation through training, validation, and evaluation. I design reproducible "
            "experimentation pipelines in Python and PyTorch, construct data preprocessing workflows, "
            "and systematically compare model architectures through structured experiments and "
            "quantitative analysis. This work has sharpened my ability to move quickly from a research "
            "question to an empirical result while maintaining rigor in how I measure and report "
            "performance. I have learned to treat evaluation not as a final step but as a continuous "
            "discipline embedded throughout the development process."
        ),
        "BODY_TWO": (
            "In parallel, my background in computer engineering has given me practical experience "
            "working across software and hardware layers. I have built systems in C and C++, worked "
            "with embedded platforms, and reasoned about performance trade-offs such as latency, memory "
            "constraints, and system throughput. This cross-layer perspective helps me understand not "
            "just how a model performs in isolation, but how it fits within the broader system it "
            "operates in. I find that thinking at multiple levels of abstraction simultaneously leads "
            "to better engineering decisions and more robust systems overall."
        ),
        "BODY_THREE": (
            "Beyond technical development, I place strong emphasis on communicating research and "
            "engineering work clearly. I regularly document experiments, summarize findings, and present "
            "results in structured formats that allow teams to iterate quickly and build on prior work. "
            "I believe that disciplined documentation and clear communication are just as important as "
            "the technical work itself, particularly in a research environment where reproducibility and "
            "shared understanding directly accelerate progress. Working collaboratively across teams "
            "while maintaining individual ownership has been a consistent part of how I operate."
        ),
        "CLOSING": (
            f"I am excited by the opportunity to contribute to {company}'s work through a role like "
            f"{title}. I bring a combination of hands-on ML engineering experience, a strong systems "
            f"foundation, and a genuine interest in how machine learning systems are built, evaluated, "
            f"and improved at scale. I believe my experience building machine learning pipelines and "
            f"thinking across the full system stack would allow me to contribute meaningfully from day "
            f"one and grow significantly through the work.\n\n"
            "Thank you for your consideration. I would welcome the opportunity to further discuss "
            "how my background in machine learning systems and experimentation could contribute to your team."
        ),
        "SIGNOFF": "Sincerely,",
        "NAME": "Tayyab Ahmed",
    }


def write_notes(job: dict, out_dir: Path) -> None:
    notes = f"""# Application Notes

## Company
{job['company']}

## Role
{job['title']}

## Location
{job['location']}

## Score
{job['score']}/100

## Source File
{job.get('source_file', 'Unknown')}

## Skill Matches
{", ".join(job.get('skill_matches', [])) or "None"}

## Interest Matches
{", ".join(job.get('interest_matches', [])) or "None"}

## Penalties Applied
{chr(10).join(job.get('penalties_applied', [])) or "None"}

## Keywords Found
{", ".join(job['keywords']) if job['keywords'] else "None"}
"""
    (out_dir / "notes.md").write_text(notes, encoding="utf-8")


def write_rankings(scored_jobs: list[dict], out_root: Path) -> None:
    lines = ["# Ranked Job Matches", ""]
    for idx, job in enumerate(scored_jobs, start=1):
        lines.append(f"## {idx}. {job['company']} | {job['title']} | {job['score']}/100")
        lines.append(f"- Source file: {job.get('source_file', 'Unknown')}")
        lines.append(f"- Location: {job.get('location', 'Unknown')}")
        lines.append(f"- Skill matches: {', '.join(job.get('skill_matches', [])) or 'None'}")
        lines.append(f"- Interest matches: {', '.join(job.get('interest_matches', [])) or 'None'}")
        lines.append(f"- Penalties: {', '.join(job.get('penalties_applied', [])) or 'None'}")
        lines.append("")

    (out_root / "rankings.md").write_text("\n".join(lines), encoding="utf-8")


def write_changes(job: dict, out_dir: Path) -> None:
    lines = [
        "# Change Summary",
        "",
        "## Resume",
        "- Updated summary to align with the selected role and company.",
        "- Reordered experience entries based on matched job keywords.",
        "- Reordered projects to emphasize the most relevant work first.",
        "",
        "## Cover Letter",
        "- Updated recipient and salutation for the company.",
        "- Tailored opening paragraph to the job title and company.",
        "- Kept body focused on machine learning systems, experimentation, and engineering depth.",
        "",
        "## Match Signals",
        f"- Skill matches: {', '.join(job.get('skill_matches', [])) or 'None'}",
        f"- Interest matches: {', '.join(job.get('interest_matches', [])) or 'None'}",
        f"- Penalties: {', '.join(job.get('penalties_applied', [])) or 'None'}",
    ]
    (out_dir / "changes.md").write_text("\n".join(lines), encoding="utf-8")


def generate_pack(job: dict, profile: dict) -> None:
    slug = slugify(f"{job['company']}_{job['title']}")

    out_dir = OUT_ROOT / slug
    final_dir = out_dir / "final"
    build_dir = out_dir / "build"

    final_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    resume_in = ASSETS_DIR / "resume_master.tex"
    cover_in = ASSETS_DIR / "cover_letter_master.tex"

    resume_out = final_dir / f"resume_{slug}.tex"
    cover_out = final_dir / f"cover_letter_{slug}.tex"

    resume_replacements = build_resume_replacements(job, profile)
    cover_replacements = build_cover_replacements(job, profile)
    write_changes(job, final_dir)
    print(f"\nGenerating pack for: {job['company']} | {job['title']} | {job['score']}/100")

    patch_file(str(resume_in), str(resume_out), resume_replacements)
    patch_file(str(cover_in), str(cover_out), cover_replacements)

    compile_latex(str(resume_out), str(build_dir), str(final_dir))
    compile_latex(str(cover_out), str(build_dir), str(final_dir))

    write_notes(job, final_dir)


def main():
    profile = load_profile(CONFIG_DIR / "profile.yaml")

    job_files = sorted(INPUTS_DIR.glob("*.txt"))
    if not job_files:
        raise FileNotFoundError(f"No job description files found in {INPUTS_DIR}")

    scored_jobs = []
    for job_file in job_files:
        raw_text = job_file.read_text(encoding="utf-8")
        parsed_job = parse_job(raw_text)
        parsed_job["source_file"] = job_file.name
        scored_job = score_job(parsed_job, profile)
        scored_jobs.append(scored_job)

    scored_jobs.sort(key=lambda job: job["score"], reverse=True)

    print("Ranked jobs:")
    for job in scored_jobs:
        print(f" - {job['company']} | {job['title']} | {job['score']}/100")

    write_rankings(scored_jobs, OUT_ROOT)

    threshold = 45
    top_n = 3
    selected_jobs = [job for job in scored_jobs[:top_n] if job["score"] >= threshold]

    if not selected_jobs:
        print("No jobs met the threshold for draft generation.")
        return

    for job in selected_jobs:
        generate_pack(job, profile)

    print(f"\nDone. Rankings written to: {OUT_ROOT / 'rankings.md'}")


if __name__ == "__main__":
    main()
