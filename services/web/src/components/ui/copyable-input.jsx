import React from 'react';
import { Input } from './input';
import { CopyButton } from './copy-button';

export const CopyableInput = React.forwardRef(({ className, value, showCopy = true, ...props }, ref) => {
  return (
    <div className="relative">
      <Input
        {...props}
        ref={ref}
        value={value}
        className={`${className} ${showCopy && value ? 'pr-10' : ''}`}
      />
      {showCopy && value && (
        <div className="absolute right-1 top-1/2 -translate-y-1/2">
          <CopyButton value={value} />
        </div>
      )}
    </div>
  );
});

CopyableInput.displayName = 'CopyableInput';