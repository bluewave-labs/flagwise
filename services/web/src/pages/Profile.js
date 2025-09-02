import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { usersService, authService } from '../services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { PasswordInput } from '../components/ui/password-input';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { 
  User, 
  Shield, 
  Key, 
  Save, 
  Calendar, 
  Clock,
  CheckCircle,
  AlertCircle,
  Edit,
  Loader2,
} from 'lucide-react';

const Profile = () => {
  const { user, updateUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Profile form states
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [showNameDialog, setShowNameDialog] = useState(false);
  const [editForm, setEditForm] = useState({ username: '' });
  const [nameForm, setNameForm] = useState({ first_name: '', last_name: '' });
  // Password form with validation
  const passwordFormValidation = useFormValidation(
    {
      current_password: '',
      new_password: '',
      confirm_password: ''
    },
    {
      current_password: [validationRules.required],
      new_password: [validationRules.required, validationRules.minLength(6)],
      confirm_password: [validationRules.required, validationRules.passwordMatch('new_password')]
    }
  );
  
  const passwordForm = passwordFormValidation.values;

  // Initialize form with current user data
  useEffect(() => {
    if (user) {
      setEditForm({ username: user.username });
      setNameForm({ 
        first_name: user.first_name || '', 
        last_name: user.last_name || '' 
      });
    }
  }, [user]);

  const handleUpdateUsername = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (!editForm.username.trim()) {
        setError('Username cannot be empty');
        return;
      }
      
      if (editForm.username === user.username) {
        setError('New username must be different from current username');
        return;
      }

      // For hardcoded admin user, we can't update username
      if (user.username === 'admin') {
        setError('Cannot change username for system admin account');
        return;
      }

      // Call API to update username (we'll need to add this endpoint)
      const response = await usersService.updateUsername(editForm.username);
      
      // Update local auth context with new username
      updateUser({ username: editForm.username });
      
      setSuccess('Username updated successfully');
      setShowEditDialog(false);
      
      setTimeout(() => setSuccess(null), 3000);
      
    } catch (err) {
      if (err.response?.status === 409) {
        setError('Username already exists. Please choose a different username.');
      } else {
        setError(err.response?.data?.detail || 'Failed to update username');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateName = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Call backend API to update name
      await usersService.updateProfile({
        first_name: nameForm.first_name.trim(),
        last_name: nameForm.last_name.trim()
      });
      
      // Update local auth context with new name info
      updateUser({ 
        first_name: nameForm.first_name.trim(), 
        last_name: nameForm.last_name.trim() 
      });
      
      setSuccess('Name updated successfully');
      setShowNameDialog(false);
      
      setTimeout(() => setSuccess(null), 3000);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update name');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (!passwordForm.current_password || !passwordForm.new_password) {
        setError('Current password and new password are required');
        return;
      }
      
      if (passwordForm.new_password !== passwordForm.confirm_password) {
        setError('New passwords do not match');
        return;
      }
      
      if (passwordForm.new_password.length < 6) {
        setError('New password must be at least 6 characters');
        return;
      }
      
      await usersService.changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password
      });
      
      setSuccess('Password changed successfully');
      setShowPasswordDialog(false);
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
      
      setTimeout(() => setSuccess(null), 3000);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  const getRoleBadge = (role) => {
    return role === 'admin' ? (
      <Badge variant="destructive" className="capitalize">
        <Shield className="h-3 w-3 mr-1" />
        Administrator
      </Badge>
    ) : (
      <Badge variant="outline" className="capitalize">
        <User className="h-3 w-3 mr-1" />
        Read-only
      </Badge>
    );
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Profile</h1>
        <p className="text-13 text-gray-600">
          Manage your personal account settings and preferences
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert variant="default" className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

      {/* Account Information */}
      <Card>
        <CardContent className="space-y-6">
          {/* Name Section */}
          <div className="grid grid-cols-1 gap-6 mt-6">
            <div>
              <label className="text-sm font-medium text-muted-foreground">Full Name</label>
              <div className="flex items-center justify-between mt-1">
                <div className="flex items-center space-x-3">
                  <p className="text-lg font-medium">
                    {user?.first_name || user?.last_name 
                      ? `${user?.first_name || ''} ${user?.last_name || ''}`.trim() 
                      : 'Not set'}
                  </p>
                  {getRoleBadge(user?.role)}
                </div>
                <Dialog open={showNameDialog} onOpenChange={setShowNameDialog}>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm">
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Update Name</DialogTitle>
                      <DialogDescription>
                        Update your first and last name
                      </DialogDescription>
                    </DialogHeader>
                    
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm font-medium">First Name</label>
                          <Input
                            value={nameForm.first_name}
                            onChange={(e) => setNameForm({...nameForm, first_name: e.target.value})}
                            placeholder="Enter first name"
                            className="mt-1"
                          />
                        </div>
                        <div>
                          <label className="text-sm font-medium">Last Name</label>
                          <Input
                            value={nameForm.last_name}
                            onChange={(e) => setNameForm({...nameForm, last_name: e.target.value})}
                            placeholder="Enter last name"
                            className="mt-1"
                          />
                        </div>
                      </div>
                      
                      <div className="flex justify-end space-x-2">
                        <Button 
                          variant="outline" 
                          onClick={() => {
                            setShowNameDialog(false);
                            setNameForm({ 
                              first_name: user?.first_name || '', 
                              last_name: user?.last_name || '' 
                            });
                            setError(null);
                          }}
                        >
                          Cancel
                        </Button>
                        <Button onClick={handleUpdateName} disabled={loading}>
                          {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                          {loading ? 'Updating...' : 'Update'}
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-1 gap-6">
            <div>
              <label className="text-sm font-medium text-muted-foreground">Username</label>
              <div className="flex items-center justify-between mt-1">
                <p className="text-lg font-medium">{user?.username}</p>
                {user?.username !== 'admin' && (
                  <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4 mr-2" />
                        Edit
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Update Username</DialogTitle>
                        <DialogDescription>
                          Choose a new username for your account
                        </DialogDescription>
                      </DialogHeader>
                      
                      <div className="space-y-4">
                        <div>
                          <label className="text-sm font-medium">New Username</label>
                          <Input
                            value={editForm.username}
                            onChange={(e) => setEditForm({...editForm, username: e.target.value})}
                            placeholder="Enter new username"
                            className="mt-1"
                          />
                        </div>
                        
                        <div className="flex justify-end space-x-2">
                          <Button 
                            variant="outline" 
                            onClick={() => {
                              setShowEditDialog(false);
                              setEditForm({ username: user?.username });
                              setError(null);
                            }}
                          >
                            Cancel
                          </Button>
                          <Button onClick={handleUpdateUsername} disabled={loading}>
                            {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                            {loading ? 'Updating...' : 'Update'}
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                )}
              </div>
            </div>
          </div>
          
        </CardContent>
      </Card>

      {/* Security Settings */}
      <Card className="mt-8">
        <CardContent className="space-y-6">
          <div className="mt-6">
            <label className="text-sm font-medium text-muted-foreground">Password</label>
            <div className="flex items-center justify-between mt-1">
              <p className="text-lg font-medium">••••••••</p>
              <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Key className="h-4 w-4 mr-2" />
                    Change Password
                  </Button>
                </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Change Password</DialogTitle>
                  <DialogDescription>
                    Enter your current password and choose a new one
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Current Password</label>
                    <PasswordInput
                      value={passwordForm.current_password}
                      onChange={(e) => setPasswordForm({...passwordForm, current_password: e.target.value})}
                      placeholder="Enter current password"
                      className="mt-1"
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">New Password</label>
                    <PasswordInput
                      value={passwordForm.new_password}
                      onChange={(e) => setPasswordForm({...passwordForm, new_password: e.target.value})}
                      placeholder="Enter new password (min 6 characters)"
                      className="mt-1"
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium">Confirm New Password</label>
                    <PasswordInput
                      value={passwordForm.confirm_password}
                      onChange={(e) => setPasswordForm({...passwordForm, confirm_password: e.target.value})}
                      placeholder="Confirm new password"
                      className="mt-1"
                    />
                  </div>
                  
                  <div className="flex justify-end space-x-2">
                    <Button 
                      variant="outline" 
                      onClick={() => {
                        setShowPasswordDialog(false);
                        setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
                        setError(null);
                      }}
                    >
                      Cancel
                    </Button>
                    <Button onClick={handleChangePassword} disabled={loading}>
                      {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Key className="h-4 w-4 mr-2" />}
                      {loading ? 'Changing Password...' : 'Change Password'}
                    </Button>
                  </div>
                </div>
              </DialogContent>
              </Dialog>
            </div>
          </div>
        </CardContent>
      </Card>

    </div>
  );
};

export default Profile;