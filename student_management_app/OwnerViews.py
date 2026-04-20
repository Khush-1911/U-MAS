from django.shortcuts import render
def owner_home(request):
    return render(request, "hod_template/home_content.html")
