import React from 'react';
import { PasswordInput } from './password-input';
import { AlertCircle, Check } from 'lucide-react';

export const ValidationPasswordInput = React.forwardRef(({ 
  className, 
  error, 
  touched, 
  onBlur,
  name,
  showStrengthMeter = false,
  value,
  ...props 
}, ref) => {
  const hasError = touched && error;

  const handleBlur = (e) => {
    onBlur?.(name);
    props.onBlur?.(e);
  };

  // Password strength indicators
  const getPasswordStrength = (password) => {
    if (!password) return { score: 0, requirements: [] };
    
    const requirements = [
      { test: password.length >= 6, text: 'At least 6 characters' },
      { test: /[A-Za-z]/.test(password), text: 'Contains letters' },
      { test: /[0-9]/.test(password), text: 'Contains numbers' },
      { test: /[^A-Za-z0-9]/.test(password), text: 'Contains special characters' }
    ];

    const score = requirements.filter(req => req.test).length;
    return { score, requirements };
  };

  const strength = showStrengthMeter ? getPasswordStrength(value) : null;

  return (
    <div className="space-y-2">
      <PasswordInput
        {...props}
        ref={ref}
        name={name}
        value={value}
        className={`${className} ${hasError ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
        onBlur={handleBlur}
      />
      
      {hasError && (
        <div className="flex items-center text-red-600 text-sm">
          <AlertCircle className="h-3 w-3 mr-1 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {showStrengthMeter && value && strength && (
        <div className="space-y-2">
          <div className="flex space-x-1">
            {[1, 2, 3, 4].map((level) => (
              <div
                key={level}
                className={`h-1 flex-1 rounded-full ${
                  strength.score >= level
                    ? strength.score === 1
                      ? 'bg-red-500'
                      : strength.score === 2
                      ? 'bg-yellow-500'
                      : strength.score === 3
                      ? 'bg-blue-500'
                      : 'bg-green-500'
                    : 'bg-gray-200'
                }`}
              />
            ))}
          </div>
          <div className="text-xs space-y-1">
            {strength.requirements.map((req, index) => (
              <div key={index} className={`flex items-center ${req.test ? 'text-green-600' : 'text-gray-400'}`}>
                <Check className={`h-3 w-3 mr-1 ${req.test ? 'opacity-100' : 'opacity-30'}`} />
                <span>{req.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
});

ValidationPasswordInput.displayName = 'ValidationPasswordInput';