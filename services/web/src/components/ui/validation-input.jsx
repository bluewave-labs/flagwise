import React from 'react';
import { Input } from './input';
import { AlertCircle } from 'lucide-react';

export const ValidationInput = React.forwardRef(({ 
  className, 
  error, 
  touched, 
  onBlur,
  name,
  ...props 
}, ref) => {
  const hasError = touched && error;

  const handleBlur = (e) => {
    onBlur?.(name);
    props.onBlur?.(e);
  };

  return (
    <div className="space-y-1">
      <Input
        {...props}
        ref={ref}
        name={name}
        className={`${className} ${hasError ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
        onBlur={handleBlur}
      />
      {hasError && (
        <div className="flex items-center text-red-600 text-sm">
          <AlertCircle className="h-3 w-3 mr-1 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
});

ValidationInput.displayName = 'ValidationInput';