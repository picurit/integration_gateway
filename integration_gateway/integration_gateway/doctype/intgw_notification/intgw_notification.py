# Copyright (c) 2025, Picurit and contributors
# For license information, please see license.txt

import json
import frappe
from typing import Any, Optional
from frappe.model.document import Document
from frappe.exceptions import ValidationError, DataError
from jsonpath_ng.ext import parse
from jsonpath_ng.exceptions import JSONPathError

class INTGWNotification(Document):

	@frappe.whitelist(methods=["GET"])
	def resolve_path(self, path: str, default: Optional[Any] = None, field_name: str = 'json_payload') -> Any:
		"""
		Resolves a JSONPath expression against the specified field content.
		
		This method is designed to work with Jinja templates and provides robust error handling for all edge cases.
		
		Args:
			path: JSONPath expression string (e.g., '$.user.name', '$..items[*].id')
			default: Default value to return if path is not found or evaluation fails
			field_name: Name of the field containing JSON data (defaults to 'json_payload')
			
		Returns:
			The resolved value(s) from JSONPath evaluation, or default value
			
		Raises:
			ValidationError: For invalid input parameters
			DataError: For JSON parsing or JSONPath compilation errors
		"""
		# Input validation
		if not isinstance(path, str):
			raise ValidationError(f"Path must be a string, got {type(path).__name__}")
			
		if not path.strip():
			raise ValidationError("Path cannot be empty or whitespace")
			
		if not isinstance(field_name, str):
			raise ValidationError(f"Field name must be a string, got {type(field_name).__name__}")
		
		try:
			# Get the field value
			field_value = self.get(field_name)
			
			# Handle empty or None field
			if field_value is None:
				return default
				
			# Parse JSON data if it's a string
			if isinstance(field_value, str):
				if not field_value.strip():
					return default
				try:
					json_data = json.loads(field_value)
				except json.JSONDecodeError as e:
					frappe.log_error(
						message=f"Failed to parse JSON in field '{field_name}': {str(e)}",
						title="INTGWNotification JSONPath Resolution Error"
					)
					raise DataError(f"Invalid JSON in field '{field_name}': {str(e)}")
			elif isinstance(field_value, (dict, list)):
				# Already parsed JSON data
				json_data = field_value
			else:
				# Unsupported data type
				raise ValidationError(f"Field '{field_name}' must contain JSON string or object, got {type(field_value).__name__}")
			
			# Compile and execute JSONPath
			try:
				jsonpath_expr = parse(path)
			except JSONPathError as e:
				frappe.log_error(
					message=f"Invalid JSONPath expression '{path}': {str(e)}",
					title="INTGWNotification JSONPath Compilation Error"
				)
				raise DataError(f"Invalid JSONPath expression '{path}': {str(e)}")
			except Exception as e:
				frappe.log_error(
					message=f"Unexpected error compiling JSONPath '{path}': {str(e)}",
					title="INTGWNotification JSONPath Compilation Error"
				)
				raise DataError(f"Failed to compile JSONPath expression '{path}': {str(e)}")
			
			# Execute JSONPath query
			try:
				matches = jsonpath_expr.find(json_data)
				
				# Handle results
				if not matches:
					return default
					
				# Extract values from matches
				values = [match.value for match in matches]
				
				# Return single value if only one match, otherwise return list
				if len(values) == 1:
					return values[0]
				else:
					return values
					
			except Exception as e:
				frappe.log_error(
					message=f"Error executing JSONPath '{path}' on data: {str(e)}",
					title="INTGWNotification JSONPath Execution Error"
				)
				raise DataError(f"Failed to execute JSONPath query '{path}': {str(e)}")
				
		except (ValidationError, DataError):
			# Re-raise our custom exceptions
			raise
		except Exception as e:
			# Catch any unexpected exceptions
			frappe.log_error(
				message=f"Unexpected error in resolve_path: {str(e)}",
				title="INTGWNotification Unexpected Error"
			)
			raise DataError(f"Unexpected error resolving path '{path}': {str(e)}")

	@frappe.whitelist(methods=["POST", "PUT", "PATCH"])
	def update_path(self, path: str, value: Any, field_name: str = 'json_payload') -> Any:
		"""
		Updates a value at the specified JSONPath location in the field content.
		
		This method supports both modifying existing values and creating new paths.
		For creating new paths, parent objects/arrays must exist.
		
		Args:
			path: JSONPath expression string (e.g., '$.user.name', '$.products[0].price')
			value: The value to set at the specified path
			field_name: Name of the field containing JSON data (defaults to 'json_payload')
			
		Raises:
			ValidationError: For invalid input parameters
			DataError: For JSON parsing, JSONPath compilation, or update operation errors
		"""
		# Input validation
		if not isinstance(path, str):
			raise ValidationError(f"Path must be a string, got {type(path).__name__}")
		if not path.strip():
			raise ValidationError("Path cannot be empty or whitespace")
		if not isinstance(field_name, str):
			raise ValidationError(f"Field name must be a string, got {type(field_name).__name__}")

		try:
			# Get the field value
			field_value = self.get(field_name)
			
			# Initialize with empty object if field is None or empty
			if field_value is None or (isinstance(field_value, str) and not field_value.strip()):
				json_data = {}
			elif isinstance(field_value, str):
				try:
					json_data = json.loads(field_value)
				except json.JSONDecodeError as e:
					frappe.log_error(
						message=f"Failed to parse JSON in field '{field_name}': {str(e)}",
						title="INTGWNotification JSONPath Update Error"
					)
					raise DataError(f"Invalid JSON in field '{field_name}': {str(e)}")
			elif isinstance(field_value, (dict, list)):
				json_data = json.loads(json.dumps(field_value))
			else:
				# Unsupported data type
				raise ValidationError(f"Field '{field_name}' must contain JSON string or object, got {type(field_value).__name__}")

			try:
				jsonpath_expr = parse(path)
			except JSONPathError as e:
				frappe.log_error(
					message=f"Invalid JSONPath expression '{path}': {str(e)}",
					title="INTGWNotification JSONPath Update Error"
				)
				raise DataError(f"Invalid JSONPath expression '{path}': {str(e)}")
			except Exception as e:
				frappe.log_error(
					message=f"Unexpected error compiling JSONPath '{path}': {str(e)}",
					title="INTGWNotification JSONPath Update Error"
				)
				raise DataError(f"Failed to compile JSONPath expression '{path}': {str(e)}")
			
			# Perform update operation
			try:
				# Find existing matches
				matches = jsonpath_expr.find(json_data)
				if matches:
					jsonpath_expr.update(json_data, value)
				else:
					# No matches found - check if path contains wildcards
					if '*' in path or '..' in path:
						# For wildcard paths that don't match anything, we need a different approach
						# Try to create the fields manually by expanding the wildcard
						self._handle_wildcard_creation(json_data, path, value)
					else:
						# For simple paths, try to create the path manually
						self._create_path(json_data, path, value)
				
				# Persist the change to the database
				formatted_json = json.dumps(json_data, indent=4, ensure_ascii=False)
				self.db_set(field_name, formatted_json)
				# Also update the in-memory value
				self.set(field_name, formatted_json)

				return json_data
			except DataError:
				raise
			except Exception as e:
				frappe.log_error(
					message=f"Error updating JSONPath '{path}' with value '{value}': {str(e)}",
					title="INTGWNotification JSONPath Update Error"
				)
				raise DataError(f"Failed to update path '{path}': {str(e)}")
		except (ValidationError, DataError):
			raise
		except Exception as e:
			frappe.log_error(
				message=f"Unexpected error in update_path: {str(e)}",
				title="INTGWNotification Unexpected Error"
			)
			raise DataError(f"Unexpected error updating path '{path}': {str(e)}")

	@frappe.whitelist(methods=["POST"])
	def delete_path(self, path: str, field_name: str = 'json_payload') -> Any:
		"""
		Deletes values at the specified JSONPath location from the field content.
		
		This method removes all matches found by the JSONPath expression.
		For array elements, deletion maintains array structure (doesn't reindex).
		
		Args:
			path: JSONPath expression string (e.g., '$.user.name', '$.products[0]')
			field_name: Name of the field containing JSON data (defaults to 'json_payload')
			
		Raises:
			ValidationError: For invalid input parameters
			DataError: For JSON parsing, JSONPath compilation, or deletion operation errors
		"""
		# Input validation
		if not isinstance(path, str):
			raise ValidationError(f"Path must be a string, got {type(path).__name__}")
		if not path.strip():
			raise ValidationError("Path cannot be empty or whitespace")
		if not isinstance(field_name, str):
			raise ValidationError(f"Field name must be a string, got {type(field_name).__name__}")

		try:
			# Get the field value
			field_value = self.get(field_name)
			
			# Handle empty or None field
			if field_value is None or (isinstance(field_value, str) and not field_value.strip()):
				return {}
			if isinstance(field_value, str):
				try:
					json_data = json.loads(field_value)
				except json.JSONDecodeError as e:
					frappe.log_error(
						message=f"Failed to parse JSON in field '{field_name}': {str(e)}",
						title="INTGWNotification JSONPath Delete Error"
					)
					raise DataError(f"Invalid JSON in field '{field_name}': {str(e)}")
			elif isinstance(field_value, (dict, list)):
				# Already parsed JSON data - make a copy to avoid modifying original
				json_data = json.loads(json.dumps(field_value))
			else:
				# Unsupported data type
				raise ValidationError(f"Field '{field_name}' must contain JSON string or object, got {type(field_value).__name__}")
			
			# Compile JSONPath
			try:
				jsonpath_expr = parse(path)
			except JSONPathError as e:
				frappe.log_error(
					message=f"Invalid JSONPath expression '{path}': {str(e)}",
					title="INTGWNotification JSONPath Delete Error"
				)
				raise DataError(f"Invalid JSONPath expression '{path}': {str(e)}")
			except Exception as e:
				frappe.log_error(
					message=f"Unexpected error compiling JSONPath '{path}': {str(e)}",
					title="INTGWNotification JSONPath Delete Error"
				)
				raise DataError(f"Failed to compile JSONPath expression '{path}': {str(e)}")
			
			# Perform delete operation
			try:
				# Use jsonpath-ng's update functionality to set values to None, then clean up
				# This is more reliable than trying to manually navigate the structure
				matches = jsonpath_expr.find(json_data)
				if not matches:
					# Nothing to delete - this is not an error
					return json_data
				jsonpath_expr.update(json_data, None)
				
				# Clean up None values from the structure
				self._clean_none_values(json_data)

				# Persist the change to the database
				formatted_json = json.dumps(json_data, indent=4, ensure_ascii=False)
				self.db_set(field_name, formatted_json)
				# Also update the in-memory value
				self.set(field_name, formatted_json)
				
				return json_data
			except Exception as e:
				frappe.log_error(
					message=f"Error deleting JSONPath '{path}': {str(e)}",
					title="INTGWNotification JSONPath Delete Error"
				)
				raise DataError(f"Failed to delete path '{path}': {str(e)}")
		except (ValidationError, DataError):
			raise
		except Exception as e:
			frappe.log_error(
				message=f"Unexpected error in delete_path: {str(e)}",
				title="INTGWNotification Unexpected Error"
			)
			raise DataError(f"Unexpected error deleting path '{path}': {str(e)}")

	def _handle_wildcard_creation(self, data: Any, path: str, value: Any) -> None:
		"""
		Handle creation of fields for wildcard paths.
		
		Args:
			data: The root data structure to modify
			path: JSONPath expression with wildcards (e.g., '$.products[*].category')
			value: The value to set at each matching location
		"""
		# For now, handle the common case of $.array[*].field
		# This can be extended for more complex wildcard patterns
		
		if path.startswith('$.') and '[*]' in path:
			# Parse path like '$.products[*].category'
			parts = path[2:].split('[*].')
			if len(parts) == 2:
				array_path = parts[0]  # 'products'
				field_name = parts[1]  # 'category'
				
				# Get the array using simple path resolution
				array_expr = parse(f'$.{array_path}')
				array_matches = array_expr.find(data)
				
				if array_matches:
					for match in array_matches:
						if isinstance(match.value, list):
							# Add the field to each object in the array
							for item in match.value:
								if isinstance(item, dict):
									item[field_name] = value
				return
		
		# If we can't handle this wildcard pattern, log and raise error
		raise DataError(f"Unsupported wildcard pattern for field creation: '{path}'")

	def _create_path(self, data: Any, path: str, value: Any) -> None:
		"""
		Helper method to create a new path in the JSON data structure.
		
		Args:
			data: The root data structure to modify
			path: JSONPath expression (e.g., '$.user.email', '$.products[0].category')
			value: The value to set at the created path
		"""
		# Remove the '$.' prefix and split the path into components
		if path.startswith('$.'):
			path = path[2:]
		elif path.startswith('$'):
			path = path[1:]
		
		if not path:
			raise DataError("Cannot create root path")
		
		# Split path into components, handling array indices
		components = self._parse_path_components(path)
		
		# Navigate to the location and create the path
		current = data
		
		for i, component in enumerate(components[:-1]):
			key = component['key']
			is_array = component['is_array']
			index = component.get('index')
			
			if is_array:
				# Handle array access
				if key:
					# Array is a property of an object (e.g., products[0])
					if key not in current:
						current[key] = []
					current = current[key]
				
				if not isinstance(current, list):
					raise DataError(f"Expected array at path component '{key}', got {type(current).__name__}")
				
				# Ensure array is large enough
				while len(current) <= index:
					current.append({})
				
				current = current[index]
			else:
				# Handle object property access
				if key not in current:
					# Determine what type the next component needs
					next_component = components[i + 1]
					current[key] = [] if next_component['is_array'] and not next_component['key'] else {}
				
				current = current[key]
		
		# Set the final value
		final_component = components[-1]
		key = final_component['key']
		is_array = final_component['is_array']
		index = final_component.get('index')
		
		if is_array:
			if key:
				# Array property
				if key not in current:
					current[key] = []
				current = current[key]
			
			if not isinstance(current, list):
				raise DataError(f"Expected array at final path component '{key}', got {type(current).__name__}")
			
			# Ensure array is large enough
			while len(current) <= index:
				current.append(None)
			
			current[index] = value
		else:
			# Object property
			if not isinstance(current, dict):
				raise DataError(f"Expected object to set property '{key}', got {type(current).__name__}")
			
			current[key] = value

	def _parse_path_components(self, path: str) -> list:
		"""
		Parse a JSONPath into components.
		
		Args:
			path: Path without the '$.' prefix (e.g., 'user.email', 'products[0].name')
			
		Returns:
			List of dictionaries with 'key', 'is_array', and optional 'index' keys
		"""
		components = []
		parts = path.split('.')
		
		for part in parts:
			if '[' in part and ']' in part:
				# Array access: 'products[0]' or '[0]'
				key_part = part.split('[')[0]
				index_part = part.split('[')[1].split(']')[0]
				
				try:
					index = int(index_part)
				except ValueError:
					raise DataError(f"Invalid array index '{index_part}' in path component '{part}'")
				
				if key_part:
					# Object property that is an array: 'products[0]'
					components.append({
						'key': key_part,
						'is_array': True,
						'index': index
					})
				else:
					# Direct array access: '[0]'
					components.append({
						'key': '',
						'is_array': True,
						'index': index
					})
			else:
				# Simple object property: 'user' or 'email'
				components.append({
					'key': part,
					'is_array': False
				})
		
		return components

	def _clean_none_values(self, data: Any) -> None:
		"""
		Helper method to recursively remove None values from dicts and lists.
		
		Args:
			data: The data structure to clean (modified in place)
		"""
		if isinstance(data, dict):
			# Create a list of keys to delete to avoid modifying dict during iteration
			keys_to_delete = [key for key, value in data.items() if value is None]
			for key in keys_to_delete:
				del data[key]
			
			# Clean nested structures
			for value in data.values():
				self._clean_none_values(value)
				
		elif isinstance(data, list):
			# Remove None values and clean nested structures
			# We need to be careful about index changes when removing elements
			i = 0
			while i < len(data):
				if data[i] is None:
					data.pop(i)
					# Don't increment i because we removed an element
				else:
					self._clean_none_values(data[i])
					i += 1
