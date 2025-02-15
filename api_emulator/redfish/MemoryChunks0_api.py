#
# Copyright (c) 2017-2021, The Storage Networking Industry Association.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# Neither the name of The Storage Networking Industry Association (SNIA) nor
# the names of its contributors may be used to endorse or promote products
# derived from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#  THE POSSIBILITY OF SUCH DAMAGE.

# Resource implementation for - /redfish/v1/Systems/{ComputerSystemId}/MemoryDomains/{MemoryDomainId}/MemoryChunks/{MemoryChunksId}
# Program name - MemoryChunks0_api.py

import g
import json, os, random, string
import traceback
import logging

from flask import Flask, request
from flask_restful import Resource
from .constants import *
from api_emulator.utils import check_authentication, create_path, get_json_data, create_and_patch_object, delete_object, patch_object, put_object, create_collection
import api_emulator.agents_management as agents_management
from .templates.MemoryChunks0 import get_MemoryChunks0_instance

members = []
member_ids = []
INTERNAL_ERROR = 500

# MemoryChunks0 Collection API
class MemoryChunks0CollectionAPI(Resource):
	def __init__(self, **kwargs):
		logging.info('MemoryChunks0 Collection init called')
		self.root = PATHS['Root']
		self.auth = kwargs['auth']

	# HTTP GET
	def get(self, ComputerSystemId, MemoryDomainId):
		logging.info('MemoryChunks0 Collection get called')
		msg, code = check_authentication(self.auth)

		if code == 200:
			path = os.path.join(self.root, 'Systems/{0}/MemoryDomains/{1}/MemoryChunks', 'index.json').format(ComputerSystemId, MemoryDomainId)
			return get_json_data(path)
		else:
			return msg, code

	# HTTP POST Collection
	def post(self, ComputerSystemId, MemoryDomainId):
		logging.info('MemoryChunks0 Collection post called')
		msg, code = check_authentication(self.auth)

		if code == 200:
			if request.data:
				config = json.loads(request.data)
				if "@odata.type" in config:
					if "Collection" in config["@odata.type"]:
						return "Invalid data in POST body", 400

			if MemoryDomainId in members:
				resp = 404
				return resp
			path = create_path(self.root, 'Systems/{0}/MemoryDomains/{1}/MemoryChunks').format(ComputerSystemId, MemoryDomainId)
			parent_path = os.path.dirname(path)
			if not os.path.exists(path):
				os.mkdir(path)
				create_collection (path, 'MemoryChunks', parent_path)

			res = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
			if request.data:
				config = json.loads(request.data)
				if "@odata.id" in config:
					return MemoryChunks0API.post(self, ComputerSystemId, MemoryDomainId, os.path.basename(config['@odata.id']))
				else:
					return MemoryChunks0API.post(self, ComputerSystemId, MemoryDomainId, str(res))
			else:
				return MemoryChunks0API.post(self, ComputerSystemId, MemoryDomainId, str(res))
		else:
			return msg, code

# MemoryChunks0 API
class MemoryChunks0API(Resource):
	def __init__(self, **kwargs):
		logging.info('MemoryChunks0 init called')
		self.root = PATHS['Root']
		self.auth = kwargs['auth']

	# HTTP GET
	def get(self, ComputerSystemId, MemoryDomainId, MemoryChunksId):
		logging.info('MemoryChunks0 get called')
		msg, code = check_authentication(self.auth)

		if code == 200:
			path = create_path(self.root, 'Systems/{0}/MemoryDomains/{1}/MemoryChunks/{2}', 'index.json').format(ComputerSystemId, MemoryDomainId, MemoryChunksId)
			return get_json_data (path)
		else:
			return msg, code

	# HTTP POST
	# - Create the resource (since URI variables are available)
	# - Update the members and members.id lists
	# - Attach the APIs of subordinate resources (do this only once)
	# - Finally, create an instance of the subordiante resources
	def post(self, ComputerSystemId, MemoryDomainId, MemoryChunksId):
		logging.info('MemoryChunks0 post called')
		msg, code = check_authentication(self.auth)
		full_id = f"/redfish/v1/Systems/{ComputerSystemId}/MemoryDomains/{MemoryDomainId}/MemoryChunks/{MemoryChunksId}"
		if code == 200:
			path = create_path(self.root, 'Systems/{0}/MemoryDomains/{1}/MemoryChunks/{2}').format(ComputerSystemId, MemoryDomainId, MemoryChunksId)
			collection_path = os.path.join(self.root, 'Systems/{0}/MemoryDomains/{1}/MemoryChunks', 'index.json').format(ComputerSystemId, MemoryDomainId)

			# Check if collection exists:
			if not os.path.exists(collection_path):
				MemoryChunks0CollectionAPI.post(self, ComputerSystemId, MemoryDomainId)

			if full_id in member_ids:
				resp = "Element Id already existing", 404
				return resp
			try:
				logging.debug("MemoryChunks0API POST - request payload")
				logging.debug(json.dumps(request.json, indent=2))
				if not request.data:
					return "Request payload missing", 400

				# This piece checking for the agent should really be in the collection class, because that is where one
				# would POST for creating an object. However, the actual resource is created in this method and this is
				# where we need the agent id.
				config = request.json
				agent, response = agents_management.forwardToAgentIfManaged("POST", request.path, config=config)
				if agent is not None and response[1] != 200:
					logging.debug("Agent returned an error")
					logging.debug(response)
					# This is the case where the object is agent managed and there was an error on the agent side
					# let's return the agent error code and message and stop here.
					return response

				logging.debug(f"Managing agent: {agent}")

				wildcards = {'ComputerSystemId':ComputerSystemId, 'MemoryDomainId':MemoryDomainId, 'MemoryChunksId':MemoryChunksId, 'rb':g.rest_base}
				config = get_MemoryChunks0_instance(wildcards)
				config = create_and_patch_object(config, members, member_ids, path, collection_path, agent)
				resp = config, 200
			except Exception:
				traceback.print_exc()
				resp = INTERNAL_ERROR
			logging.info('MemoryChunks0API POST exit')
			return resp
		else:
			return msg, code

	# HTTP PUT
	def put(self, ComputerSystemId, MemoryDomainId, MemoryChunksId):
		logging.info('MemoryChunks0 put called')
		msg, code = check_authentication(self.auth)
		full_id = f"/redfish/v1/Systems/{ComputerSystemId}/MemoryDomains/{MemoryDomainId}/MemoryChunks/{MemoryChunksId}"

		if code == 200:
			if full_id not in member_ids:
				return "Element not present.", 404

			agent, response = agents_management.forwardToAgentIfManaged("PUT", request.path, config=request.json)
			if agent is not None and response[1] != 200:
				logging.debug("Agent returned an error")
				logging.debug(response)
				# This is the case where the object is agent managed and there was an error on the agent side
				# let's return the agent error code and message and stop here.
				return response

			path = os.path.join(self.root, 'Systems/{0}/MemoryDomains/{1}/MemoryChunks/{2}', 'index.json').format(ComputerSystemId, MemoryDomainId, MemoryChunksId)
			put_object(path, agent)
			return self.get(ComputerSystemId, MemoryDomainId, MemoryChunksId)
		else:
			return msg, code

	# HTTP PATCH
	def patch(self, ComputerSystemId, MemoryDomainId, MemoryChunksId):
		logging.info('MemoryChunks0 patch called')
		msg, code = check_authentication(self.auth)
		full_id = f"/redfish/v1/Systems/{ComputerSystemId}/MemoryDomains/{MemoryDomainId}/MemoryChunks/{MemoryChunksId}"

		if code == 200:
			if full_id not in member_ids:
				return "Element not present.", 404

			agent, response = agents_management.forwardToAgentIfManaged("PATCH", request.path, config=request.json)
			if agent is not None and response[1] != 200:
				logging.debug("Agent returned an error")
				logging.debug(response)
				# This is the case where the object is agent managed and there was an error on the agent side
				# let's return the agent error code and message and stop here.
				return response

			path = os.path.join(self.root, 'Systems/{0}/MemoryDomains/{1}/MemoryChunks/{2}', 'index.json').format(ComputerSystemId, MemoryDomainId, MemoryChunksId)
			patch_object(path)
			return self.get(ComputerSystemId, MemoryDomainId, MemoryChunksId)
		else:
			return msg, code

	# HTTP DELETE
	def delete(self, ComputerSystemId, MemoryDomainId, MemoryChunksId):
		logging.info('MemoryChunks0 delete called')
		msg, code = check_authentication(self.auth)
		full_id = f"/redfish/v1/Systems/{ComputerSystemId}/MemoryDomains/{MemoryDomainId}/MemoryChunks/{MemoryChunksId}"

		if code == 200:
			if full_id not in member_ids:
				return "Element not present.", 404

			agent, response = agents_management.forwardToAgentIfManaged("DELETE", request.path)
			if agent is not None and response[1] != 200:
				logging.debug("Agent returned an error")
				logging.debug(response)
				# This is the case where the object is agent managed and there was an error on the agent side
				# let's return the agent error code and message and stop here.
				return response

			path = create_path(self.root, 'Systems/{0}/MemoryDomains/{1}/MemoryChunks/{2}').format(ComputerSystemId, MemoryDomainId, MemoryChunksId)
			base_path = create_path(self.root, 'Systems/{0}/MemoryDomains/{1}/MemoryChunks').format(ComputerSystemId, MemoryDomainId)
			return delete_object(path, base_path, members=members, member_ids=member_ids)
		else:
			return msg, code

