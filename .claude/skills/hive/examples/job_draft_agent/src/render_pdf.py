import shutil
import subprocess
from pathlib import Path


def compile_latex(tex_path: str, build_dir: str, final_dir: str) -> Path:
    build_dir_path = Path(build_dir)
    final_dir_path = Path(final_dir)

    build_dir_path.mkdir(parents=True, exist_ok=True)
    final_dir_path.mkdir(parents=True, exist_ok=True)

    pdflatex_path = shutil.which("pdflatex")
    if pdflatex_path is None:
        raise RuntimeError("pdflatex was not found on your system PATH.")

    tex_path_obj = Path(tex_path)
    expected_pdf = build_dir_path / f"{tex_path_obj.stem}.pdf"

    cmd = [
        pdflatex_path,
        "-interaction=nonstopmode",
        f"-output-directory={build_dir}",
        tex_path,
    ]

    for i in range(2):
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[pdflatex warning] Pass {i + 1} returned code {result.returncode}")
            print(result.stdout)
            print(result.stderr)

    if not expected_pdf.exists():
        raise RuntimeError(f"LaTeX compilation did not produce a PDF for {tex_path}.")

    final_pdf = final_dir_path / expected_pdf.name
    if expected_pdf.resolve() != final_pdf.resolve():
        shutil.copy2(expected_pdf, final_pdf)

    print(f"PDF generated successfully: {final_pdf}")
    return final_pdf
