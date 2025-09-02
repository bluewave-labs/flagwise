import React from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './dialog';
import { Button } from './button';
import { AlertTriangle, Trash2, Loader2 } from 'lucide-react';

export const ConfirmationDialog = ({
  isOpen,
  onOpenChange,
  title,
  description,
  confirmText = "Confirm",
  cancelText = "Cancel",
  onConfirm,
  onCancel,
  destructive = false,
  loading = false,
  icon = null,
  children
}) => {
  const handleConfirm = () => {
    if (loading) return;
    onConfirm?.();
  };

  const handleCancel = () => {
    if (loading) return;
    onCancel?.();
    onOpenChange?.(false);
  };

  const DefaultIcon = destructive ? AlertTriangle : null;
  const IconComponent = icon || DefaultIcon;

  return (
    <Dialog open={isOpen} onOpenChange={loading ? undefined : onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <div className="flex items-center space-x-2">
            {IconComponent && (
              <IconComponent className={`h-5 w-5 ${destructive ? 'text-red-600' : 'text-blue-600'}`} />
            )}
            <DialogTitle className={destructive ? 'text-red-900' : ''}>{title}</DialogTitle>
          </div>
          {description && (
            <DialogDescription className={destructive ? 'text-red-700' : ''}>
              {description}
            </DialogDescription>
          )}
        </DialogHeader>
        
        {children && (
          <div className="py-4">
            {children}
          </div>
        )}
        
        <div className="flex justify-end space-x-2">
          <Button 
            variant="outline" 
            onClick={handleCancel}
            disabled={loading}
          >
            {cancelText}
          </Button>
          <Button 
            variant={destructive ? "destructive" : "default"}
            onClick={handleConfirm}
            disabled={loading}
          >
            {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            {destructive && !loading && <Trash2 className="h-4 w-4 mr-2" />}
            {confirmText}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Specific confirmation dialog variants for common use cases
export const DeleteConfirmationDialog = (props) => (
  <ConfirmationDialog
    {...props}
    destructive={true}
    confirmText={props.confirmText || "Delete"}
    title={props.title || "Confirm Deletion"}
    description={props.description || "This action cannot be undone."}
  />
);

export const DataPurgeConfirmationDialog = (props) => (
  <ConfirmationDialog
    {...props}
    destructive={true}
    confirmText={props.confirmText || "Purge Data"}
    title={props.title || "⚠️ Confirm Data Purge"}
    description={props.description || "WARNING: This action cannot be undone! All data will be permanently deleted."}
  />
);