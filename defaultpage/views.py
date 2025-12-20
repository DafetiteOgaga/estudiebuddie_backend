from django.shortcuts import render
from django.http import HttpResponse

welcome = """
	Welcome to the Study Buddie Backend!<br/>
	Remember that the paths in the config starts with the appname<br/>
	And it continues with specific path names in individual apps.
"""
# Create your views here.
def defaultpage(request):
	"""
	Default page view that renders the default page template.
	"""
	return HttpResponse(welcome)
