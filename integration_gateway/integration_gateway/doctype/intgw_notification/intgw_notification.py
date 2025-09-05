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
