import os
import glob

directory = "/Users/buntie/Desktop/Project ETC/U-MAS/student_management_app"
files_to_check = []
for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith('.py') or file.endswith('.html'):
            files_to_check.append(os.path.join(root, file))

replacements = {
    "Courses": "Department",
    "course_id": "department_id",
    "course_name": "department_name",
    "course_obj": "department_obj",
    "AdminHOD": "OwnerProfile",
    "adminhod": "ownerprofile",
    "assigned_staff": "mentor",
    "course": "department"
}

for filepath in files_to_check:
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    # Be careful with "course" vs "courses"
    for old, new in replacements.items():
        if old == "course":
            # only match exact word or in specific contexts to avoid messing up urls?
            # actually course is heavily used.
            content = content.replace("course", "department")
            content = content.replace("Course", "Department")
        else:
            content = content.replace(old, new)
            
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated {filepath}")
