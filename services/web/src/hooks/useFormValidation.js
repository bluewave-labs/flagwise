import { useState, useEffect } from 'react';

export const useFormValidation = (initialState, validationRules) => {
  const [values, setValues] = useState(initialState);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  // Validate a single field
  const validateField = (name, value) => {
    const rules = validationRules[name];
    if (!rules) return null;

    for (const rule of rules) {
      const error = rule(value, values);
      if (error) return error;
    }
    return null;
  };

  // Validate all fields
  const validateAll = () => {
    const newErrors = {};
    let isValid = true;

    Object.keys(validationRules).forEach(name => {
      const error = validateField(name, values[name]);
      if (error) {
        newErrors[name] = error;
        isValid = false;
      }
    });

    setErrors(newErrors);
    return isValid;
  };

  // Handle input change
  const handleChange = (name, value) => {
    setValues(prev => ({ ...prev, [name]: value }));
    
    // Real-time validation for touched fields
    if (touched[name]) {
      const error = validateField(name, value);
      setErrors(prev => ({
        ...prev,
        [name]: error
      }));
    }
  };

  // Handle input blur
  const handleBlur = (name) => {
    setTouched(prev => ({ ...prev, [name]: true }));
    const error = validateField(name, values[name]);
    setErrors(prev => ({
      ...prev,
      [name]: error
    }));
  };

  // Reset form
  const reset = () => {
    setValues(initialState);
    setErrors({});
    setTouched({});
  };

  const isValid = Object.keys(errors).length === 0;

  return {
    values,
    errors,
    touched,
    isValid,
    handleChange,
    handleBlur,
    validateAll,
    reset,
    setValues
  };
};

// Common validation rules
export const validationRules = {
  required: (value) => !value || value.trim() === '' ? 'This field is required' : null,
  
  minLength: (min) => (value) => 
    value && value.length < min ? `Must be at least ${min} characters` : null,
  
  maxLength: (max) => (value) => 
    value && value.length > max ? `Must be no more than ${max} characters` : null,
  
  email: (value) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return value && !emailRegex.test(value) ? 'Please enter a valid email address' : null;
  },
  
  username: (value) => {
    const usernameRegex = /^[a-zA-Z0-9_-]+$/;
    return value && !usernameRegex.test(value) ? 'Username can only contain letters, numbers, hyphens, and underscores' : null;
  },
  
  passwordStrength: (value) => {
    if (!value) return null;
    if (value.length < 6) return 'Password must be at least 6 characters';
    if (!/[A-Za-z]/.test(value)) return 'Password must contain at least one letter';
    if (!/[0-9]/.test(value)) return 'Password must contain at least one number';
    return null;
  },
  
  passwordMatch: (confirmField) => (value, allValues) => {
    return value && value !== allValues[confirmField] ? 'Passwords do not match' : null;
  },
  
  numeric: (value) => {
    return value && isNaN(value) ? 'Must be a valid number' : null;
  },
  
  positiveNumber: (value) => {
    return value && (isNaN(value) || Number(value) <= 0) ? 'Must be a positive number' : null;
  }
};