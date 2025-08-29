import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Box,
  Button,
  Avatar,
  Divider,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Menu as MenuIcon,
  AccountCircle,
  Logout as LogoutIcon,
  Settings as SettingsIcon,
  Dashboard as DashboardIcon,
  AccountBalance as AccountBalanceIcon,
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import { formatPhoneNumber } from '../../utils/validation';

interface NavigationProps {
  onNavigate: (page: string) => void;
  currentPage: string;
}

const Navigation: React.FC<NavigationProps> = ({ onNavigate, currentPage }) => {
  const { user, logout } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [mobileMenuAnchor, setMobileMenuAnchor] = useState<null | HTMLElement>(null);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleMobileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setMobileMenuAnchor(event.currentTarget);
  };

  const handleMobileMenuClose = () => {
    setMobileMenuAnchor(null);
  };

  const handleLogout = () => {
    handleProfileMenuClose();
    logout();
  };

  const handleNavigate = (page: string) => {
    handleMobileMenuClose();
    onNavigate(page);
  };

  const navigationItems = [
    { key: 'dashboard', label: 'Dashboard', icon: <DashboardIcon /> },
    { key: 'brokers', label: 'Broker Accounts', icon: <AccountBalanceIcon /> },
  ];

  const isMenuOpen = Boolean(anchorEl);
  const isMobileMenuOpen = Boolean(mobileMenuAnchor);

  return (
    <AppBar position="static">
      <Toolbar>
        {/* Mobile menu button */}
        <IconButton
          edge="start"
          color="inherit"
          aria-label="menu"
          onClick={handleMobileMenuOpen}
          sx={{ mr: 2, display: { md: 'none' } }}
        >
          <MenuIcon />
        </IconButton>

        {/* Logo/Brand */}
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Quantleap Analytics
        </Typography>

        {/* Desktop navigation */}
        <Box sx={{ display: { xs: 'none', md: 'flex' }, mr: 2 }}>
          {navigationItems.map((item) => (
            <Button
              key={item.key}
              color="inherit"
              onClick={() => onNavigate(item.key)}
              sx={{
                mr: 1,
                backgroundColor: currentPage === item.key ? 'rgba(255,255,255,0.1)' : 'transparent',
              }}
              startIcon={item.icon}
            >
              {item.label}
            </Button>
          ))}
        </Box>

        {/* User profile menu */}
        <IconButton
          edge="end"
          aria-label="account of current user"
          aria-controls="profile-menu"
          aria-haspopup="true"
          onClick={handleProfileMenuOpen}
          color="inherit"
        >
          <Avatar sx={{ width: 32, height: 32 }}>
            {user?.fullName ? user.fullName.charAt(0).toUpperCase() : <AccountCircle />}
          </Avatar>
        </IconButton>
      </Toolbar>

      {/* Mobile menu */}
      <Menu
        id="mobile-menu"
        anchorEl={mobileMenuAnchor}
        anchorOrigin={{
          vertical: 'top',
          horizontal: 'left',
        }}
        keepMounted
        transformOrigin={{
          vertical: 'top',
          horizontal: 'left',
        }}
        open={isMobileMenuOpen}
        onClose={handleMobileMenuClose}
        sx={{ display: { md: 'none' } }}
      >
        {navigationItems.map((item) => (
          <MenuItem
            key={item.key}
            onClick={() => handleNavigate(item.key)}
            selected={currentPage === item.key}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText>{item.label}</ListItemText>
          </MenuItem>
        ))}
      </Menu>

      {/* Profile menu */}
      <Menu
        id="profile-menu"
        anchorEl={anchorEl}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        keepMounted
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        open={isMenuOpen}
        onClose={handleProfileMenuClose}
      >
        <Box sx={{ px: 2, py: 1, minWidth: 200 }}>
          <Typography variant="subtitle1" fontWeight="bold">
            {user?.fullName}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            {user?.email}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            {user?.phoneNumber && formatPhoneNumber(user.phoneNumber)}
          </Typography>
        </Box>
        <Divider />
        <MenuItem onClick={handleProfileMenuClose}>
          <ListItemIcon>
            <SettingsIcon fontSize="small" />
          </ListItemIcon>
          Settings
        </MenuItem>
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <LogoutIcon fontSize="small" />
          </ListItemIcon>
          Logout
        </MenuItem>
      </Menu>
    </AppBar>
  );
};

export default Navigation;