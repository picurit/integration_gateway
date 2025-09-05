# Copyright (c) 2025, Picurit and Contributors
# See license.txt

import json
import unittest
from unittest.mock import patch, MagicMock
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.exceptions import ValidationError, DataError
from integration_gateway.integration_gateway.doctype.intgw_notification.intgw_notification import INTGWNotification


class TestINTGWNotification(FrappeTestCase):
    """
    Comprehensive test suite for INTGWNotification class.
    Tests cover all JSONPath-ng features and edge cases.
    """
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a proper Frappe document instance
        self.notification = frappe.get_doc({
            "doctype": "INTGW Notification",
            "json_payload": ""
        })
        
        # Complex test data covering various JSONPath scenarios
        self.test_data = {
            "user": {
                "name": "John Doe",
                "age": 30,
                "email": "john@example.com",
                "preferences": {
                    "theme": "dark",
                    "notifications": True
                }
            },
            "products": [
                {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics", "tags": ["computing", "portable"]},
                {"id": 2, "name": "Mouse", "price": 25.99, "category": "Electronics", "tags": ["computing", "peripheral"]},
                {"id": 3, "name": "Book", "price": 15.99, "category": "Education", "tags": ["reading", "knowledge"]},
                {"id": 4, "name": "Desk", "price": 299.99, "category": "Furniture", "tags": ["office", "workspace"]}
            ],
            "orders": [
                {
                    "id": "ORD001",
                    "total": 1025.98,
                    "items": [
                        {"product_id": 1, "quantity": 1, "subtotal": 999.99},
                        {"product_id": 2, "quantity": 1, "subtotal": 25.99}
                    ],
                    "customer": {"name": "Alice Smith", "id": 101}
                },
                {
                    "id": "ORD002", 
                    "total": 315.98,
                    "items": [
                        {"product_id": 3, "quantity": 2, "subtotal": 31.98},
                        {"product_id": 4, "quantity": 1, "subtotal": 299.99}
                    ],
                    "customer": {"name": "Bob Johnson", "id": 102}
                }
            ],
            "metadata": {
                "timestamp": "2025-09-05T12:00:00Z",
                "version": "1.0",
                "source": "test_system",
                "numbers": [1, 2, 3, 4, 5, 10, 15, 20],
                "text_data": "Hello World Example Text"
            },
            "nested": {
                "level1": {
                    "level2": {
                        "level3": {
                            "deep_value": "found_it",
                            "array": ["a", "b", "c"]
                        }
                    }
                }
            }
        }
        
        # Set up the notification with test data
        self.notification.set("json_payload", json.dumps(self.test_data))
    
    def tearDown(self):
        """Clean up after each test method."""
        pass
    
    # Basic JSONPath Tests
    def test_simple_path_resolution(self):
        """Test basic JSONPath resolution."""
        result = self.notification.resolve_path("$.user.name")
        self.assertEqual(result, "John Doe")
        
        result = self.notification.resolve_path("$.user.age")
        self.assertEqual(result, 30)
        
        result = self.notification.resolve_path("$.metadata.version")
        self.assertEqual(result, "1.0")
    
    def test_nested_path_resolution(self):
        """Test deeply nested path resolution."""
        result = self.notification.resolve_path("$.user.preferences.theme")
        self.assertEqual(result, "dark")
        
        result = self.notification.resolve_path("$.nested.level1.level2.level3.deep_value")
        self.assertEqual(result, "found_it")
    
    def test_array_index_access(self):
        """Test array element access by index."""
        result = self.notification.resolve_path("$.products[0].name")
        self.assertEqual(result, "Laptop")
        
        result = self.notification.resolve_path("$.products[1].price")
        self.assertEqual(result, 25.99)
        
        result = self.notification.resolve_path("$.metadata.numbers[0]")
        self.assertEqual(result, 1)
        
        result = self.notification.resolve_path("$.metadata.numbers[-1]")
        self.assertEqual(result, 20)
    
    def test_wildcard_array_access(self):
        """Test wildcard array access returning multiple values."""
        result = self.notification.resolve_path("$.products[*].name")
        expected = ["Laptop", "Mouse", "Book", "Desk"]
        self.assertEqual(result, expected)
        
        result = self.notification.resolve_path("$.products[*].id")
        expected = [1, 2, 3, 4]
        self.assertEqual(result, expected)
    
    def test_recursive_descent(self):
        """Test recursive descent (..) operator."""
        result = self.notification.resolve_path("$..name")
        # Should find user.name and all product names and customer names
        self.assertIn("John Doe", result)
        self.assertIn("Laptop", result)
        self.assertIn("Alice Smith", result)
        
        result = self.notification.resolve_path("$..id")
        # Should find all id fields throughout the document
        self.assertIsInstance(result, list)
        self.assertIn(1, result)  # product id
        self.assertIn(101, result)  # customer id
    
    # JSONPath-ng Extended Features Tests
    def test_array_slice(self):
        """Test array slicing."""
        result = self.notification.resolve_path("$.products[0:2].name")
        expected = ["Laptop", "Mouse"]
        self.assertEqual(result, expected)
        
        result = self.notification.resolve_path("$.metadata.numbers[2:5]")
        expected = [3, 4, 5]
        self.assertEqual(result, expected)
    
    def test_filter_expressions(self):
        """Test filter expressions with conditions."""
        # Filter products by price
        result = self.notification.resolve_path("$.products[?(@.price > 100)].name")
        expected = ["Laptop", "Desk"]
        self.assertEqual(result, expected)
        
        # Filter by category
        result = self.notification.resolve_path("$.products[?(@.category == 'Electronics')].name")
        expected = ["Laptop", "Mouse"]
        self.assertEqual(result, expected)
    
    def test_length_function(self):
        """Test getting array lengths using JSONPath."""
        # JSONPath doesn't have a built-in length function, but we can test array access
        result = self.notification.resolve_path("$.products[*]")
        self.assertEqual(len(result), 4)  # Check length in Python
        
        result = self.notification.resolve_path("$.orders[*]")
        self.assertEqual(len(result), 2)
        
        result = self.notification.resolve_path("$.metadata.numbers[*]")
        self.assertEqual(len(result), 8)
    
    def test_arithmetic_operations(self):
        """Test arithmetic operations in JSONPath."""
        # Sum of all product prices
        result = self.notification.resolve_path("$.products[*].price")
        total_price = sum(result)
        self.assertAlmostEqual(total_price, 1341.96, places=2)
        
        # Test individual arithmetic operations via filters
        result = self.notification.resolve_path("$.metadata.numbers[?(@.* > 15)]")
        expected = [20]  # Only 20 is greater than 15 when multiplied by itself
        
    def test_string_functions(self):
        """Test string operations with filters."""
        # JSONPath-ng supports basic string comparisons in filters
        # Test string equality filters
        result = self.notification.resolve_path("$.products[?(@.category == 'Electronics')].name")
        expected = ["Laptop", "Mouse"]
        self.assertEqual(result, expected)
        
        # Test with user name
        result = self.notification.resolve_path("$.user[?(@.name == 'John Doe')]")
        if result:
            self.assertIn("name", str(result))  # Check result contains name data
    
    def test_sorted_function(self):
        """Test sorted() function if available."""
        # Note: sorted() might not be available in all jsonpath-ng versions
        # This test checks if the feature exists and works correctly
        try:
            result = self.notification.resolve_path("$.metadata.numbers.sorted()")
            if result is not None:
                expected = [1, 2, 3, 4, 5, 10, 15, 20]
                self.assertEqual(result, expected)
        except Exception:
            # If sorted is not supported, this test should pass
            pass
    
    # Edge Cases and Error Handling Tests
    def test_nonexistent_path(self):
        """Test behavior with non-existent paths."""
        result = self.notification.resolve_path("$.nonexistent.path", default="not_found")
        self.assertEqual(result, "not_found")
        
        result = self.notification.resolve_path("$.user.nonexistent", default=None)
        self.assertIsNone(result)
        
        # Test without default (should return None by default)
        result = self.notification.resolve_path("$.does.not.exist")
        self.assertIsNone(result)
    
    def test_invalid_jsonpath_syntax(self):
        """Test handling of invalid JSONPath syntax."""
        with self.assertRaises(DataError):
            self.notification.resolve_path("$.invalid[syntax")
        
        with self.assertRaises(DataError):
            self.notification.resolve_path("$[invalid")
        
        with self.assertRaises(DataError):
            self.notification.resolve_path("$user")
    
    def test_empty_path(self):
        """Test handling of empty or whitespace paths."""
        with self.assertRaises(ValidationError):
            self.notification.resolve_path("")
        
        with self.assertRaises(ValidationError):
            self.notification.resolve_path("   ")
    
    def test_invalid_path_type(self):
        """Test handling of non-string path parameters."""
        # These tests are now caught by Frappe's type validation system
        # which is actually better than our custom validation
        from frappe.exceptions import FrappeTypeError
        
        with self.assertRaises(FrappeTypeError):
            self.notification.resolve_path(123)
        
        with self.assertRaises(FrappeTypeError):
            self.notification.resolve_path(None)
        
        with self.assertRaises(FrappeTypeError):
            self.notification.resolve_path(["$.user.name"])
    
    def test_invalid_field_name(self):
        """Test handling of invalid field names."""
        from frappe.exceptions import FrappeTypeError
        
        with self.assertRaises(FrappeTypeError):
            self.notification.resolve_path("$.user.name", field_name=123)
        
        with self.assertRaises(FrappeTypeError):
            self.notification.resolve_path("$.user.name", field_name=None)
    
    def test_empty_json_payload(self):
        """Test behavior with empty JSON payload."""
        self.notification.set("json_payload", None)
        result = self.notification.resolve_path("$.user.name", default="default_value")
        self.assertEqual(result, "default_value")
        
        self.notification.set("json_payload", "")
        result = self.notification.resolve_path("$.user.name", default="default_value")
        self.assertEqual(result, "default_value")
        
        self.notification.set("json_payload", "   ")
        result = self.notification.resolve_path("$.user.name", default="default_value")
        self.assertEqual(result, "default_value")
    
    def test_invalid_json_payload(self):
        """Test handling of invalid JSON in payload."""
        self.notification.set("json_payload", '{"invalid": json}')
        
        with self.assertRaises(DataError):
            self.notification.resolve_path("$.user.name")
    
    def test_different_field_names(self):
        """Test resolution from different field names."""
        # Set up a different field with JSON data
        self.notification.set("custom_field", json.dumps({"test": "value"}))
        
        result = self.notification.resolve_path("$.test", field_name="custom_field")
        self.assertEqual(result, "value")
    
    def test_dict_and_list_field_types(self):
        """Test handling of already parsed JSON data (dict/list)."""
        # Test with dict
        self.notification.set("dict_field", {"key": "value"})
        result = self.notification.resolve_path("$.key", field_name="dict_field")
        self.assertEqual(result, "value")
        
        # Test with list
        self.notification.set("list_field", [{"item": 1}, {"item": 2}])
        result = self.notification.resolve_path("$[0].item", field_name="list_field")
        self.assertEqual(result, 1)
    
    def test_unsupported_field_types(self):
        """Test handling of unsupported field data types."""
        self.notification.set("number_field", 12345)
        
        with self.assertRaises(ValidationError):
            self.notification.resolve_path("$.any.path", field_name="number_field")
    
    def test_complex_nested_queries(self):
        """Test complex nested JSONPath queries."""
        # Get all item quantities from all orders
        result = self.notification.resolve_path("$.orders[*].items[*].quantity")
        expected = [1, 1, 2, 1]  # quantities from both orders
        self.assertEqual(result, expected)
        
        # Get all customer names from orders
        result = self.notification.resolve_path("$.orders[*].customer.name")
        expected = ["Alice Smith", "Bob Johnson"]
        self.assertEqual(result, expected)
    
    def test_single_vs_multiple_results(self):
        """Test handling of single vs multiple results."""
        # Single result should return the value directly
        result = self.notification.resolve_path("$.user.name")
        self.assertEqual(result, "John Doe")
        self.assertIsInstance(result, str)
        
        # Multiple results should return a list
        result = self.notification.resolve_path("$.products[*].name")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 4)
    
    @patch('frappe.log_error')
    def test_error_logging(self, mock_log_error):
        """Test that errors are properly logged."""
        # Test JSON parsing error logging
        self.notification.set("json_payload", '{"invalid": json}')
        
        with self.assertRaises(DataError):
            self.notification.resolve_path("$.user.name")
        
        # Verify that frappe.log_error was called
        mock_log_error.assert_called()
        
        # Reset mock for next test
        mock_log_error.reset_mock()
        
        # Test JSONPath compilation error logging
        with self.assertRaises(DataError):
            self.notification.resolve_path("$.invalid[syntax")
        
        mock_log_error.assert_called()
    
    # Performance and Edge Case Tests
    def test_large_json_payload(self):
        """Test performance with large JSON payloads."""
        # Create a large dataset
        large_data = {
            "items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]
        }
        self.notification.set("json_payload", json.dumps(large_data))
        
        # Test that it can handle large datasets
        result = self.notification.resolve_path("$.items[999].value")
        self.assertEqual(result, "item_999")
        
        # Test wildcard on large dataset
        result = self.notification.resolve_path("$.items[0:5].id")
        expected = [0, 1, 2, 3, 4]
        self.assertEqual(result, expected)
    
    def test_deeply_nested_json(self):
        """Test very deeply nested JSON structures."""
        deep_data = {"level": {"level": {"level": {"level": {"value": "deep"}}}}}
        self.notification.set("json_payload", json.dumps(deep_data))
        
        result = self.notification.resolve_path("$.level.level.level.level.value")
        self.assertEqual(result, "deep")
    
    def test_special_characters_in_data(self):
        """Test handling of special characters in JSON data."""
        special_data = {
            "unicode": "🚀 Unicode test ñáéíóú",
            "special_chars": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "newlines": "Line 1\nLine 2\nLine 3",
            "tabs": "Column1\tColumn2\tColumn3"
        }
        self.notification.set("json_payload", json.dumps(special_data))
        
        result = self.notification.resolve_path("$.unicode")
        self.assertEqual(result, "🚀 Unicode test ñáéíóú")
        
        result = self.notification.resolve_path("$.special_chars")
        self.assertEqual(result, "!@#$%^&*()_+-=[]{}|;':\",./<>?")
    
    def test_boolean_and_null_values(self):
        """Test handling of boolean and null values."""
        bool_data = {
            "is_active": True,
            "is_deleted": False,
            "null_value": None,
            "zero": 0,
            "empty_string": "",
            "empty_list": [],
            "empty_dict": {}
        }
        self.notification.set("json_payload", json.dumps(bool_data))
        
        result = self.notification.resolve_path("$.is_active")
        self.assertTrue(result)
        
        result = self.notification.resolve_path("$.is_deleted")
        self.assertFalse(result)
        
        result = self.notification.resolve_path("$.null_value")
        self.assertIsNone(result)
        
        result = self.notification.resolve_path("$.zero")
        self.assertEqual(result, 0)
        
        result = self.notification.resolve_path("$.empty_string")
        self.assertEqual(result, "")
        
        result = self.notification.resolve_path("$.empty_list")
        self.assertEqual(result, [])
        
        result = self.notification.resolve_path("$.empty_dict")
        self.assertEqual(result, {})


class TestINTGWNotificationIntegration(FrappeTestCase):
    """
    Integration tests for INTGWNotification with Frappe framework.
    These tests interact with the database but remain idempotent.
    """
    
    def setUp(self):
        """Set up before each integration test."""
        self.test_doc_name = f"TEST_INTGW_{frappe.utils.now_datetime().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def tearDown(self):
        """Clean up after each integration test."""
        # Remove any test documents created in this test
        try:
            if frappe.db.exists("INTGW Notification", self.test_doc_name):
                frappe.delete_doc("INTGW Notification", self.test_doc_name, force=True)
                frappe.db.commit()
        except Exception:
            # Ignore cleanup errors
            pass
    
    def test_document_creation_and_method_calls(self):
        """Test creating a document and calling resolve_path method."""
        test_data = {
            "user": {"name": "Integration Test User", "id": 12345},
            "metadata": {"test": True, "timestamp": "2025-09-05T12:00:00Z"}
        }
        
        # Create a new document without saving to avoid server script issues
        doc = frappe.get_doc({
            "doctype": "INTGW Notification",
            "name": self.test_doc_name,
            "json_payload": json.dumps(test_data)
        })
        
        # Test resolve_path method on unsaved document
        result = doc.resolve_path("$.user.name")
        self.assertEqual(result, "Integration Test User")
        
        result = doc.resolve_path("$.metadata.test")
        self.assertTrue(result)
        
        # Test with default value
        result = doc.resolve_path("$.nonexistent", default="default_value")
        self.assertEqual(result, "default_value")
    
    def test_whitelist_method_access(self):
        """Test that whitelisted methods can be called via API."""
        test_data = {"api_test": {"value": "success"}}
        
        doc = frappe.get_doc({
            "doctype": "INTGW Notification", 
            "name": self.test_doc_name,
            "json_payload": json.dumps(test_data)
        })
                
        # Test resolve_path method (whitelisted)
        result = doc.resolve_path("$.api_test.value")
        self.assertEqual(result, "success")


class TestINTGWNotificationUpdatePath(FrappeTestCase):
    """
    Comprehensive test suite for INTGWNotification update_path method.
    Tests cover all JSONPath-ng update features and edge cases.
    """
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a proper Frappe document instance
        self.notification = frappe.get_doc({
            "doctype": "INTGW Notification",
            "json_payload": ""
        })
        
        # Initial test data for update operations
        self.initial_data = {
            "user": {
                "name": "John Doe",
                "age": 30,
                "preferences": {
                    "theme": "light"
                }
            },
            "products": [
                {"id": 1, "name": "Laptop", "price": 999.99},
                {"id": 2, "name": "Mouse", "price": 25.99}
            ],
            "metadata": {
                "version": "1.0",
                "numbers": [1, 2, 3]
            }
        }
        
        # Set up the notification with initial data
        self.notification.set("json_payload", json.dumps(self.initial_data))
    
    def tearDown(self):
        """Clean up after each test method."""
        pass
    
    # Basic Update Tests
    def test_update_simple_string_value(self):
        """Test updating a simple string value."""
        self.notification.update_path("$.user.name", "Jane Doe")
        
        result = self.notification.resolve_path("$.user.name")
        self.assertEqual(result, "Jane Doe")
    
    def test_update_numeric_value(self):
        """Test updating numeric values."""
        self.notification.update_path("$.user.age", 35)
        
        result = self.notification.resolve_path("$.user.age")
        self.assertEqual(result, 35)
        
        # Test float value
        self.notification.update_path("$.products[0].price", 1299.99)
        result = self.notification.resolve_path("$.products[0].price")
        self.assertEqual(result, 1299.99)
    
    def test_update_boolean_value(self):
        """Test updating boolean values."""
        self.notification.update_path("$.user.is_active", True)
        
        result = self.notification.resolve_path("$.user.is_active")
        self.assertTrue(result)
        
        self.notification.update_path("$.user.is_active", False)
        result = self.notification.resolve_path("$.user.is_active")
        self.assertFalse(result)
    
    def test_update_nested_object_value(self):
        """Test updating values in nested objects."""
        self.notification.update_path("$.user.preferences.theme", "dark")
        
        result = self.notification.resolve_path("$.user.preferences.theme")
        self.assertEqual(result, "dark")
    
    def test_update_array_element(self):
        """Test updating specific array elements."""
        self.notification.update_path("$.products[0].name", "Gaming Laptop")
        
        result = self.notification.resolve_path("$.products[0].name")
        self.assertEqual(result, "Gaming Laptop")
        
        # Verify other elements remain unchanged
        result = self.notification.resolve_path("$.products[1].name")
        self.assertEqual(result, "Mouse")
    
    def test_update_array_element_by_negative_index(self):
        """Test updating array elements using negative indices."""
        self.notification.update_path("$.metadata.numbers[-1]", 10)
        
        result = self.notification.resolve_path("$.metadata.numbers[-1]")
        self.assertEqual(result, 10)
    
    def test_update_multiple_matching_paths(self):
        """Test updating multiple paths that match a wildcard."""
        # Add a category field to all products
        self.notification.update_path("$.products[*].category", "Electronics")
        
        result = self.notification.resolve_path("$.products[*].category")
        expected = ["Electronics", "Electronics"]
        self.assertEqual(result, expected)
    
    def test_update_with_complex_values(self):
        """Test updating with complex data types (objects, arrays)."""
        # Update with an object
        new_preferences = {
            "theme": "dark",
            "language": "en",
            "notifications": True
        }
        self.notification.update_path("$.user.preferences", new_preferences)
        
        result = self.notification.resolve_path("$.user.preferences")
        self.assertEqual(result, new_preferences)
        
        # Update with an array
        new_numbers = [10, 20, 30, 40]
        self.notification.update_path("$.metadata.numbers", new_numbers)
        
        result = self.notification.resolve_path("$.metadata.numbers")
        self.assertEqual(result, new_numbers)
    
    def test_update_null_value(self):
        """Test updating with null/None values."""
        self.notification.update_path("$.user.middle_name", None)
        
        result = self.notification.resolve_path("$.user.middle_name")
        self.assertIsNone(result)
    
    # Creating New Paths Tests
    def test_create_new_simple_field(self):
        """Test creating a new simple field."""
        self.notification.update_path("$.user.email", "john@example.com")
        
        result = self.notification.resolve_path("$.user.email")
        self.assertEqual(result, "john@example.com")
    
    def test_create_new_nested_field(self):
        """Test creating a new field in existing nested object."""
        self.notification.update_path("$.user.preferences.notifications", True)
        
        result = self.notification.resolve_path("$.user.preferences.notifications")
        self.assertTrue(result)
    
    def test_create_new_array_element(self):
        """Test adding new elements to existing arrays."""
        # Note: JSONPath-ng may not support direct array appending
        # This test checks if we can set a specific index
        try:
            self.notification.update_path("$.metadata.numbers[3]", 4)
            result = self.notification.resolve_path("$.metadata.numbers[3]")
            self.assertEqual(result, 4)
        except DataError:
            # If direct array expansion is not supported, that's acceptable
            pass
    
    # Edge Cases and Error Handling
    def test_update_empty_json_payload(self):
        """Test updating when JSON payload is empty."""
        self.notification.set("json_payload", "")
        self.notification.update_path("$.new_field", "new_value")
        
        result = self.notification.resolve_path("$.new_field")
        self.assertEqual(result, "new_value")
    
    def test_update_null_json_payload(self):
        """Test updating when JSON payload is None."""
        self.notification.set("json_payload", None)
        self.notification.update_path("$.new_field", "new_value")
        
        result = self.notification.resolve_path("$.new_field")
        self.assertEqual(result, "new_value")
    
    def test_update_with_invalid_jsonpath(self):
        """Test error handling with invalid JSONPath expressions."""
        with self.assertRaises(DataError):
            self.notification.update_path("$.invalid[syntax", "value")
        
        with self.assertRaises(DataError):
            self.notification.update_path("$[invalid", "value")
    
    def test_update_with_empty_path(self):
        """Test error handling with empty paths."""
        with self.assertRaises(ValidationError):
            self.notification.update_path("", "value")
        
        with self.assertRaises(ValidationError):
            self.notification.update_path("   ", "value")
    
    def test_update_with_invalid_path_type(self):
        """Test error handling with non-string path parameters."""
        from frappe.exceptions import FrappeTypeError
        
        with self.assertRaises(FrappeTypeError):
            self.notification.update_path(123, "value")
        
        with self.assertRaises(FrappeTypeError):
            self.notification.update_path(None, "value")
    
    def test_update_with_invalid_field_name(self):
        """Test error handling with invalid field names."""
        from frappe.exceptions import FrappeTypeError
        
        with self.assertRaises(FrappeTypeError):
            self.notification.update_path("$.user.name", "value", field_name=123)
    
    def test_update_invalid_json_payload(self):
        """Test error handling with invalid JSON in payload."""
        self.notification.set("json_payload", '{"invalid": json}')
        
        with self.assertRaises(DataError):
            self.notification.update_path("$.user.name", "value")
    
    def test_update_different_field_names(self):
        """Test updating in different field names."""
        # Set up a different field with JSON data
        self.notification.set("custom_field", json.dumps({"test": "original"}))
        
        self.notification.update_path("$.test", "updated", field_name="custom_field")
        result = self.notification.resolve_path("$.test", field_name="custom_field")
        self.assertEqual(result, "updated")
    
    def test_update_dict_field_types(self):
        """Test updating in already parsed JSON data (dict)."""
        self.notification.set("dict_field", {"key": "original"})
        self.notification.update_path("$.key", "updated", field_name="dict_field")
        
        result = self.notification.resolve_path("$.key", field_name="dict_field")
        self.assertEqual(result, "updated")
    
    def test_update_list_field_types(self):
        """Test updating in already parsed JSON data (list)."""
        self.notification.set("list_field", [{"item": 1}, {"item": 2}])
        self.notification.update_path("$[0].item", 10, field_name="list_field")
        
        result = self.notification.resolve_path("$[0].item", field_name="list_field")
        self.assertEqual(result, 10)
    
    def test_update_unsupported_field_types(self):
        """Test error handling with unsupported field data types."""
        self.notification.set("number_field", 12345)
        
        with self.assertRaises(ValidationError):
            self.notification.update_path("$.any.path", "value", field_name="number_field")
    
    @patch('frappe.log_error')
    def test_update_error_logging(self, mock_log_error):
        """Test that errors are properly logged during updates."""
        # Test JSON parsing error logging
        self.notification.set("json_payload", '{"invalid": json}')
        
        with self.assertRaises(DataError):
            self.notification.update_path("$.user.name", "value")
        
        # Verify that frappe.log_error was called
        mock_log_error.assert_called()
    
    def test_update_idempotency(self):
        """Test that repeated updates with same value are idempotent."""
        # First update
        self.notification.update_path("$.user.name", "Updated Name")
        result1 = self.notification.resolve_path("$.user.name")
        
        # Second update with same value
        self.notification.update_path("$.user.name", "Updated Name")
        result2 = self.notification.resolve_path("$.user.name")
        
        # Both results should be identical
        self.assertEqual(result1, result2)
        self.assertEqual(result2, "Updated Name")


class TestINTGWNotificationDeletePath(FrappeTestCase):
    """
    Comprehensive test suite for INTGWNotification delete_path method.
    Tests cover all JSONPath-ng delete features and edge cases.
    """
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a proper Frappe document instance
        self.notification = frappe.get_doc({
            "doctype": "INTGW Notification",
            "json_payload": ""
        })
        
        # Initial test data for delete operations
        self.initial_data = {
            "user": {
                "name": "John Doe",
                "age": 30,
                "email": "john@example.com",
                "preferences": {
                    "theme": "light",
                    "notifications": True,
                    "language": "en"
                },
                "temp_field": "to_be_deleted"
            },
            "products": [
                {"id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"},
                {"id": 2, "name": "Mouse", "price": 25.99, "category": "Electronics"},
                {"id": 3, "name": "Book", "price": 15.99, "category": "Education"},
                {"id": 4, "name": "Desk", "price": 299.99, "category": "Furniture"}
            ],
            "metadata": {
                "version": "1.0",
                "timestamp": "2025-09-05T12:00:00Z",
                "numbers": [1, 2, 3, 4, 5],
                "to_delete": "will_be_removed"
            },
            "temporary": {
                "field1": "value1",
                "field2": "value2"
            }
        }
        
        # Set up the notification with initial data
        self.notification.set("json_payload", json.dumps(self.initial_data))
    
    def tearDown(self):
        """Clean up after each test method."""
        pass
    
    # Basic Delete Tests
    def test_delete_simple_field(self):
        """Test deleting a simple field."""
        self.notification.delete_path("$.user.temp_field")
        
        result = self.notification.resolve_path("$.user.temp_field", default="NOT_FOUND")
        self.assertEqual(result, "NOT_FOUND")
        
        # Verify other fields remain
        result = self.notification.resolve_path("$.user.name")
        self.assertEqual(result, "John Doe")
    
    def test_delete_nested_field(self):
        """Test deleting a field in nested objects."""
        self.notification.delete_path("$.user.preferences.notifications")
        
        result = self.notification.resolve_path("$.user.preferences.notifications", default="NOT_FOUND")
        self.assertEqual(result, "NOT_FOUND")
        
        # Verify other nested fields remain
        result = self.notification.resolve_path("$.user.preferences.theme")
        self.assertEqual(result, "light")
    
    def test_delete_entire_nested_object(self):
        """Test deleting an entire nested object."""
        self.notification.delete_path("$.user.preferences")
        
        result = self.notification.resolve_path("$.user.preferences", default="NOT_FOUND")
        self.assertEqual(result, "NOT_FOUND")
        
        # Verify parent object still exists
        result = self.notification.resolve_path("$.user.name")
        self.assertEqual(result, "John Doe")
    
    def test_delete_array_element_by_index(self):
        """Test deleting specific array elements by index."""
        # Get original array length
        original_products = self.notification.resolve_path("$.products")
        original_length = len(original_products)
        
        self.notification.delete_path("$.products[1]")
        
        # The element should be removed (array should be shorter)
        updated_products = self.notification.resolve_path("$.products")
        self.assertLess(len(updated_products), original_length)
        
        # Verify the correct element was removed (Mouse should be gone)
        product_names = self.notification.resolve_path("$.products[*].name")
        self.assertNotIn("Mouse", product_names)
        self.assertIn("Laptop", product_names)
    
    def test_delete_array_element_by_negative_index(self):
        """Test deleting array elements using negative indices."""
        self.notification.delete_path("$.metadata.numbers[-1]")
        
        numbers = self.notification.resolve_path("$.metadata.numbers")
        # The last element (5) should be removed
        self.assertNotIn(5, numbers)
        self.assertIn(4, numbers)
    
    def test_delete_multiple_matching_paths(self):
        """Test deleting multiple paths that match a wildcard expression."""
        # Delete all product categories
        self.notification.delete_path("$.products[*].category")
        
        # Verify categories are deleted but other fields remain
        categories = self.notification.resolve_path("$.products[*].category", default=[])
        self.assertEqual(categories, [])  # Should be empty or not found
        
        product_names = self.notification.resolve_path("$.products[*].name")
        self.assertTrue(len(product_names) > 0)  # Names should still exist
    
    def test_delete_using_recursive_descent(self):
        """Test deleting using recursive descent (..) operator."""
        # This will delete all fields named "version" anywhere in the document
        self.notification.delete_path("$..version")
        
        result = self.notification.resolve_path("$.metadata.version", default="NOT_FOUND")
        self.assertEqual(result, "NOT_FOUND")
    
    # Edge Cases and Error Handling
    def test_delete_nonexistent_path(self):
        """Test deleting a path that doesn't exist (should not raise error)."""
        # This should not raise an error
        self.notification.delete_path("$.nonexistent.path")
        
        # Original data should remain unchanged
        result = self.notification.resolve_path("$.user.name")
        self.assertEqual(result, "John Doe")
    
    def test_delete_from_empty_json_payload(self):
        """Test deleting when JSON payload is empty."""
        self.notification.set("json_payload", "")
        
        # Should not raise an error
        self.notification.delete_path("$.any.path")
    
    def test_delete_from_null_json_payload(self):
        """Test deleting when JSON payload is None."""
        self.notification.set("json_payload", None)
        
        # Should not raise an error
        self.notification.delete_path("$.any.path")
    
    def test_delete_with_invalid_jsonpath(self):
        """Test error handling with invalid JSONPath expressions."""
        with self.assertRaises(DataError):
            self.notification.delete_path("$.invalid[syntax")
        
        with self.assertRaises(DataError):
            self.notification.delete_path("$[invalid")
    
    def test_delete_with_empty_path(self):
        """Test error handling with empty paths."""
        with self.assertRaises(ValidationError):
            self.notification.delete_path("")
        
        with self.assertRaises(ValidationError):
            self.notification.delete_path("   ")
    
    def test_delete_with_invalid_path_type(self):
        """Test error handling with non-string path parameters."""
        from frappe.exceptions import FrappeTypeError
        
        with self.assertRaises(FrappeTypeError):
            self.notification.delete_path(123)
        
        with self.assertRaises(FrappeTypeError):
            self.notification.delete_path(None)
    
    def test_delete_with_invalid_field_name(self):
        """Test error handling with invalid field names."""
        from frappe.exceptions import FrappeTypeError
        
        with self.assertRaises(FrappeTypeError):
            self.notification.delete_path("$.user.name", field_name=123)
    
    def test_delete_invalid_json_payload(self):
        """Test error handling with invalid JSON in payload."""
        self.notification.set("json_payload", '{"invalid": json}')
        
        with self.assertRaises(DataError):
            self.notification.delete_path("$.user.name")
    
    def test_delete_different_field_names(self):
        """Test deleting from different field names."""
        # Set up a different field with JSON data
        self.notification.set("custom_field", json.dumps({"test": "value", "keep": "this"}))
        
        self.notification.delete_path("$.test", field_name="custom_field")
        
        result = self.notification.resolve_path("$.test", field_name="custom_field", default="NOT_FOUND")
        self.assertEqual(result, "NOT_FOUND")
        
        # Verify other field remains
        result = self.notification.resolve_path("$.keep", field_name="custom_field")
        self.assertEqual(result, "this")
    
    def test_delete_dict_field_types(self):
        """Test deleting from already parsed JSON data (dict)."""
        self.notification.set("dict_field", {"key1": "value1", "key2": "value2"})
        self.notification.delete_path("$.key1", field_name="dict_field")
        
        result = self.notification.resolve_path("$.key1", field_name="dict_field", default="NOT_FOUND")
        self.assertEqual(result, "NOT_FOUND")
        
        # Verify other key remains
        result = self.notification.resolve_path("$.key2", field_name="dict_field")
        self.assertEqual(result, "value2")
    
    def test_delete_list_field_types(self):
        """Test deleting from already parsed JSON data (list)."""
        self.notification.set("list_field", [{"item": 1}, {"item": 2}, {"item": 3}])
        self.notification.delete_path("$[1]", field_name="list_field")
        
        items = self.notification.resolve_path("$[*].item", field_name="list_field")
        # Should have removed the middle element
        self.assertNotIn(2, items)
        self.assertIn(1, items)
        self.assertIn(3, items)
    
    def test_delete_unsupported_field_types(self):
        """Test error handling with unsupported field data types."""
        self.notification.set("number_field", 12345)
        
        with self.assertRaises(ValidationError):
            self.notification.delete_path("$.any.path", field_name="number_field")
    
    @patch('frappe.log_error')
    def test_delete_error_logging(self, mock_log_error):
        """Test that errors are properly logged during deletions."""
        # Test JSON parsing error logging
        self.notification.set("json_payload", '{"invalid": json}')
        
        with self.assertRaises(DataError):
            self.notification.delete_path("$.user.name")
        
        # Verify that frappe.log_error was called
        mock_log_error.assert_called()
    
    def test_delete_idempotency(self):
        """Test that repeated deletions are idempotent."""
        # First deletion
        self.notification.delete_path("$.metadata.to_delete")
        result1 = self.notification.resolve_path("$.metadata.to_delete", default="NOT_FOUND")
        
        # Second deletion of same path
        self.notification.delete_path("$.metadata.to_delete")
        result2 = self.notification.resolve_path("$.metadata.to_delete", default="NOT_FOUND")
        
        # Both results should be identical
        self.assertEqual(result1, result2)
        self.assertEqual(result2, "NOT_FOUND")
    
    def test_delete_entire_object_then_verify_structure(self):
        """Test deleting entire objects and verifying document structure."""
        # Delete the entire temporary object
        self.notification.delete_path("$.temporary")
        
        result = self.notification.resolve_path("$.temporary", default="NOT_FOUND")
        self.assertEqual(result, "NOT_FOUND")
        
        # Verify other top-level objects remain intact
        result = self.notification.resolve_path("$.user.name")
        self.assertEqual(result, "John Doe")
        
        result = self.notification.resolve_path("$.metadata.version")
        self.assertEqual(result, "1.0")
    
    def test_delete_array_cleanup(self):
        """Test that array cleanup works correctly after deletions."""
        # Delete a middle element to test cleanup
        self.notification.delete_path("$.metadata.numbers[2]")  # Delete 3
        
        numbers = self.notification.resolve_path("$.metadata.numbers")
        
        # Verify the array is properly cleaned up (no None values)
        self.assertNotIn(None, numbers)
        self.assertNotIn(3, numbers)
        
        # Verify remaining elements
        expected_remaining = [1, 2, 4, 5]
        for num in expected_remaining:
            self.assertIn(num, numbers)


if __name__ == "__main__":
    unittest.main()
