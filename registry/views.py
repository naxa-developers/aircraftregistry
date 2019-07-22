import datetime
import json

from datetime import datetime
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.utils import translation
from django.views.generic import TemplateView
from rest_framework import generics, mixins, status, viewsets
from rest_framework.authentication import (SessionAuthentication,
                                           TokenAuthentication)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from registry.models import Activity, Authorization, Contact, Operator, Aircraft, Pilot, Test, TestValidity
from registry.serializers import (ContactSerializer, OperatorSerializer, PilotSerializer, 
                                  PrivilagedContactSerializer, PrivilagedPilotSerializer,
                                  PrivilagedOperatorSerializer, AircraftSerializer, AircraftDetailSerializer, AircraftESNSerializer)
from django.http import JsonResponse
from rest_framework.decorators import api_view
from six.moves.urllib import request as req
from functools import wraps
import os
import jwt
import json
from functools import wraps


from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend

# Create your views here.


def get_token_auth_header(request):
	auth = request.META.get("HTTP_AUTHORIZATION", None)
	parts = auth.split()

	token = parts[1]
	
	return token


def requires_scope(required_scope):
	"""Determines if the required scope is present in the access token
	Args:
	    required_scope (str): The scope required to access the resource
	"""
	def require_scope(f):
		@wraps(f)
		def decorated(*args, **kwargs):
			token = get_token_auth_header(args[0])
			print(token)
			AUTH0_DOMAIN = os.environ.get('AUTH0_DOMAIN')
			AUTH0_AUDIENCE = os.environ.get('AUTH0_AUDIENCE')
			print(AUTH0_DOMAIN)
			jsonurl = req.urlopen('https://' + AUTH0_DOMAIN + '/.well-known/jwks.json')
			jwks = json.loads(jsonurl.read())
			cert = '-----BEGIN CERTIFICATE-----\n' + jwks['keys'][0]['x5c'][0] + '\n-----END CERTIFICATE-----'
			certificate = load_pem_x509_certificate(cert.encode('utf-8'), default_backend())
			public_key = certificate.public_key()
			try:
				decoded = jwt.decode(token, public_key, audience=AUTH0_AUDIENCE, algorithms=['RS256'])
			except Exception as e: 
				raise PermissionDenied
							
			if decoded.get("scope"):
				token_scopes = decoded["scope"].split()
				print(token_scopes, required_scope)
				for token_scope in token_scopes:
					if token_scope == required_scope:
						return f(*args, **kwargs)
			response = JsonResponse({'message': 'You don\'t have access to this resource'})
			response.status_code = 403
			return response
		return decorated
	return require_scope

@api_view(['GET'])
@requires_scope('read:operator')
class OperatorList(mixins.ListModelMixin,
				  generics.GenericAPIView):
	"""
	List all operators, or create a new operator.
	"""

	queryset = Operator.objects.all()
	serializer_class = OperatorSerializer

	def get(self, request, *args, **kwargs):
		return self.list(request, *args, **kwargs)



class OperatorDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
	"""
	Retrieve, update or delete a Operator instance.
	"""
	# authentication_classes = (SessionAuthentication,TokenAuthentication)
	# permission_classes = (IsAuthenticated,)

	queryset = Operator.objects.all()
	serializer_class = OperatorSerializer

	def get(self, request, *args, **kwargs):
	    return self.retrieve(request, *args, **kwargs)

	def put(self, request, *args, **kwargs):
		return self.update(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		return self.create(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
	    return self.destroy(request, *args, **kwargs)




class AircraftDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
	"""
	Retrieve, update or delete a Aircraft instance.
	"""
	# authentication_classes = (SessionAuthentication,TokenAuthentication)
	# permission_classes = (IsAuthenticated,)

	def get_Aircraft(self, pk):
		try:
			a = Aircraft.objects.get(id=pk)			
		except Aircraft.DoesNotExist:					
			raise Http404
		else: 
			return a

	def get(self, request, pk,format=None):
		aircraft = self.get_Aircraft(pk)		
		serializer = AircraftDetailSerializer(aircraft)
		return Response(serializer.data)

	def put(self, request, *args, **kwargs):
		return self.update(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		return self.create(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
	    return self.destroy(request, *args, **kwargs)



class OperatorDetailPrivilaged(mixins.RetrieveModelMixin,
                    generics.GenericAPIView):
	"""
	Retrieve, update or delete a Operator instance.
	"""
	
	queryset = Operator.objects.all()
	serializer_class = PrivilagedOperatorSerializer

	def get(self, request, *args, **kwargs):
	    return self.retrieve(request, *args, **kwargs)



class OperatorAircraft(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
	"""
	Retrieve, update or delete a Operator instance.
	"""
	
	queryset = Aircraft.objects.all()
	serializer_class = AircraftSerializer

	def get_Aircraft(self, pk):
		try:
			o =  Operator.objects.get(id=pk)
		except Operator.DoesNotExist:
			raise Http404
		else: 
			return Aircraft.objects.filter(operator = o)

	def get(self, request, pk,format=None):
		aircraft = self.get_Aircraft(pk)
		serializer = AircraftSerializer(aircraft, many=True)

		return Response(serializer.data)

	def post(self, request, *args, **kwargs):
		return self.create(request, *args, **kwargs)

	def put(self, request, *args, **kwargs):
	    return self.update(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
	    return self.destroy(request, *args, **kwargs)



class AircraftESNDetails(mixins.RetrieveModelMixin,
                    generics.GenericAPIView):

    queryset = Aircraft.objects.all()
    serializer_class = AircraftESNSerializer
    lookup_field = 'esn'
	
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)



class ContactList(mixins.ListModelMixin,
				  generics.GenericAPIView):
	"""
	List all contacts in the database
	"""

	queryset = Contact.objects.all()
	serializer_class = ContactSerializer

	def get(self, request, *args, **kwargs):
		return self.list(request, *args, **kwargs)



class ContactDetail(mixins.RetrieveModelMixin,
                    generics.GenericAPIView):
	"""
	Retrieve, update or delete a Contact instance.
	"""
	
	queryset = Contact.objects.all()
	serializer_class = ContactSerializer

	def get(self, request, *args, **kwargs):
	    return self.retrieve(request, *args, **kwargs)




class ContactDetailPrivilaged(mixins.RetrieveModelMixin,
                    generics.GenericAPIView):
	"""
	Retrieve, update or delete a Contact instance.
	"""
	
	queryset = Contact.objects.all()
	serializer_class = PrivilagedContactSerializer

	def get(self, request, *args, **kwargs):
	    return self.retrieve(request, *args, **kwargs)



class PilotList(mixins.ListModelMixin,
				  generics.GenericAPIView):
	"""
	List all pilots in the database
	"""
	queryset = Pilot.objects.all()
	serializer_class = PilotSerializer

	def get(self, request, *args, **kwargs):
		return self.list(request, *args, **kwargs)



class PilotDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
	"""
	Retrieve, update or delete a Pilot instance.
	"""
	# authentication_classes = (SessionAuthentication,TokenAuthentication)
	# permission_classes = (IsAuthenticated,)

	queryset = Pilot.objects.all()
	serializer_class = PilotSerializer

	def get(self, request, *args, **kwargs):
	    return self.retrieve(request, *args, **kwargs)

	def put(self, request, *args, **kwargs):
	    return self.update(request, *args, **kwargs)

	def delete(self, request, *args, **kwargs):
	    return self.destroy(request, *args, **kwargs)




class PilotDetailPrivilaged(mixins.RetrieveModelMixin,
                    generics.GenericAPIView):
	"""
	Retrieve, update or delete a Pilot instance.
	"""
	

	queryset = Pilot.objects.all()
	serializer_class = PrivilagedPilotSerializer

	def get(self, request, *args, **kwargs):
	    return self.retrieve(request, *args, **kwargs)


class HomeView(TemplateView):
    template_name ='registry/index.html'

class APIView(TemplateView):
    template_name ='registry/api.html'
