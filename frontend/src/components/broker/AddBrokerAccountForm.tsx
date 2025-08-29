import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  List,
  ListItem,
  ListItemText,
  InputAdornment,
  IconButton,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  VpnKey as VpnKeyIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { CreateBrokerAccount } from '../../types';
import { validateApiKey, validateApiSecret } from '../../utils/validation';
import { BrokerService } from '../../services/brokerService';
import ErrorAlert from '../common/ErrorAlert';

interface AddBrokerAccountFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (accountData: CreateBrokerAccount) => Promise<void>;
  isLoading?: boolean;
  error?: string | null;
  onClearError?: () => void;
}

const AddBrokerAccountForm: React.FC<AddBrokerAccountFormProps> = ({
  open,
  onClose,
  onSubmit,
  isLoading = false,
  error,
  onClearError,
}) => {
  const [formData, setFormData] = useState<CreateBrokerAccount>({
    broker_name: '',
    api_key: '',
    api_secret: '',
  });

  const [showApiSecret, setShowApiSecret] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof CreateBrokerAccount, string>>>({});

  const supportedBrokers = BrokerService.getSupportedBrokers();

  const handleInputChange = (field: keyof CreateBrokerAccount) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.value;

    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));

    // Clear field error when user starts typing
    if (fieldErrors[field]) {
      setFieldErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }

    // Clear general error when user makes changes
    if (error && onClearError) {
      onClearError();
    }
  };

  const validateForm = (): boolean => {
    const errors: Partial<Record<keyof CreateBrokerAccount, string>> = {};

    // Validate broker selection
    if (!formData.broker_name) {
      errors.broker_name = 'Please select a broker';
    }

    // Validate API key
    const apiKeyValidation = validateApiKey(formData.broker_name, formData.api_key);
    if (!apiKeyValidation.isValid) {
      errors.api_key = apiKeyValidation.error;
    }

    // Validate API secret
    const apiSecretValidation = validateApiSecret(formData.broker_name, formData.api_secret);
    if (!apiSecretValidation.isValid) {
      errors.api_secret = apiSecretValidation.error;
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      await onSubmit(formData);
      handleClose();
    } catch (error) {
      // Error handling is managed by parent component
    }
  };

  const handleClose = () => {
    // Reset form when closing
    setFormData({
      broker_name: '',
      api_key: '',
      api_secret: '',
    });
    setFieldErrors({});
    setShowApiSecret(false);
    onClose();
  };

  const selectedBroker = supportedBrokers.find(b => b.id === formData.broker_name);
  const instructions = selectedBroker ? BrokerService.getBrokerInstructions(selectedBroker.id) : null;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Add Broker Account</DialogTitle>
      
      <DialogContent>
        {error && (
          <Box sx={{ mb: 2 }}>
            <ErrorAlert message={error} onClose={onClearError} />
          </Box>
        )}

        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
          <FormControl fullWidth margin="normal" error={!!fieldErrors.broker_name}>
            <InputLabel>Select Broker *</InputLabel>
            <Select
              value={formData.broker_name}
              label="Select Broker *"
              onChange={(e) => {
                setFormData(prev => ({ 
                  ...prev, 
                  broker_name: e.target.value,
                  // Clear credentials when changing broker
                  api_key: '',
                  api_secret: '',
                }));
                if (fieldErrors.broker_name) {
                  setFieldErrors(prev => ({ ...prev, broker_name: undefined }));
                }
              }}
            >
              {supportedBrokers.map((broker) => (
                <MenuItem key={broker.id} value={broker.id}>
                  <Box>
                    <Typography variant="body1">{broker.name}</Typography>
                    <Typography variant="body2" color="textSecondary">
                      {broker.description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
            {fieldErrors.broker_name && (
              <Typography variant="caption" color="error" sx={{ mt: 1, ml: 2 }}>
                {fieldErrors.broker_name}
              </Typography>
            )}
          </FormControl>

          {instructions && (
            <Box sx={{ mt: 2, mb: 2 }}>
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  {instructions.title}
                </Typography>
                <List dense>
                  {instructions.steps.map((step, index) => (
                    <ListItem key={index} sx={{ py: 0 }}>
                      <ListItemText primary={step} />
                    </ListItem>
                  ))}
                </List>
              </Alert>
            </Box>
          )}

          {formData.broker_name && (
            <>
              <TextField
                fullWidth
                margin="normal"
                label={instructions?.apiKeyLabel || 'API Key'}
                value={formData.api_key}
                onChange={handleInputChange('api_key')}
                error={!!fieldErrors.api_key}
                helperText={fieldErrors.api_key}
                required
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <VpnKeyIcon />
                    </InputAdornment>
                  ),
                }}
              />

              <TextField
                fullWidth
                margin="normal"
                label={instructions?.apiSecretLabel || 'API Secret'}
                type={showApiSecret ? 'text' : 'password'}
                value={formData.api_secret}
                onChange={handleInputChange('api_secret')}
                error={!!fieldErrors.api_secret}
                helperText={fieldErrors.api_secret}
                required
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SecurityIcon />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle api secret visibility"
                        onClick={() => setShowApiSecret(!showApiSecret)}
                        edge="end"
                      >
                        {showApiSecret ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />

              <Alert severity="warning" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  Your API credentials will be encrypted and stored securely in AWS Secrets Manager. 
                  They will only be used for authenticated trading operations.
                </Typography>
              </Alert>
            </>
          )}
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={isLoading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={isLoading || !formData.broker_name}
        >
          {isLoading ? 'Adding Account...' : 'Add Account'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AddBrokerAccountForm;