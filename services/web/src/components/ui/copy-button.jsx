import React, { useState } from 'react';
import { Button } from './button';
import { Copy, Check } from 'lucide-react';
import { useToast } from '../../hooks/use-toast';

export const CopyButton = ({ value, variant = "ghost", size = "sm", className = "" }) => {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      toast({
        title: "Copied to clipboard",
        description: "Value has been copied to your clipboard",
        duration: 2000,
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Copy failed",
        description: "Unable to copy to clipboard",
        duration: 3000,
      });
    }
  };

  return (
    <Button
      type="button"
      variant={variant}
      size={size}
      className={className}
      onClick={handleCopy}
      disabled={!value}
    >
      {copied ? (
        <Check className="h-4 w-4 text-green-600" />
      ) : (
        <Copy className="h-4 w-4" />
      )}
      <span className="sr-only">Copy to clipboard</span>
    </Button>
  );
};