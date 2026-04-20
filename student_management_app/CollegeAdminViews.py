from django.shortcuts import render
def collegeadmin_home(request):
    return render(request, "hod_template/home_content.html")
