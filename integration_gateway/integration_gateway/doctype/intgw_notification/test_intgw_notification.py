# Copyright (c) 2025, Picurit and Contributors
# See license.txt

import json
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import frappe
from frappe.exceptions import DataError, ValidationError
from frappe.tests.utils import FrappeTestCase


@contextmanager
def get_test_intgw_notification(json_payload: Any = None):
	"""Context manager to create and cleanup test INTGW Notification documents"""
	doc = frappe.new_doc("INTGW Notification")
	if json_payload is not None:
		doc.json_payload = json_payload
	doc.insert()
	doc.reload()
	try:
		yield doc
	finally:
		doc.delete()


class TestINTGWNotification(FrappeTestCase):
	"""Test cases for INTGW Notification doctype and its resolve_path method"""
	
	@classmethod
	def setUpClass(cls):
		"""Set up test class with sample data"""
		super().setUpClass()
		
		# Sample notification data for comprehensive testing
		cls.sample_notification_data = {
			"user": {
				"name": "John Doe",
				"email": "john@example.com",
				"profile": {
					"age": 30,
					"preferences": ["email", "sms"]
				}
			},
			"orders": [
				{"id": 1, "total": 100.50, "items": ["item1", "item2"]},
				{"id": 2, "total": 250.75, "items": ["item3"]},
				{"id": 3, "total": 75.25, "items": ["item4", "item5", "item6"]}
			],
			"metadata": {
				"version": "1.0",
				"created_at": "2025-08-28T10:00:00Z"
			},
			"tags": ["important", "urgent", "customer"]
		}
		
		# Complex nested data for advanced testing
		cls.complex_data = {
			"event": "order_created",
			"timestamp": "2025-08-28T15:30:00Z",
			"customer": {
				"id": "CUST-001",
				"name": "Alice Johnson",
				"email": "alice@example.com",
				"tier": "premium"
			},
			"order": {
				"id": "ORD-12345",
				"total": 299.99,
				"currency": "USD",
				"items": [
					{"sku": "ITEM-001", "name": "Widget A", "quantity": 2, "price": 149.99},
					{"sku": "ITEM-002", "name": "Gadget B", "quantity": 1, "price": 0.01}
				]
			},
			"shipping": {
				"method": "express",
				"address": {
					"street": "123 Main St",
					"city": "New York",
					"state": "NY",
					"zip": "10001"
				}
			}
		}
	
	def setUp(self):
		"""Set up individual test cases"""
		# Create a test document for general use
		self.test_doc = frappe.new_doc("INTGW Notification")
		self.test_doc.json_payload = json.dumps(self.sample_notification_data)
	
	def tearDown(self):
		"""Clean up after each test"""
		if hasattr(self, 'test_doc') and self.test_doc.name:
			self.test_doc.delete()
	
	def test_basic_field_access(self):
		"""Test basic JSONPath field access"""
		with get_test_intgw_notification(json.dumps(self.sample_notification_data)) as doc:
			# Test simple field access
			result = doc.resolve_path("$.user.name")
			self.assertEqual(result, "John Doe")
			
			# Test nested field access
			result = doc.resolve_path("$.user.profile.age")
			self.assertEqual(result, 30)
			
			# Test email field
			result = doc.resolve_path("$.user.email")
			self.assertEqual(result, "john@example.com")
	
	def test_array_access(self):
		"""Test JSONPath array access patterns"""
		with get_test_intgw_notification(json.dumps(self.sample_notification_data)) as doc:
			# Test array index access
			result = doc.resolve_path("$.orders[0].id")
			self.assertEqual(result, 1)
			
			# Test array element access
			result = doc.resolve_path("$.tags[0]")
			self.assertEqual(result, "important")
			
			# Test last element
			result = doc.resolve_path("$.tags[2]")
			self.assertEqual(result, "customer")
	
	def test_wildcard_expressions(self):
		"""Test JSONPath wildcard and array processing"""
		with get_test_intgw_notification(json.dumps(self.sample_notification_data)) as doc:
			# Test array wildcard
			result = doc.resolve_path("$.orders[*].id")
			self.assertEqual(result, [1, 2, 3])
			
			# Test array totals
			result = doc.resolve_path("$.orders[*].total")
			self.assertEqual(result, [100.50, 250.75, 75.25])
			
			# Test nested array preferences
			result = doc.resolve_path("$.user.profile.preferences[*]")
			self.assertEqual(result, ["email", "sms"])
	
	def test_recursive_descent(self):
		"""Test JSONPath recursive descent operators"""
		with get_test_intgw_notification(json.dumps(self.sample_notification_data)) as doc:
			# Test recursive item search
			result = doc.resolve_path("$..items")
			expected = [["item1", "item2"], ["item3"], ["item4", "item5", "item6"]]
			self.assertEqual(result, expected)
			
			# Test flattened recursive search
			result = doc.resolve_path("$..items[*]")
			expected = ["item1", "item2", "item3", "item4", "item5", "item6"]
			self.assertEqual(result, expected)
	
	def test_default_values(self):
		"""Test default value handling for non-existent paths"""
		with get_test_intgw_notification(json.dumps(self.sample_notification_data)) as doc:
			# Test simple default
			result = doc.resolve_path("$.user.address", "N/A")
			self.assertEqual(result, "N/A")
			
			# Test complex default
			default_obj = {"status": "not_found"}
			result = doc.resolve_path("$.nonexistent.path", default_obj)
			self.assertEqual(result, default_obj)
			
			# Test numeric default
			result = doc.resolve_path("$.orders[10].id", -1)
			self.assertEqual(result, -1)
			
			# Test None default (should return None)
			result = doc.resolve_path("$.missing.field")
			self.assertIsNone(result)
	
	def test_data_type_handling(self):
		"""Test handling of different data types in JSON payload"""
		# Test with JSON string (most common case)
		with get_test_intgw_notification(json.dumps(self.sample_notification_data)) as doc:
			result = doc.resolve_path("$.user.name")
			self.assertEqual(result, "John Doe")
		
		# Test with dictionary data (stored as JSON string)
		with get_test_intgw_notification(json.dumps(self.sample_notification_data)) as doc:
			# Manually set the field as dict after creation to test dict handling
			doc.json_payload = self.sample_notification_data
			result = doc.resolve_path("$.user.name")
			self.assertEqual(result, "John Doe")
		
		# Test with list data (stored as JSON string first, then test as list)
		list_data = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]
		with get_test_intgw_notification(json.dumps(list_data)) as doc:
			result = doc.resolve_path("$[*].id")
			self.assertEqual(result, [1, 2])
			
			result = doc.resolve_path("$[0].name")
			self.assertEqual(result, "Item 1")
			
			# Test with list data directly set after creation
			doc.json_payload = list_data
			result = doc.resolve_path("$[*].id")
			self.assertEqual(result, [1, 2])
	
	def test_empty_and_null_data(self):
		"""Test handling of empty and null JSON data"""
		# Test with valid empty JSON object first, then manipulate
		with get_test_intgw_notification("{}") as doc:
			# Test None data by setting it after creation
			doc.json_payload = None
			result = doc.resolve_path("$.anything", "default_value")
			self.assertEqual(result, "default_value")
		
		# Test with valid JSON first, then set empty string
		with get_test_intgw_notification("{}") as doc:
			doc.json_payload = ""
			result = doc.resolve_path("$.anything", "empty_default")
			self.assertEqual(result, "empty_default")
		
		# Test with empty JSON object
		with get_test_intgw_notification("{}") as doc:
			result = doc.resolve_path("$.missing", "not_found")
			self.assertEqual(result, "not_found")
	
	def test_input_validation_errors(self):
		"""Test input validation and error handling"""
		with get_test_intgw_notification(json.dumps(self.sample_notification_data)) as doc:
			# Test non-string path - Frappe now does type validation at the decorator level
			# We need to test this differently since Frappe catches it before our validation
			try:
				doc.resolve_path(123)  # This will raise FrappeTypeError
				self.fail("Should have raised an error for non-string path")
			except Exception as e:
				# Accept either our ValidationError or Frappe's type error
				self.assertTrue(
					isinstance(e, (ValidationError, frappe.exceptions.FrappeTypeError))
				)
			
			# Test empty path - this should still work as it passes type validation
			with self.assertRaises(ValidationError) as cm:
				doc.resolve_path("")
			self.assertIn("Path cannot be empty", str(cm.exception))
			
			# Test whitespace-only path
			with self.assertRaises(ValidationError) as cm:
				doc.resolve_path("   ")
			self.assertIn("Path cannot be empty", str(cm.exception))
			
			# Test non-string field_name - similar to path, this may be caught by Frappe
			try:
				doc.resolve_path("$.test", field_name=123)
				self.fail("Should have raised an error for non-string field_name")
			except Exception as e:
				self.assertTrue(
					isinstance(e, (ValidationError, frappe.exceptions.FrappeTypeError))
				)
	
	def test_json_parsing_errors(self):
		"""Test JSON parsing error handling"""
		# Start with valid JSON, then modify to test invalid JSON handling
		with get_test_intgw_notification('{"valid": "json"}') as doc:
			# Set invalid JSON after document creation to bypass field validation
			doc.json_payload = '{"invalid": json}'
			with self.assertRaises(DataError) as cm:
				doc.resolve_path("$.anything")
			self.assertIn("Invalid JSON", str(cm.exception))
			
			# Test malformed JSON
			doc.json_payload = '{"unclosed": "object"'
			with self.assertRaises(DataError) as cm:
				doc.resolve_path("$.test")
			self.assertIn("Invalid JSON", str(cm.exception))
	
	def test_jsonpath_compilation_errors(self):
		"""Test JSONPath expression compilation errors"""
		with get_test_intgw_notification(json.dumps(self.sample_notification_data)) as doc:
			# Test invalid JSONPath syntax
			with self.assertRaises(DataError) as cm:
				doc.resolve_path("$.[invalid path")
			self.assertIn("Invalid JSONPath expression", str(cm.exception))
			
			# Test malformed expression
			with self.assertRaises(DataError) as cm:
				doc.resolve_path("$.{invalid}")
			self.assertIn("Invalid JSONPath expression", str(cm.exception))
	
	def test_unsupported_data_types(self):
		"""Test handling of unsupported data types"""
		# Start with valid JSON, then modify to test unsupported types
		with get_test_intgw_notification('{"valid": "json"}') as doc:
			# Test with integer data by setting it after creation
			doc.json_payload = 12345
			with self.assertRaises(ValidationError) as cm:
				doc.resolve_path("$.anything")
			self.assertIn("must contain JSON string or object", str(cm.exception))
			
			# Test with float data
			doc.json_payload = 123.45
			with self.assertRaises(ValidationError) as cm:
				doc.resolve_path("$.test")
			self.assertIn("must contain JSON string or object", str(cm.exception))
	
	def test_custom_field_names(self):
		"""Test resolve_path with custom field names"""
		# Create a document with data in a different field
		doc = frappe.new_doc("INTGW Notification")
		doc.json_payload = json.dumps({"original": "data"})
		
		# Add custom field data (simulate having multiple JSON fields)
		custom_data = {"custom": {"value": "test_value"}}
		setattr(doc, 'custom_json_field', json.dumps(custom_data))
		
		doc.insert()
		
		try:
			# Test default field
			result = doc.resolve_path("$.original")
			self.assertEqual(result, "data")
			
			# Test custom field name
			# Note: This simulates how it would work if the field existed
			# In practice, you'd need to add the field to the DocType
			result = doc.resolve_path("$.custom.value", field_name='custom_json_field')
			self.assertEqual(result, "test_value")
		finally:
			doc.delete()
	
	def test_complex_real_world_scenarios(self):
		"""Test complex real-world JSON structures"""
		with get_test_intgw_notification(json.dumps(self.complex_data)) as doc:
			# Test event information
			result = doc.resolve_path("$.event")
			self.assertEqual(result, "order_created")
			
			# Test customer tier
			result = doc.resolve_path("$.customer.tier")
			self.assertEqual(result, "premium")
			
			# Test order item processing
			result = doc.resolve_path("$.order.items[*].name")
			self.assertEqual(result, ["Widget A", "Gadget B"])
			
			# Test quantity summation data
			result = doc.resolve_path("$.order.items[*].quantity")
			self.assertEqual(result, [2, 1])
			
			# Test address components
			result = doc.resolve_path("$.shipping.address.street")
			self.assertEqual(result, "123 Main St")
			
			# Test nested object access
			result = doc.resolve_path("$.shipping.address")
			expected = {
				"street": "123 Main St",
				"city": "New York", 
				"state": "NY",
				"zip": "10001"
			}
			self.assertEqual(result, expected)
	
	def test_performance_edge_cases(self):
		"""Test performance-related edge cases"""
		# Test with large array
		large_data = {
			"items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]
		}
		
		with get_test_intgw_notification(json.dumps(large_data)) as doc:
			# Test wildcard on large array
			result = doc.resolve_path("$.items[*].id")
			self.assertEqual(len(result), 1000)
			self.assertEqual(result[0], 0)
			self.assertEqual(result[-1], 999)
			
			# Test specific index
			result = doc.resolve_path("$.items[500].value")
			self.assertEqual(result, "item_500")
	
	def test_single_vs_multiple_results(self):
		"""Test return behavior for single vs multiple results"""
		with get_test_intgw_notification(json.dumps(self.sample_notification_data)) as doc:
			# Single result should return the value directly
			result = doc.resolve_path("$.user.name")
			self.assertIsInstance(result, str)
			self.assertEqual(result, "John Doe")
			
			# Multiple results should return a list
			result = doc.resolve_path("$.orders[*].id")
			self.assertIsInstance(result, list)
			self.assertEqual(result, [1, 2, 3])
			
			# Single result from array should return the value
			result = doc.resolve_path("$.orders[0].id")
			self.assertIsInstance(result, int)
			self.assertEqual(result, 1)
	
	def test_method_whitelist_integration(self):
		"""Test that resolve_path method is properly whitelisted"""
		with get_test_intgw_notification(json.dumps(self.sample_notification_data)) as doc:
			# The method should be callable (whitelist is checked at runtime)
			# This test ensures the decorator is properly applied
			result = doc.resolve_path("$.user.name")
			self.assertEqual(result, "John Doe")
			
			# Test the test_template method as well
			result = doc.test_template()
			self.assertEqual(result, "Hey, i am alive!")
	
	def test_template_integration_compatibility(self):
		"""Test compatibility with template integration patterns"""
		# This tests the patterns that would be used in Jinja templates
		with get_test_intgw_notification(json.dumps(self.complex_data)) as doc:
			# Test patterns commonly used in templates
			customer_name = doc.resolve_path("$.customer.name", "Unknown Customer")
			self.assertEqual(customer_name, "Alice Johnson")
			
			# Test array processing patterns
			item_names = doc.resolve_path("$.order.items[*].name", [])
			self.assertIsInstance(item_names, list)
			self.assertEqual(len(item_names), 2)
			
			# Test conditional data patterns
			campaign = doc.resolve_path("$.metadata.campaign", None)
			priority = doc.resolve_path("$.priority", "normal")
			self.assertIsNone(campaign)  # Not in complex_data
			self.assertEqual(priority, "normal")  # Default value
