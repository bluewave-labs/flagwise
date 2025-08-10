import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { usersService } from '../services/api';
import { getErrorMessage } from '../lib/utils';
import { useToast } from '../hooks/use-toast';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Pagination } from '../components/ui/pagination';
import { 
  Loader2, 
  UserPlus, 
  Edit,
  Trash2,
  Key,
  Shield,
  User,
  Calendar,
  Activity,
  MoreHorizontal,
  Filter
} from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '../components/ui/dropdown-menu';

const UserManagement = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  
  // Users state
  const [users, setUsers] = useState([]);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  
  // Filter state
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showAdminPasswordDialog, setShowAdminPasswordDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  
  // Form states
  const [createForm, setCreateForm] = useState({
    username: '',
    password: '',
    role: 'read_only',
    first_name: '',
    last_name: ''
  });
  
  const [editForm, setEditForm] = useState({
    role: '',
    is_active: true,
    first_name: '',
    last_name: ''
  });

  const [originalEditForm, setOriginalEditForm] = useState({
    role: '',
    is_active: true,
    first_name: '',
    last_name: ''
  });
  
  const [adminPasswordForm, setAdminPasswordForm] = useState({
    new_password: '',
    confirm_password: ''
  });

  // Load users
  useEffect(() => {
    loadUsers();
  }, [currentPage, pageSize, roleFilter, statusFilter]);

  const loadUsers = async (page = currentPage) => {
    try {
      setLoading(true);
      
      const params = {
        page,
        page_size: pageSize,
        ...Object.fromEntries(
          Object.entries({
            role: roleFilter !== 'all' ? roleFilter : undefined,
            is_active: statusFilter !== 'all' ? (statusFilter === 'active') : undefined
          }).filter(([_, value]) => value !== undefined)
        )
      };
      
      const response = await usersService.getUsers(params);
      const data = response.data || response;
      
      setUsers(data.items || []);
      setTotalCount(data.total_count || 0);
      setTotalPages(data.total_pages || 1);
      setCurrentPage(data.page || page);
      
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: getErrorMessage(err, "Failed to load users")
      });
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    try {
      if (!createForm.username || !createForm.password) {
        toast({
          variant: "destructive",
          title: "Validation Error",
          description: "Username and password are required"
        });
        return;
      }
      
      await usersService.createUser(createForm);
      toast({
        variant: "success",
        title: "Success",
        description: "User created successfully"
      });
      setShowCreateDialog(false);
      setCreateForm({ username: '', password: '', role: 'read_only', first_name: '', last_name: '' });
      await loadUsers();
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: getErrorMessage(err, 'Failed to create user')
      });
    }
  };

  const handleEditUser = async () => {
    try {
      await usersService.updateUser(selectedUser.id, editForm);
      toast({
        variant: "success",
        title: "Success",
        description: "User updated successfully"
      });
      setShowEditDialog(false);
      setSelectedUser(null);
      await loadUsers();
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: getErrorMessage(err, 'Failed to update user')
      });
    }
  };

  const handleDeleteUser = async () => {
    try {
      if (users.length <= 1) {
        toast({
          variant: "destructive",
          title: "Cannot Delete User",
          description: "Cannot delete the last user. At least one user must remain to access the system."
        });
        return;
      }
      
      await usersService.deleteUser(selectedUser.id);
      toast({
        variant: "success",
        title: "Success",
        description: "User deleted successfully"
      });
      setShowDeleteDialog(false);
      setSelectedUser(null);
      await loadUsers();
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: getErrorMessage(err, 'Failed to delete user')
      });
    }
  };

  const handleAdminResetPassword = async () => {
    try {
      if (!adminPasswordForm.new_password) {
        toast({
          variant: "destructive",
          title: "Validation Error",
          description: "New password is required"
        });
        return;
      }
      
      if (adminPasswordForm.new_password !== adminPasswordForm.confirm_password) {
        toast({
          variant: "destructive",
          title: "Validation Error",
          description: "Passwords do not match"
        });
        return;
      }
      
      if (adminPasswordForm.new_password.length < 6) {
        toast({
          variant: "destructive",
          title: "Validation Error",
          description: "Password must be at least 6 characters"
        });
        return;
      }
      
      await usersService.adminResetPassword(selectedUser.id, adminPasswordForm.new_password);
      
      toast({
        variant: "success",
        title: "Success",
        description: `Password changed successfully for ${selectedUser.username}`
      });
      setShowAdminPasswordDialog(false);
      setAdminPasswordForm({ new_password: '', confirm_password: '' });
      setSelectedUser(null);
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: getErrorMessage(err, 'Failed to change password')
      });
    }
  };

  const hasEditFormChanges = () => {
    return (
      editForm.role !== originalEditForm.role ||
      editForm.is_active !== originalEditForm.is_active ||
      editForm.first_name !== originalEditForm.first_name ||
      editForm.last_name !== originalEditForm.last_name
    );
  };

  const openEditDialog = (userToEdit) => {
    const formData = {
      role: userToEdit.role,
      is_active: userToEdit.is_active,
      first_name: userToEdit.first_name || '',
      last_name: userToEdit.last_name || ''
    };
    
    setSelectedUser(userToEdit);
    setEditForm(formData);
    setOriginalEditForm(formData); // Store original values for comparison
    setShowEditDialog(true);
  };

  const openDeleteDialog = (userToDelete) => {
    setSelectedUser(userToDelete);
    setShowDeleteDialog(true);
  };

  const openAdminPasswordDialog = (userToReset) => {
    setSelectedUser(userToReset);
    setShowAdminPasswordDialog(true);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const getRoleBadge = (role) => {
    return role === 'admin' ? (
      <Badge variant="destructive" className="capitalize">
        <Shield className="h-3 w-3 mr-1" />
        Admin
      </Badge>
    ) : (
      <Badge variant="outline" className="capitalize">
        <User className="h-3 w-3 mr-1" />
        Read-only
      </Badge>
    );
  };

  const getStatusBadge = (isActive) => {
    return isActive ? (
      <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
        <Activity className="h-3 w-3 mr-1" />
        Active
      </Badge>
    ) : (
      <Badge variant="secondary">
        Inactive
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin" />
          <p className="text-muted-foreground">Loading users...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">User Management</h1>
          <p className="text-13 text-gray-600">
            Manage user accounts, roles, and permissions
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button>
                <UserPlus className="h-4 w-4 mr-2" />
                Add User
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New User</DialogTitle>
                <DialogDescription>
                  Add a new user account to the system
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Username</label>
                  <Input
                    value={createForm.username}
                    onChange={(e) => setCreateForm({...createForm, username: e.target.value})}
                    placeholder="Enter username"
                    className="mt-1"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">First Name</label>
                    <Input
                      value={createForm.first_name}
                      onChange={(e) => setCreateForm({...createForm, first_name: e.target.value})}
                      placeholder="Enter first name"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Last Name</label>
                    <Input
                      value={createForm.last_name}
                      onChange={(e) => setCreateForm({...createForm, last_name: e.target.value})}
                      placeholder="Enter last name"
                      className="mt-1"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="text-sm font-medium">Password</label>
                  <Input
                    type="password"
                    value={createForm.password}
                    onChange={(e) => setCreateForm({...createForm, password: e.target.value})}
                    placeholder="Enter password (min 6 characters)"
                    className="mt-1"
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium">Role</label>
                  <Select 
                    value={createForm.role}
                    onValueChange={(value) => setCreateForm({...createForm, role: value})}
                  >
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="read_only">Read-only</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="flex justify-end space-x-2">
                  <Button 
                    variant="outline" 
                    onClick={() => {
                      setShowCreateDialog(false);
                      setCreateForm({ username: '', password: '', role: 'read_only', first_name: '', last_name: '' });
                    }}
                  >
                    Cancel
                  </Button>
                  <Button onClick={handleCreateUser}>
                    Create User
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center justify-between bg-muted/30 border border-muted rounded-lg p-4">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <Select value={roleFilter} onValueChange={(value) => {
              setRoleFilter(value);
              setCurrentPage(1);
            }}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="read_only">Read-only</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="flex items-center space-x-2">
            <Select value={statusFilter} onValueChange={(value) => {
              setStatusFilter(value);
              setCurrentPage(1);
            }}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        
        <div className="text-sm text-muted-foreground">
          {totalCount} user{totalCount !== 1 ? 's' : ''} total
        </div>
      </div>

      {/* Users Table */}
      {users.length === 0 ? (
        <div className="text-center py-12">
          <User className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No users found</h3>
          <p className="text-muted-foreground mb-4">
            {roleFilter !== 'all' || statusFilter !== 'all' 
              ? 'No users match your current filters. Try adjusting the filter criteria.' 
              : 'Create your first user account to get started'}
          </p>
          {(roleFilter === 'all' && statusFilter === 'all') && (
            <Button onClick={() => setShowCreateDialog(true)}>
              <UserPlus className="h-4 w-4 mr-2" />
              Add User
            </Button>
          )}
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Username</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Login</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
                {/* Database Users */}
                {users.map((userItem) => (
                  <TableRow key={userItem.id}>
                    <TableCell className="font-medium">
                      {userItem.username}
                    </TableCell>
                    <TableCell>
                      {userItem.first_name || userItem.last_name 
                        ? `${userItem.first_name || ''} ${userItem.last_name || ''}`.trim()
                        : '-'
                      }
                    </TableCell>
                    <TableCell>{getRoleBadge(userItem.role)}</TableCell>
                    <TableCell>{getStatusBadge(userItem.is_active)}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(userItem.last_login)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(userItem.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openEditDialog(userItem)}>
                            <Edit className="h-4 w-4 mr-2" />
                            Edit User
                          </DropdownMenuItem>
                          {user?.role === 'admin' && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem onClick={() => openAdminPasswordDialog(userItem)}>
                                <Key className="h-4 w-4 mr-2" />
                                Change Password
                              </DropdownMenuItem>
                            </>
                          )}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem 
                            className={`text-red-600 ${users.length <= 1 ? 'opacity-50 cursor-not-allowed' : ''}`}
                            onClick={() => users.length > 1 ? openDeleteDialog(userItem) : null}
                            disabled={users.length <= 1}
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete User
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </div>
      )}
      
      {/* Pagination */}
      {users.length > 0 && totalCount > 0 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          totalCount={totalCount}
          pageSize={pageSize}
          itemName="users"
          onPageChange={(page) => {
            setCurrentPage(page);
            loadUsers(page);
          }}
          onPageSizeChange={(newPageSize) => {
            setPageSize(newPageSize);
            setCurrentPage(1);
          }}
        />
      )}

      {/* Edit User Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
            <DialogDescription>
              Update user role and status
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">First Name</label>
                <Input
                  value={editForm.first_name}
                  onChange={(e) => setEditForm({...editForm, first_name: e.target.value})}
                  placeholder="Enter first name"
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Last Name</label>
                <Input
                  value={editForm.last_name}
                  onChange={(e) => setEditForm({...editForm, last_name: e.target.value})}
                  placeholder="Enter last name"
                  className="mt-1"
                />
              </div>
            </div>
            
            <div>
              <label className="text-sm font-medium">Role</label>
              <Select 
                value={editForm.role}
                onValueChange={(value) => setEditForm({...editForm, role: value})}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="read_only">Read-only</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-sm font-medium">Status</label>
              <Select 
                value={editForm.is_active ? 'active' : 'inactive'}
                onValueChange={(value) => setEditForm({...editForm, is_active: value === 'active'})}
              >
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex justify-end space-x-2">
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowEditDialog(false);
                  setSelectedUser(null);
                }}
              >
                Cancel
              </Button>
              <Button 
                onClick={handleEditUser}
                disabled={!hasEditFormChanges()}
              >
                Update User
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete User Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete User</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedUser?.username}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex justify-end space-x-2">
            <Button 
              variant="outline" 
              onClick={() => {
                setShowDeleteDialog(false);
                setSelectedUser(null);
              }}
            >
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDeleteUser}
            >
              Delete User
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Admin Password Reset Dialog */}
      <Dialog open={showAdminPasswordDialog} onOpenChange={setShowAdminPasswordDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change User Password</DialogTitle>
            <DialogDescription>
              Change password for {selectedUser?.username}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">New Password</label>
              <Input
                type="password"
                value={adminPasswordForm.new_password}
                onChange={(e) => setAdminPasswordForm({...adminPasswordForm, new_password: e.target.value})}
                placeholder="Enter new password (min 6 characters)"
                className="mt-1"
              />
            </div>
            
            <div>
              <label className="text-sm font-medium">Confirm New Password</label>
              <Input
                type="password"
                value={adminPasswordForm.confirm_password}
                onChange={(e) => setAdminPasswordForm({...adminPasswordForm, confirm_password: e.target.value})}
                placeholder="Confirm new password"
                className="mt-1"
              />
            </div>
            
            <div className="flex justify-end space-x-2">
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowAdminPasswordDialog(false);
                  setAdminPasswordForm({ new_password: '', confirm_password: '' });
                  setSelectedUser(null);
                }}
              >
                Cancel
              </Button>
              <Button onClick={handleAdminResetPassword}>
                Change Password
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserManagement;