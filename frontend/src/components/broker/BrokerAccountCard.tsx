import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
} from '@mui/icons-material';
import { BrokerAccount } from '../../types';
// Fixed account_status references

interface BrokerAccountCardProps {
  account: BrokerAccount;
  onEdit: (account: BrokerAccount) => void;
  onDelete: (accountId: string) => void;
  onTest: (accountId: string) => void;
  isTestingConnection?: boolean;
}

const BrokerAccountCard: React.FC<BrokerAccountCardProps> = ({
  account,
  onEdit,
  onDelete,
  onTest,
  isTestingConnection = false,
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleEdit = () => {
    handleClose();
    onEdit(account);
  };

  const handleDeleteClick = () => {
    handleClose();
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    setDeleteDialogOpen(false);
    onDelete(account.broker_account_id);
  };

  const handleTestConnection = () => {
    handleClose();
    onTest(account.broker_account_id);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getBrokerDisplayName = (brokerName: string) => {
    switch (brokerName.toLowerCase()) {
      case 'zerodha':
        return 'Zerodha Kite';
      default:
        return brokerName.charAt(0).toUpperCase() + brokerName.slice(1);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <>
      <Card sx={{ minWidth: 300, maxWidth: 400 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start">
            <Typography variant="h6" component="div" gutterBottom>
              {getBrokerDisplayName(account.broker_name)}
            </Typography>
            <IconButton
              aria-label="more"
              aria-controls={open ? 'broker-menu' : undefined}
              aria-haspopup="true"
              aria-expanded={open ? 'true' : undefined}
              onClick={handleClick}
              size="small"
            >
              <MoreVertIcon />
            </IconButton>
          </Box>

          <Typography variant="body2" color="textSecondary" gutterBottom>
            Account ID: {account.broker_account_id.substring(0, 8)}...
          </Typography>

          <Box display="flex" alignItems="center" gap={1} sx={{ mb: 2 }}>
            <Chip
              label={account.account_status?.toUpperCase() || 'UNKNOWN'}
              color={getStatusColor(account.account_status || 'default') as any}
              size="small"
            />
            <Chip
              label={account.account_type ? (account.account_type.charAt(0).toUpperCase() + account.account_type.slice(1)) : 'Trading'}
              variant="outlined"
              size="small"
            />
          </Box>

          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Added: {formatDate(account.created_at)}
          </Typography>

          <Button
            variant="outlined"
            size="small"
            startIcon={account.account_status === 'active' ? <WifiIcon /> : <WifiOffIcon />}
            onClick={handleTestConnection}
            disabled={isTestingConnection}
            fullWidth
          >
            {isTestingConnection ? 'Testing...' : 'Test Connection'}
          </Button>
        </CardContent>
      </Card>

      <Menu
        id="broker-menu"
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        MenuListProps={{
          'aria-labelledby': 'basic-button',
        }}
      >
        <MenuItem onClick={handleEdit}>
          <EditIcon fontSize="small" sx={{ mr: 1 }} />
          Edit Credentials
        </MenuItem>
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
          <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
          Remove Account
        </MenuItem>
      </Menu>

      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Remove Broker Account</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to remove your {getBrokerDisplayName(account.broker_name)} account?
            This action cannot be undone and you'll need to re-add your credentials to reconnect.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
          >
            Remove Account
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default BrokerAccountCard;