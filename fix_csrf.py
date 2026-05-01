import os

base_templates = [
    "student_management_app/templates/student_template/base_template.html",
    "student_management_app/templates/collegeadmin_template/base_template.html",
    "student_management_app/templates/department_hod_template/base_template.html",
    "student_management_app/templates/owner_template/base_template.html",
    "student_management_app/templates/staff_template/base_template.html",
    "student_management_app/templates/hod_template/base_template.html",
    "student_management_app/templates/principal_template/base_template.html"
]

jquery_script = """<script src="{% static 'plugins/jquery/jquery.min.js' %}"></script>"""
csrf_setup = """<script src="{% static 'plugins/jquery/jquery.min.js' %}"></script>
<script>
  function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
          const cookies = document.cookie.split(';');
          for (let i = 0; i < cookies.length; i++) {
              const cookie = cookies[i].trim();
              if (cookie.substring(0, name.length + 1) === (name + '=')) {
                  cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                  break;
              }
          }
      }
      return cookieValue;
  }
  const csrftoken = getCookie('csrftoken');
  $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (!(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) && !this.crossDomain) {
              xhr.setRequestHeader("X-CSRFToken", csrftoken);
          }
      }
  });
</script>"""

for tmpl in base_templates:
    if os.path.exists(tmpl):
        with open(tmpl, "r") as f:
            content = f.read()
        if "$.ajaxSetup" not in content and jquery_script in content:
            content = content.replace(jquery_script, csrf_setup)
            with open(tmpl, "w") as f:
                f.write(content)
            print(f"Patched {tmpl}")

# Now remove @csrf_exempt from views
views_files = [
    "student_management_app/StaffViews.py",
    "student_management_app/HodViews.py",
    "student_management_app/StudentViews.py"
]

for view_file in views_files:
    if os.path.exists(view_file):
        with open(view_file, "r") as f:
            content = f.read()
        if "@csrf_exempt" in content:
            # We replace @csrf_exempt followed by a newline, but handle cases where it might have trailing spaces
            import re
            content = re.sub(r'@csrf_exempt[ \t]*\n', '', content)
            with open(view_file, "w") as f:
                f.write(content)
            print(f"Removed @csrf_exempt from {view_file}")
