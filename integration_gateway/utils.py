import frappe
from frappe.model.document import Document
from frappe import is_whitelisted as validate_whitelisted
from frappe.exceptions import PermissionError, DataError


class TemplateDocProxy:
    """
    Template proxy that exposes document fields and guarded methods for webhook templates.
    
    This proxy provides secure access to document methods by ensuring only whitelisted
    methods can be executed through template rendering.
    """
    
    def __init__(self, doc_obj: Document, doc_dict: dict):
        """
        Initialize the proxy with a document object and its dictionary representation.
        
        Args:
            doc_obj (Document): The Frappe document object
            doc_dict (dict): Dictionary representation of the document
        """
        self._doc = doc_obj
        self._dict = doc_dict

    def __getattr__(self, name):
        """
        Provide access to document fields and whitelisted methods.
        
        Args:
            name (str): The attribute name to access
            
        Returns:
            The requested attribute value or method wrapper
            
        Raises:
            AttributeError: If the attribute doesn't exist
            PermissionError: If attempting to call a non-whitelisted method
            DataError: If an error occurs while calling a whitelisted method
        """
        # For simple fields (strings, numbers, lists)
        if name in self._dict:
            return self._dict.get(name)

        # Bound method on the document (guarded)
        maybe = getattr(self._doc, name, None)
        if callable(maybe):
            # underlying function object for bound methods
            method = getattr(maybe, "__func__", maybe)

            def _method_wrapper(*args, **kwargs):
                # Security: allow execution only if the method is whitelisted.
                # validate_whitelisted is an alias for is_whitelisted 
                # is_whitelisted throws PermissionError if not allowed, otherwise continues
                try:
                    validate_whitelisted(method)
                    # If we reach this line, the method is whitelisted
                    return self._doc.run_method(name, *args, **kwargs)
                
                except PermissionError:
                    # Not whitelisted: deny
                    raise

                except Exception as e:
                    # Unhandled exception
                    dotted = f"{method.__module__}.{method.__name__}"
                    raise DataError(f"Error occurred while calling method {dotted}: {e}")

            # return the wrapper callable to Jinja (templates will call it)
            return _method_wrapper

        # Fallback: return other attributes directly from the doc object if present
        if hasattr(self._doc, name):
            return getattr(self._doc, name)

        # Not found
        raise AttributeError(name)

    def as_dict(self):
        """
        Return the dictionary representation of the document.
        
        Returns:
            dict: Dictionary representation of the document
        """
        # if template needs full dict
        return dict(self._dict)
