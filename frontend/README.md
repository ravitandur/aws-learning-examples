# Quantleap Analytics - Frontend

React.js frontend for the Quantleap Analytics Algorithmic Trading Platform, supporting user authentication and broker management for Indian markets.

## Architecture

This is a unified frontend application that serves all modules of the trading platform:

- **Module 2**: User Authentication & Broker Management ✅ 
- **Module 3**: Market Data Integration (Coming soon)
- **Module 4**: Trading Engine (Coming soon)
- **Module 5**: Portfolio Management (Coming soon)

## Features

### Module 2 - Authentication & Broker Management
- ✅ User registration with Indian phone/state validation
- ✅ Login with email or phone number
- ✅ Forgot password with email-based reset flow
- ✅ Secure JWT token management
- ✅ Broker account management (Zerodha integration)
- ✅ Professional algorithmic trading platform design with TailwindCSS
- ✅ Real-time connection testing

### Technology Stack
- **React 18** with TypeScript
- **TailwindCSS** for professional algorithmic trading platform styling
- **Lucide React** for consistent modern iconography
- **Inter font** for clean, readable typography
- **Axios** for API communication
- **Context API** for state management
- **Indian market specialization** (phone validation, states, IST timezone)

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Backend API deployed (Module 2)

### Installation

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API Gateway URLs
   ```

3. **Start development server**:
   ```bash
   npm start
   ```

4. **Build for production**:
   ```bash
   npm run build
   ```

## Configuration

### Environment Variables

Create `.env` file with your API endpoints:

```bash
# Development
REACT_APP_ENVIRONMENT=dev
REACT_APP_API_URL_DEV=https://your-api-gateway-dev.execute-api.ap-south-1.amazonaws.com/dev

# Staging  
REACT_APP_API_URL_STAGING=https://your-api-gateway-staging.execute-api.ap-south-1.amazonaws.com/staging

# Production
REACT_APP_API_URL_PROD=https://your-api-gateway-prod.execute-api.ap-south-1.amazonaws.com/production
```

### API Integration

The frontend automatically connects to the correct backend environment based on `REACT_APP_ENVIRONMENT`.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/              # Authentication forms
│   │   ├── broker/            # Broker management
│   │   └── common/            # Shared components
│   ├── context/               # React Context (Auth state)
│   ├── pages/                 # Page components
│   ├── services/              # API services
│   ├── types/                 # TypeScript definitions
│   └── utils/                 # Validation & utilities
├── public/
└── package.json
```

## Key Components

### Authentication Flow
1. **AuthPage**: Login/registration with Indian validation
2. **AuthContext**: JWT token management & user state
3. **API Client**: Axios interceptors for auth headers

### Broker Management
1. **BrokerAccountsList**: View all connected accounts
2. **AddBrokerAccountForm**: Secure credential entry
3. **BrokerAccountCard**: Account management & testing

### Indian Market Features
- **Phone Validation**: `+91[6-9]xxxxxxxxx` format
- **State Selection**: All 36 Indian states & UTs
- **Zerodha Integration**: API key/secret validation
- **IST Timezone**: Local time formatting

## API Integration

### Authentication Endpoints
```typescript
POST /auth/register            - User registration
POST /auth/login               - User authentication  
POST /auth/forgot-password     - Request password reset
POST /auth/confirm-forgot-password - Confirm password reset with code
GET /auth/profile              - User profile data
PUT /auth/profile              - Update profile
```

### Broker Management Endpoints  
```typescript
POST /broker-accounts           - Add broker account
GET /broker-accounts            - List accounts
PUT /broker-accounts/{id}       - Update account
DELETE /broker-accounts/{id}    - Remove account
POST /broker-accounts/{id}/verify - Test connection
```

## Development

### Available Scripts

**Development:**
- `npm start` - Start development server (http://localhost:3000)
- `npm run build` - Build for production  
- `npm run eject` - Eject from Create React App

**Testing Infrastructure ⭐ NEW:**
- `npm test` - Interactive test runner
- `npm run test:all` - Run all test categories
- `npm run test:utils` - Test utility functions
- `npm run test:services` - Test API services
- `npm run test:components` - Test React components
- `npm run test:integration` - Test end-to-end workflows
- `npm run test:coverage` - Generate coverage reports (HTML/LCOV)
- `npm run test:ci` - CI/CD optimized testing with coverage
- `npm run test:watch` - Watch mode for development
- `npm run test:verbose` - Detailed test output

### Testing User Flow

1. **Registration**: 
   - Use format `+919876543210` for phone
   - Select any Indian state
   - Password must meet complexity requirements

2. **Broker Setup**:
   - Add Zerodha account with API credentials  
   - Test connection to verify setup
   - Manage multiple broker accounts

## Deployment

### Production Build
```bash
npm run build
# Deploy 'build' folder to your hosting platform
```

### Environment-Specific Builds
```bash
# Development build
REACT_APP_ENVIRONMENT=dev npm run build

# Staging build  
REACT_APP_ENVIRONMENT=staging npm run build

# Production build
REACT_APP_ENVIRONMENT=production npm run build
```

## Security Features

- **JWT Token Storage**: Secure localStorage with auto-refresh
- **API Credentials**: Never logged or exposed in frontend
- **Input Validation**: Client-side validation for all forms
- **Error Handling**: Secure error messages without sensitive data
- **HTTPS Only**: All API communication encrypted

## Future Modules Integration

This frontend is designed to seamlessly integrate upcoming modules:

### Module 3 - Market Data Integration
- Real-time NSE/BSE data components
- Market depth visualization  
- Watchlist management

### Module 4 - Trading Engine  
- Strategy configuration forms
- Order management interface
- Real-time position tracking

### Module 5 - Portfolio Management
- P&L visualization
- Risk management dashboards
- Performance analytics

## Troubleshooting

### Common Issues

1. **API Connection Failed**: Check API Gateway URL in `.env`
2. **Phone Validation Error**: Ensure format `+919876543210`  
3. **Build Fails**: Clear `node_modules` and reinstall
4. **Auth Token Expired**: Tokens auto-refresh on API calls

### Development Tips

- Use React Developer Tools for debugging state
- Check browser network tab for API call details
- Enable `REACT_APP_DEBUG=true` for detailed logging

## Contributing

This frontend follows the modular architecture where each trading platform module has its dedicated components while sharing common utilities and styling.

When adding new modules:
1. Create module-specific components in `src/components/{module}/`
2. Add API services in `src/services/{module}Service.ts`
3. Update navigation in `src/components/common/Navigation.tsx`
4. Add new pages in `src/pages/`

## Next Steps

After setting up the frontend:
1. ✅ Test user registration and login
2. ✅ Connect your Zerodha account  
3. ✅ Verify broker connection works
4. 🚀 Ready for Module 3: Market Data Integration

## Support

For issues or questions about the frontend implementation, refer to the main project documentation in the parent directory.