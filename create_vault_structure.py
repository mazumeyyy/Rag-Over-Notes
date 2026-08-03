"""
Parse the B.Sc. CSIT syllabus and create folder structure for
all subjects and their units.

SKIPS:
- Semester 1 / CSC114 Introduction to IT (completed)
- Semester 1 / CSC115 C Programming (completed)
- Semester 1 / CSC116 Digital Logic Units 1-3 (completed, creates 4-7)
"""

import os
import re
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DATA_DIR = r"c:\Users\Mazum Paudel\rag-vault\data"
PDF_TEXT = r"c:\Users\Mazum Paudel\rag-vault\pdf_extracted_text.txt"

# ── Manually curated subject list from the syllabus ──────────────────────
# Format: (semester, course_code, folder_name, [list of (unit_num, unit_title)])
# We'll parse units from the text file automatically.

# Map course titles to (semester, code, folder_name)
COURSE_MAP = [
    # Semester I
    (1, "CSC114", "CSC114_Introduction_to_IT",            "Introduction to Information Technology",  "COMPLETED"),
    (1, "CSC115", "CSC115_C_Programming",                 "C Programming",                          "COMPLETED"),
    (1, "CSC116", "CSC116_Digital_Logic",                  "Digital Logic",                          "PARTIAL:3"),  # Units 1-3 done
    (1, "MTH117", "MTH117_Mathematics_I",                  "Mathematics I",                          "TODO"),
    (1, "PHY118", "PHY118_Physics",                        "Physics",                                "TODO"),

    # Semester II
    (2, "CSC165", "CSC165_Discrete_Structure",             "Discrete Structures",                    "TODO"),
    (2, "CSC166", "CSC166_Object_Oriented_Programming",    "Object Oriented Programming",            "TODO"),
    (2, "CSC167", "CSC167_Microprocessor",                 "Microprocessor",                         "TODO"),
    (2, "MTH168", "MTH168_Mathematics_II",                 "Mathematics II",                         "TODO"),
    (2, "STA169", "STA169_Statistics_I",                   "Statistics I",                           "TODO"),

    # Semester III
    (3, "CSC211", "CSC211_Data_Structures_and_Algorithms", "Data Structures and Algorithms",         "TODO"),
    (3, "CSC212", "CSC212_Numerical_Method",               "Numerical Method",                       "TODO"),
    (3, "CSC213", "CSC213_Computer_Architecture",          "Computer Architecture",                  "TODO"),
    (3, "CSC214", "CSC214_Computer_Graphics",              "Computer Graphics",                      "TODO"),
    (3, "STA215", "STA215_Statistics_II",                  "Statistics II",                          "TODO"),

    # Semester IV
    (4, "CSC262", "CSC262_Theory_of_Computation",          "Theory of Computation",                  "TODO"),
    (4, "CSC263", "CSC263_Computer_Networks",               "Computer Networks",                      "TODO"),
    (4, "CSC264", "CSC264_Operating_Systems",              "Operating Systems",                      "TODO"),
    (4, "CSC265", "CSC265_Database_Management_System",     "Database Management System",             "TODO"),
    (4, "CSC266", "CSC266_Artificial_Intelligence",        "Artificial Intelligence",                "TODO"),

    # Semester V
    (5, "CSC325", "CSC325_Design_and_Analysis_of_Algorithms", "Design and Analysis of Algorithms",  "TODO"),
    (5, "CSC326", "CSC326_System_Analysis_and_Design",     "System Analysis and Design",             "TODO"),
    (5, "CSC327", "CSC327_Cryptography",                   "Cryptography",                           "TODO"),
    (5, "CSC328", "CSC328_Simulation_and_Modeling",        "Simulation and Modeling",                "TODO"),
    (5, "CSC329", "CSC329_Web_Technology",                 "Web Technology",                         "TODO"),
    # Electives
    (5, "CSC330", "CSC330_Multimedia_Computing",            "Multimedia Computing",                  "TODO"),
    (5, "CSC331", "CSC331_Wireless_Networking",             "Wireless Networking",                   "TODO"),
    (5, "CSC332", "CSC332_Image_Processing",                "Image Processing",                     "TODO"),
    (5, "CSC333", "CSC333_Knowledge_Management",            "Knowledge Management",                 "TODO"),
    (5, "CSC334", "CSC334_Society_and_Ethics_in_IT",        "Society and Ethics in Information Technology", "TODO"),
    (5, "CSC335", "CSC335_Microprocessor_Based_Design",     "Microprocessor Based Design",          "TODO"),

    # Semester VI
    (6, "CSC375", "CSC375_Software_Engineering",           "Software Engineering",                   "TODO"),
    (6, "CSC376", "CSC376_Compiler_Design_and_Construction","Compiler Design and Construction",      "TODO"),
    (6, "CSC377", "CSC377_E_Governance",                   "E-Governance",                           "TODO"),
    (6, "CSC378", "CSC378_NET_Centric_Computing",          "NET Centric Computing",                  "TODO"),
    (6, "CSC379", "CSC379_Technical_Writing",              "Technical Writing",                      "TODO"),
    # Electives
    (6, "CSC380", "CSC380_Applied_Logic",                   "Applied Logic",                        "TODO"),
    (6, "CSC381", "CSC381_E_Commerce",                      "E-Commerce",                           "TODO"),
    (6, "CSC382", "CSC382_Automation_and_Robotics",         "Automation and Robotics",              "TODO"),
    (6, "CSC383", "CSC383_Neural_Networks",                 "Neural Networks",                      "TODO"),
    (6, "CSC384", "CSC384_Computer_Hardware_Design",        "Computer Hardware Design",             "TODO"),
    (6, "CSC385", "CSC385_Cognitive_Science",               "Cognitive Science",                    "TODO"),

    # Semester VII
    (7, "CSC419", "CSC419_Advanced_Java_Programming",      "Advanced Java Programming",              "TODO"),
    (7, "CSC420", "CSC420_Data_Warehousing_and_Data_Mining","Data Warehousing and Data Mining",       "TODO"),
    (7, "MGT421", "MGT421_Principles_of_Management",       "Principles of Management",              "TODO"),
    (7, "CSC422", "CSC422_Project_Work",                   "Project Work",                           "TODO"),
    # Electives
    (7, "CSC423", "CSC423_Information_Retrieval",           "Information Retrieval",                 "TODO"),
    (7, "CSC424", "CSC424_Database_Administration",         "Database Administration",              "TODO"),
    (7, "CSC425", "CSC425_Software_Project_Management",     "Software Project Management",          "TODO"),
    (7, "CSC426", "CSC426_Network_Security",                "Network Security",                     "TODO"),
    (7, "CSC427", "CSC427_Digital_System_Design",           "Digital System Design",                "TODO"),
    (7, "MGT428", "MGT428_International_Marketing",         "International Marketing",              "TODO"),

    # Semester VIII
    (8, "CSC475", "CSC475_Advanced_Database",              "Advanced Database",                      "TODO"),
    (8, "CSC476", "CSC476_Internship",                     "Internship",                             "TODO"),
    # Electives
    (8, "CSC477", "CSC477_Advanced_Networking_with_IPv6",   "Advanced Networking with IPv6",         "TODO"),
    (8, "CSC478", "CSC478_Distributed_Networking",          "Distributed Networking",               "TODO"),
    (8, "CSC479", "CSC479_Game_Technology",                 "Game Technology",                      "TODO"),
    (8, "CSC480", "CSC480_Distributed_and_OO_Database",     "Distributed and Object Oriented Database","TODO"),
    (8, "CSC481", "CSC481_Introduction_to_Cloud_Computing", "Introduction to Cloud Computing",      "TODO"),
    (8, "CSC482", "CSC482_Geographical_Information_System", "Geographical Information System",       "TODO"),
    (8, "CSC483", "CSC483_Decision_Support_and_Expert_System","Decision Support System and Expert System","TODO"),
    (8, "CSC484", "CSC484_Mobile_Application_Development",  "Mobile Application Development",       "TODO"),
    (8, "CSC485", "CSC485_Real_Time_Systems",               "Real Time Systems",                    "TODO"),
    (8, "CSC486", "CSC486_Network_and_System_Administration","Network and System Administration",   "TODO"),
    (8, "CSC487", "CSC487_Embedded_Systems_Programming",    "Embedded Systems Programming",         "TODO"),
    (8, "MGT488", "MGT488_International_Business_Management","International Business Management",   "TODO"),
]


def extract_units_for_course(text, course_title):
    """Extract unit numbers and titles from the PDF text for a given course."""
    units = []

    # Find the course section in the text
    # Look for "Course Title: <title>" then find all "Unit N:" lines after it
    # until the next "Course Title:" or "Laboratory Work" or "Text Book"

    # Normalize spaces in course_title for matching
    title_pattern = re.escape(course_title)
    # Allow flexible whitespace
    title_pattern = title_pattern.replace(r'\ ', r'\s+')

    # Find where this course starts
    course_match = re.search(
        r'Course\s+Title:\s*' + title_pattern,
        text, re.IGNORECASE
    )

    if not course_match:
        # Try partial match
        words = course_title.split()
        if len(words) >= 2:
            partial = r'\s+'.join(re.escape(w) for w in words[:3])
            course_match = re.search(
                r'Course\s+Title:\s*' + partial,
                text, re.IGNORECASE
            )

    if not course_match:
        print(f"  WARNING: Could not find course section for '{course_title}'")
        return units

    start_pos = course_match.start()

    # Find the next course or end of relevant section
    next_course = re.search(
        r'\nCourse\s+Title:',
        text[start_pos + 50:],
        re.IGNORECASE
    )
    end_pos = start_pos + 50 + next_course.start() if next_course else len(text)

    section = text[start_pos:end_pos]

    # Extract all "Unit N: Title (X Hrs.)" patterns
    unit_pattern = re.compile(
        r'Unit\s*(\d+)\s*[:\.]\s*(.+?)(?:\s*\([\d\s]+\s*[Hh]rs?\.?\s*\))?(?:\s*\r?\n)',
        re.IGNORECASE
    )

    for match in unit_pattern.finditer(section):
        unit_num = int(match.group(1))
        unit_title = match.group(2).strip()
        # Clean up the title
        unit_title = re.sub(r'\s+', ' ', unit_title)
        unit_title = unit_title.rstrip('.')
        # Remove trailing hour info if still present
        unit_title = re.sub(r'\s*\(\d+\s*[Hh]rs?\.?\)\s*$', '', unit_title)
        units.append((unit_num, unit_title))

    return units


def create_unit_folder(base_path, unit_num, unit_title):
    """Create a unit folder with a .gitkeep file."""
    folder_name = f"Unit {unit_num}-{unit_title}"
    # Sanitize folder name for Windows
    folder_name = re.sub(r'[<>:"/\\|?*]', '', folder_name)
    folder_name = folder_name.strip()

    folder_path = os.path.join(base_path, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    gitkeep = os.path.join(folder_path, ".gitkeep")
    if not os.path.exists(gitkeep):
        with open(gitkeep, 'w') as f:
            f.write("")

    return folder_name


def main():
    # Read the full extracted text
    with open(PDF_TEXT, 'r', encoding='utf-8') as f:
        text = f.read()

    created_count = 0
    skipped_count = 0
    warning_count = 0

    for semester, code, folder_name, course_title, status in COURSE_MAP:
        sem_dir = os.path.join(DATA_DIR, f"semester_{semester}")
        subject_dir = os.path.join(sem_dir, folder_name)

        # Ensure semester and subject directories exist
        os.makedirs(subject_dir, exist_ok=True)

        # Add .gitkeep to subject folder if not present
        gitkeep = os.path.join(subject_dir, ".gitkeep")
        if not os.path.exists(gitkeep):
            with open(gitkeep, 'w') as f:
                f.write("")

        if status == "COMPLETED":
            print(f"✓ SKIP  Semester {semester} / {code} {course_title} (COMPLETED)")
            skipped_count += 1
            continue

        # Extract units from PDF text
        units = extract_units_for_course(text, course_title)

        if not units:
            # Some courses like Project Work and Internship may not have units
            print(f"⚠ Semester {semester} / {code} {course_title} — no units found (may be project/internship)")
            warning_count += 1
            continue

        # Determine which units to skip (for PARTIAL status)
        skip_up_to = 0
        if status.startswith("PARTIAL:"):
            skip_up_to = int(status.split(":")[1])

        print(f"\n📘 Semester {semester} / {code} {course_title}")

        for unit_num, unit_title in units:
            if unit_num <= skip_up_to:
                print(f"   ✓ SKIP  Unit {unit_num}: {unit_title} (already done)")
                skipped_count += 1
                continue

            created_name = create_unit_folder(subject_dir, unit_num, unit_title)
            print(f"   + Created Unit {unit_num}: {unit_title}")
            created_count += 1

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"  Folders created : {created_count}")
    print(f"  Skipped (done)  : {skipped_count}")
    print(f"  Warnings        : {warning_count}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
